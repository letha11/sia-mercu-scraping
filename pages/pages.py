from typing import Any
import requests
import requests.cookies
import logging
import datetime as DT
from bs4 import BeautifulSoup, NavigableString
from uuid import uuid4

from utils.constants import login_url, home_url, jadwal_url

class Pages:
    cookies_jar = None
    phpsessid_storage: dict[str, Any] = {}

    def __init__(
        self,
        session: requests.Session,
    ) -> None:
        self.session = session

    def scrape_jadwal(self, token: str, periode_args: str):
        phpsessid = self.phpsessid_storage.get(token)

        # have not login
        if phpsessid is None:
            return

        logging.info("Getting Jadwal")

        jadwal_result = self.session.post(
            jadwal_url,
            data={"periode": periode_args},
            cookies=self.__create_cookie_jar(phpsessid),
        )

        # have not login
        if jadwal_result.url == login_url:
            return

        jadwal_parsed = BeautifulSoup(jadwal_result.text, features="lxml")

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
                self.__clean_nama_matkul(item)
                if item.find("i") is not None
                else item.find("a").text.strip()
                if i == 6
                else item.text.strip()
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
        phpsessid = self.phpsessid_storage.get(token)

        if phpsessid is None:
            return

        home_result = self.session.get(
            home_url, cookies=self.__create_cookie_jar(phpsessid)
        )

        if home_result.url == login_url:
            return

        home_parsed = BeautifulSoup(home_result.text, features="lxml")

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
            absensi_image = absensi_table[-2].find_all("img")

            for i, kuliah_row in enumerate(
                perkuliahan_table.find_all("tr", recursive=False)[3:]
            ):
                col_data = [
                    item.text.strip()
                    if item.find("a") is None
                    else item.find("a")["href"]
                    for item in kuliah_row.contents
                    if type(item) is not NavigableString
                ]

                result = {
                    "pertemuan": int(
                        "".join([text for text in col_data[0] if text.isdigit()])
                    ),
                    "tanggal": str(DT.datetime.strptime(col_data[1], "%a, %d %b %Y")),
                    "kehadiran": "Belum Dilaksanakan",
                    "materi": col_data[2],
                    "link_modul": col_data[3],
                }

                perkuliahan.append(result)

            for i, img in enumerate(absensi_image):
                kehadiran = "Tidak Hadir"

                if img["src"].find("check") != -1:
                    kehadiran = "Hadir"

                    perkuliahan[i]["kehadiran"] = kehadiran

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
            login_url, data={"act": "login", "username": username, "password": password}
        )

        if login_result.url == login_url:
            return

        unique_id = str(uuid4())
        self.phpsessid_storage[unique_id] = self.session.cookies["PHPSESSID"]
        logging.info("Login Finished")

        return unique_id

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


