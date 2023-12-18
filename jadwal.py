import logging
from bs4 import BeautifulSoup

def get_periode(soup_jadwal: BeautifulSoup):
    logging.info('Getting Periode')
    periode = []
    periode_html = soup_jadwal.find(id="periode")

    for periode_item in periode_html.find_all("option"):
        label = periode_item.text.strip()
        value = periode_item["value"]
        periode.append({"label": label, "value": value})
    
    logging.info('Finished extracting periode')
    return periode


def clean_nama_matkul(element):
    # Filtering empty string
    nama_matkul_clean = list(filter(None, [cs.text.strip() for cs in element.contents]))

    nama_matkul = " ".join(nama_matkul_clean)

    return nama_matkul


def get_matkul(soup_jadwal: BeautifulSoup):
    logging.info('Getting Mata Kuliah')
    matkul = []

    matkul_table = soup_jadwal.find_all("table")[-1]
    matkul_list = matkul_table.find("tbody").find_all("tr")

    for i in range(0, len(matkul_list), 2):
        content = matkul_list[i].find_all("td")

        content = [
            clean_nama_matkul(item)
            if item.find("i") != None
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
        
    logging.info('Finished Getting Mata Kuliah')
    return matkul

def get_jadwal(soup_jadwal: BeautifulSoup):
    periode = get_periode(soup_jadwal)
    matkul = get_matkul(soup_jadwal)
    
    return {
        'periode': periode,
        'mata_kuliah': matkul,
    }

