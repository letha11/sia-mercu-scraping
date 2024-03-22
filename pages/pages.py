import requests
import requests.cookies
import logging
import dateparser

from bs4 import BeautifulSoup, NavigableString
from requests.exceptions import RequestException, Timeout
from repository.user_repository import UserRepositoryImpl
from utils.auth_helper import AuthHelper
from utils.constants import login_url, home_url, jadwal_url
from utils.jwt_service import JWT_Service


class Pages:
    cookies_jar = None

    def __init__(
        self,
        session: requests.Session,
        jwt_service: JWT_Service,
        user_repository: UserRepositoryImpl,
        auth_helper: AuthHelper,
    ) -> None:
        self.session = session
        self.jwt_service = jwt_service
        self.user_repository = user_repository
        self.auth_helper = auth_helper

    def scrape_jadwal(self, token: str, periode_args: str):
        username = self.jwt_service.decode_token(token)["username"]
        user = self.user_repository.get(username)

        if user is None:
            return

        phpsessid = self.auth_helper.decrypt(user.phpsessid)

        # have not login
        if phpsessid is None:
            return

        logging.info("Getting Jadwal")

        jadwal_result = self.session.post(
            jadwal_url,
            data={"periode": periode_args},
            cookies=self.__create_cookie_jar(phpsessid),
            timeout=25,
        )

        # phpsessid expired
        if jadwal_result.url == login_url:
            relog_result = self.__re_login(username, user.password)

            # Something went wrong
            if relog_result is None:
                return

            phpsessid = relog_result

            # Re-try getting jadwal
            jadwal_result = self.session.post(
                jadwal_url,
                data={"periode": periode_args},
                cookies=self.__create_cookie_jar(phpsessid),
                timeout=25,
            )

        jadwal_parsed = BeautifulSoup(jadwal_result.text, "lxml")

        periode = []
        periode_html = jadwal_parsed.find(id="periode")

        for periode_item in periode_html.find_all("option"):
            label = periode_item.text.strip()
            value = periode_item["value"]
            periode.append({"label": label, "value": value})

        matkul = []

        matkul_table = jadwal_parsed.find_all("table")[-1]
        matkul_list = matkul_table.find("tbody").find_all("tr")

        for i in range(0, len(matkul_list), 2):
            content = matkul_list[i].find_all("td")

            content = [
                (
                    self.__clean_nama_matkul(item)
                    if item.find("i") is not None
                    else item.find("a").text.strip() if i == 6 else item.text.strip()
                )
                for i, item in enumerate(content)
            ]

            matkul.append(
                {
                    "hari": content[1],
                    "time": f"{content[2]} - {content[3]}",
                    "nama_matkul": content[5],
                    "ruangan": content[6],
                    "dosen": content[7],
                }
            )

        logging.info("Finished Getting Jadwal")

        return {
            "periode": periode,
            "mata_kuliah": matkul,
        }

    def scrape_home(self, token: str):
        username = self.jwt_service.decode_token(token)["username"]
        user = self.user_repository.get(username)

        if user is None:
            return

        phpsessid = self.auth_helper.decrypt(user.phpsessid)

        if phpsessid is None:
            return

        home_result = self.session.get(
            home_url,
            cookies=self.__create_cookie_jar(phpsessid),
            timeout=25,
        )

        if home_result.url == login_url:
            relog_result = self.__re_login(username, user.password)

            # Something went wrong
            if relog_result is None:
                return

            phpsessid = relog_result

            # Re-try getting home
            home_result = self.session.get(
                home_url, cookies=self.__create_cookie_jar(phpsessid), timeout=25
            )

        home_parsed = BeautifulSoup(home_result.text, "lxml")

        matkul_table = home_parsed.find("tbody")
        mata_kuliah = []
        rows_matkul_table = matkul_table.find_all("tr", recursive=False)

        for i in range(0, len(rows_matkul_table), 2):
            nama_matkul_idx = i
            table_idx = i + 1

            perkuliahan = []

            nama_matkul = (
                rows_matkul_table[nama_matkul_idx]
                .find("div")
                .text.split("-")[1]
                .strip()
            )
            perkuliahan_table = (
                rows_matkul_table[table_idx].find("div", id="tabs-2").find("tbody")
            )
            absensi_table = (
                rows_matkul_table[table_idx].find("div", id="tabs-1").find_all("tr")
            )
            tr_pertemuan = [
                th_tag.text
                for th_tag in absensi_table[0].find_all("th")
                if th_tag.text.strip()
            ]
            td_abseni_checkmark = absensi_table[-2].find_all("td")

            for i, kuliah_row in enumerate(
                perkuliahan_table.find_all("tr", recursive=False)
            ):
                if len(kuliah_row.find_all("td")) >= 3:
                    col_data = [
                        (
                            item.text.strip()
                            if item.find("a") is None
                            else item.find("a")["href"]
                        )
                        for item in kuliah_row.contents
                        if type(item) is not NavigableString
                    ]

                    pertemuan = ""
                    temp_pertemuan = ""

                    for char in reversed(col_data[0]):
                        if char.isdigit():
                            temp_pertemuan += char
                        else:
                            break

                    pertemuan = int(temp_pertemuan[::-1])

                    kehadiran = "Belum Dilaksanakan"

                    for i, pt in enumerate(tr_pertemuan):
                        if pt == str(pertemuan):
                            kehadiran = (
                                "Hadir"
                                if td_abseni_checkmark[i].find("img")
                                else "Tidak Hadir"
                            )
                            break

                    result = {
                        "pertemuan": pertemuan,
                        "tanggal": dateparser.parse(col_data[1], languages=["id"]),
                        "kehadiran": kehadiran,
                        "materi": col_data[2],
                        "link_modul": col_data[3],
                    }

                    perkuliahan.append(result)

            mata_kuliah.append(
                {
                    "nama_matkul": nama_matkul,
                    "perkuliahan": perkuliahan,
                }
            )

        return mata_kuliah

    def login(self, username, password) -> str | None:
        logging.info("Login in process")

        login_result = self.session.post(
            login_url,
            data={"act": "login", "username": username, "password": password},
            timeout=25,
        )

        # Wrong credentials
        if login_result.url == login_url:
            return

        phpsessid = self.session.cookies["PHPSESSID"]

        user = self.user_repository.get(username)

        if user is None:
            self.user_repository.save(username, password=password, PHPSESSID=phpsessid)
        else:
            self.user_repository.update(
                username, password=password, PHPSESSID=phpsessid
            )

        token = self.jwt_service.generate_token({"username": username})

        logging.info("Login Finished")

        return token

    def __re_login(self, username, password) -> str | None:
        logging.info("Re-Login in process")
        login_result = self.session.post(
            login_url,
            data={
                "act": "login",
                "username": username,
                "password": self.auth_helper.decrypt(password),
            },
            timeout=25,
        )

        # Wrong credentials
        if login_result.url == login_url:
            return

        phpsessid: str = self.session.cookies["PHPSESSID"]

        self.user_repository.update(username, PHPSESSID=phpsessid)

        logging.info("Re-Login Finished")

        return phpsessid

    def __create_cookie_jar(self, phpsessid: str) -> requests.cookies.RequestsCookieJar:
        return requests.cookies.cookiejar_from_dict({"PHPSESSID": phpsessid})

    # Jadwal Helper
    def __clean_nama_matkul(self, element):
        # Filtering empty string
        nama_matkul_clean = list(
            filter(None, [cs.text.strip() for cs in element.contents])
        )

        nama_matkul = " ".join(nama_matkul_clean)

        return nama_matkul
