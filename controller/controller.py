from collections import defaultdict, OrderedDict
from typing import Any, Dict, List, Literal, Set, Tuple
from bs4.element import Tag
import requests
import requests.cookies
import logging
import dateparser

from bs4 import BeautifulSoup, NavigableString
from requests.models import Response
from models import status
from models.status import Status
from repository.user_repository import UserRepositoryImpl
from utils.auth_helper import AuthHelper
from utils.constants import *
from utils.jwt_service import JWT_Service


class Controller:
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
            return Status.UNAUTHORIZED

        phpsessid = self.auth_helper.decrypt(user.phpsessid)

        # have not login
        if phpsessid is None:
            return Status.UNAUTHORIZED

        logging.info("Getting Jadwal")

        if periode_args is None or periode_args == "":
            jadwal_result = self.session.post(
                jadwal_url,
                data={"periode": periode_args},
                cookies=self.__create_cookie_jar(phpsessid),
                timeout=25,
            )
            if jadwal_result.url == login_url:
                return Status.RELOGIN_NEEDED

            jadwal_parsed = BeautifulSoup(jadwal_result.text, "lxml")

            periode = []
            periode_html = jadwal_parsed.find(id="periode")

            latest_periode_val = periode_html.find_all("option")[-1]["value"]

            jadwal_result = self.session.post(
                jadwal_url,
                data={"periode": latest_periode_val},
                cookies=self.__create_cookie_jar(phpsessid),
                timeout=25,
            )
        else:
            jadwal_result = self.session.post(
                jadwal_url,
                data={"periode": periode_args},
                cookies=self.__create_cookie_jar(phpsessid),
                timeout=25,
            )

        # phpsessid expired
        if jadwal_result.url == login_url:
            return Status.RELOGIN_NEEDED

        # jadwal_html = open("jadwal_html.html")
        # jadwal_html = jadwal_html.read()
        jadwal_parsed = BeautifulSoup(jadwal_result.text, "lxml")
        # jadwal_parsed = BeautifulSoup(jadwal_html, "lxml")

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

        matkul_categorized_by_day = defaultdict(list)

        for m in matkul:
            matkul_categorized_by_day[m["hari"].lower()].append(m)

        matkul_categorized_by_day = dict(matkul_categorized_by_day)

        self.session.cookies.clear()
        return {
            "periode": periode,
            "mata_kuliah": matkul_categorized_by_day,
        }

    def scrape_attendance(self, token: str):
        username = self.jwt_service.decode_token(token)["username"]
        user = self.user_repository.get(username)

        if user is None:
            return Status.UNAUTHORIZED

        phpsessid = self.auth_helper.decrypt(user.phpsessid)

        if phpsessid is None:
            return Status.UNAUTHORIZED

        home_result = self.session.get(
            home_url,
            cookies=self.__create_cookie_jar(phpsessid),
            timeout=25,
        )

        # phpsessid expired but token still valid
        if home_result.url == login_url:
            return Status.RELOGIN_NEEDED

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
                            if item.find("a") is not Tag
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

                    tanggal = dateparser.parse(col_data[1], languages=["id"])
                    tanggal_isostring = ""

                    if tanggal is not None:
                        tanggal_isostring = tanggal.isoformat()
                    else:
                        tanggal_isostring = None

                    result = {
                        "pertemuan": pertemuan,
                        "tanggal": tanggal_isostring,
                        "kehadiran": kehadiran,
                        "materi": col_data[2],
                        "link_modul": col_data[3],
                    }

                    perkuliahan.append(result)

            perkuliahan = sorted(perkuliahan, key=lambda p: p["pertemuan"])

            mata_kuliah.append(
                {
                    "nama_matkul": nama_matkul,
                    "perkuliahan": perkuliahan,
                }
            )

        self.session.cookies.clear()
        return mata_kuliah


    def scrape_transcript(self, token: str):
        username = self.jwt_service.decode_token(token)["username"]
        user = self.user_repository.get(username)

        if user is None:
            return Status.UNAUTHORIZED

        phpsessid = self.auth_helper.decrypt(user.phpsessid)

        if phpsessid is None:
            return Status.UNAUTHORIZED

        transkrip_page = self.session.get(
            get_transcript_url(username),
            cookies=self.__create_cookie_jar(phpsessid),
            timeout=25,
        )

        if transkrip_page.url == login_url:
            return Status.RELOGIN_NEEDED

        transkrip_parsed = BeautifulSoup(transkrip_page.text, "lxml")
        data: List = []
        data_table = transkrip_parsed.css.select(
            "#main_form > div > div.row-fluid > div:nth-child(3) > table"
        )[0]
        rows = data_table.find_all("tr")[1:-1]

        for row in rows:
            number = row.css.select("td:nth-child(1)")[0].text
            semester = row.css.select("td:nth-child(2)")[0].text
            subject_code = row.css.select("td:nth-child(3)")[0].text
            subject = row.css.select("td:nth-child(4)")[0].text
            sks = row.css.select("td:nth-child(5)")[0].text
            grade = row.css.select("td:nth-child(6)")[0].text

            dict = {
                "number": number,
                "semester": semester,
                "subject_code": subject_code,
                "subject": subject,
                "sks": sks,
                "grade": grade,
            }

            data.append(dict)

        return data


    def scrape_detail_mhs(self, token: str):
        username = self.jwt_service.decode_token(token)["username"]
        user = self.user_repository.get(username)

        if user is None:
            return Status.UNAUTHORIZED

        phpsessid = self.auth_helper.decrypt(user.phpsessid)

        if phpsessid is None:
            return Status.UNAUTHORIZED

        detail_result = self.session.get(
            detail_url,
            cookies=self.__create_cookie_jar(phpsessid),
            timeout=25,
        )

        if detail_result.url == login_url:
            return Status.RELOGIN_NEEDED

        detail_parsed = BeautifulSoup(detail_result.text, "lxml")

        data: Dict[str, Any] = {}
        container_tbody = detail_parsed.select_one("div.form-container > table.table")
        picture_img_url = container_tbody.find("img").get("src")
        list_tr = container_tbody.find_all("tr", recursive=False)

        for tr in list_tr:
            result = self.__extract_tr_to_dict(tr)
            if len(result) >= 2:
                data[result[0]] = result[1]

        alert_tr = list_tr[0].find_all("tr", recursive=True)
        for tr in alert_tr:
            result = self.__extract_tr_to_dict(tr)
            if len(result) >= 2:
                data[result[0]] = result[1]

        data["picture_url"] = picture_img_url

        self.session.cookies.clear()
        return data

    def refresh_token(self, refresh_token: str) -> Tuple[str, str]:
        logging.info("Refreshing token...")

        decoded = self.jwt_service.decode_token(refresh_token)

        new_token = self.jwt_service.generate_token(decoded, expiration_time="7h")
        new_refresh_token = self.jwt_service.generate_token(
            decoded, expiration_time="7d"
        )

        return new_token, new_refresh_token

    def get_captcha(self):
        logging.info("Getting Captcha...")

        captcha_result = self.session.get(
            captcha_url,
            timeout=25,
        )

        return captcha_result.content

    def login(self, username, password, captcha):
        logging.info("Login in process")

        login_result = self.session.post(
            login_url,
            data={
                "act": "login",
                "username": username,
                "password": password,
                "captcha": captcha,
            },
            timeout=25,
        )

        # Wrong credentials
        if login_result.url == login_url:
            return

        phpsessid = self.session.cookies["PHPSESSID"]

        self.session.cookies.clear()

        user = self.user_repository.get(username)

        if user is None:
            self.user_repository.save(username, password=password, PHPSESSID=phpsessid)
        else:
            self.user_repository.update(
                username, password=password, PHPSESSID=phpsessid
            )

        token = self.jwt_service.generate_token({"username": username})
        refresh_token = self.jwt_service.generate_token(
            {"username": username}, expiration_time="7d"
        )

        logging.info("Login Finished")

        return token, refresh_token

    def relogin(self, token: str, captcha: str):
        username = self.jwt_service.decode_token(token)["username"]
        user = self.user_repository.get(username)

        if user is None:
            return Status.UNAUTHORIZED

        password = self.auth_helper.decrypt(user.password)

        relogin_result = self.session.post(
            login_url,
            data={
                "act": "login",
                "username": username,
                "password": password,
                "captcha": captcha,
            },
            timeout=25,
        )

        # Wrong captcha
        if relogin_result.url == login_url:
            return

        # Update latest PHPSESSID to database
        print(self.session.cookies["PHPSESSID"])
        phpsessid: str = self.session.cookies["PHPSESSID"]
        self.user_repository.update(username, PHPSESSID=phpsessid)

        logging.info("ReLogin Finished")

        return Status.SUCCESS

    def __create_cookie_jar(self, phpsessid: str) -> requests.cookies.RequestsCookieJar:
        return requests.cookies.cookiejar_from_dict({"PHPSESSID": phpsessid})

    def __extract_tr_to_dict(self, tr):
        list_td = tr.find_all("td")
        list_td = [td.text.replace("\n", "") for td in list_td if td.text.strip() != ""]
        list_td[0] = list_td[0].lower().replace(" ", "_")
        return list_td

    # Jadwal Helper
    def __clean_nama_matkul(self, element):
        # Filtering empty string
        nama_matkul_clean: list[str] = list(
            filter(None, [cs.text.strip() for cs in element.contents])
        )

        nama_matkul = nama_matkul_clean[0].title()

        return nama_matkul
