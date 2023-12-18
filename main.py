import os

import requests, requests.cookies
import datetime as DT
import logging
from bs4 import BeautifulSoup

# Local
import jadwal as jd

logging.basicConfig(format='%(asctime)s : (%(levelname)s) : %(message)s', level=logging.DEBUG)

# 1. Check if phpsessid are null
# 2. if yes then login and store the new phpsessid
# 3. if not check the max_age/already passed the max_age from the first login (so we need to save the time when the first login get executed)
# 4. if already exceed, then login again and set new phpsessid

url = "https://sia.mercubuana.ac.id/akad.php/home"

username = "41522010137"
password = "02052004"

# phpsessid = "7steia4mrastaqveotajj68ug6"
phpsessid = ""
login_timestamp = None
expired_date = None

# cookie_jar = requests.cookies.cookiejar_from_dict({"PHPSESSID": phpsessid})

payload_login = {"act": "login", "username": username, "password": "02052004"}

session = requests.session()
session.headers[
    "user-agent"
] = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"


def login(username, password):
    logging.info('Login in process')
    global login_timestamp, expired_date, phpsessid
    login_url = "https://sia.mercubuana.ac.id/gate.php/login"
    login_timestamp = DT.datetime.now()
    expired_date = login_timestamp + DT.timedelta(hours=1)
    login_result = session.post(
        login_url, data={"act": "login", "username": username, "password": password}
    )

    phpsessid = session.cookies["PHPSESSID"]

    data = {
        "username": username,
        "PHPSESSID": phpsessid,
        "login_timestamp": str(login_timestamp),
        "expired_date": str(expired_date),
    }

    with open("history.txt", "w") as f:
        f.write(str(data))
        f.close()
    logging.info('Login Finished')



# First time
if not os.path.isfile("./history.txt"):
    login(username, password)
else:
    with open("history.txt", "r") as f:
        dict_result = eval(f.read())  # text = f.read().strip()
        print(dict_result["username"])
        username = dict_result["username"]
        phpsessid = dict_result["PHPSESSID"]
        login_timestamp = DT.datetime.strptime(
            dict_result["login_timestamp"], "%Y-%m-%d %H:%M:%S.%f"
        )
        expired_date = DT.datetime.strptime(
            dict_result["expired_date"], "%Y-%m-%d %H:%M:%S.%f"
        )

    # Exceed login time
    if login_timestamp >= expired_date:
        logging.info("Exceed Login Time")
        login(username, password)


cookie_jar = requests.cookies.cookiejar_from_dict({"PHPSESSID": phpsessid})
home_result = session.get(url, cookies=cookie_jar)

if home_result.status_code == 302 or home_result.url == 'https://sia.mercubuana.ac.id/gate.php/login':
    login(username, password)
#
with open("result_home.html", "w") as f:
    f.write(home_result.text)

jadwal_url = "https://sia.mercubuana.ac.id/akad.php/biomhs/jadwal"
jadwal_result = session.post(
    jadwal_url,
    data={
        "act": "",
        "key": "",
        "format": "",
        "filter_num_record": "",
        "filter_string": "",
        "filter_sort": "",
        "filter_page": "",
        "filter_field_search_list": "",
        "periode": 20231,
    },
    cookies=cookie_jar,
)

# print(test.text)
with open("result_jadwal.html", "w") as f:
    f.write(jadwal_result.text)

soup_jadwal = BeautifulSoup(jadwal_result.text, features="lxml")

for matkul in jd.get_jadwal(soup_jadwal)['mata_kuliah']:
    print(matkul['hari'])
# print(jd.get_jadwal(soup_jadwal))
# print(soup_jadwal.prettify())


# print(test.)
# print(cookie_jar)
