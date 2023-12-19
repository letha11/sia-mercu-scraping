import datetime as DT
import locale
from bs4 import BeautifulSoup, NavigableString
# For formatting date from string of indonesian locale date to datetime object
locale.setlocale(locale.LC_TIME, "id_ID.utf8")

def scrape_home(home_html: str):
    home_parsed = BeautifulSoup(home_html, features="lxml")

    matkul_table = home_parsed.find("tbody")
    mata_kuliah = []
    rows_matkul_table = matkul_table.find_all("tr", recursive=False)

    for i in range(0, len(rows_matkul_table), 2):
        nama_matkul_idx = i
        table_idx = i+1

        perkuliahan = []

        nama_matkul = rows_matkul_table[nama_matkul_idx].find("div").text.split("-")[1].strip()
        perkuliahan_table = rows_matkul_table[table_idx].find("div", id="tabs-2").find("tbody")
        absensi_table = rows_matkul_table[table_idx].find("div", id="tabs-1").find_all("tr")
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
