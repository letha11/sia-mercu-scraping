import locale
import requests
import logging
from flask import Flask, jsonify, request

from pages.pages import Pages

# For formatting date from string of indonesian locale date to datetime object
locale.setlocale(locale.LC_TIME, "id_ID.utf8")

logging.basicConfig(
    format="%(asctime)s : (%(levelname)s) : %(message)s", level=logging.DEBUG
)

app = Flask(__name__)

session = requests.session()
session.headers[
    "user-agent"
] = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"

pages = Pages(session)


@app.route("/")
def root():
    return "Scraping API!"


@app.route("/login", methods=["POST"])
def login_route():
    data = request.form

    try:
        username = data["username"]
        password = data["password"]
        result = pages.login(username=username, password=password)

        if result is None:
            return (
                jsonify(
                    {
                        "success": False,
                        "message": "Invalid Credentials",
                    }
                ),
                401,
            )

        return jsonify(
            {
                "success": True,
                "message": "Login success",
                "token": result,
            }
        )
    except KeyError as error:
        return (
            jsonify(
                {
                    "success": False,
                    "message": "You need to fill username and password",
                },
            ),
            400,
        )
    except Exception as error:
        return jsonify(
            {
                "success": False,
                "message": "Something went wrong",
            },
        )


@app.route("/jadwal", methods=["GET"])
def jadwal():
    periode_args = request.args.get("periode")
    bearer = request.headers.get('Authorization')
    if bearer is None :
        return (
            jsonify(
                {
                    "success": False,
                    "message": "You need to log in first",
                }
            ),
            401,
        )

    bearer_splitted = bearer.split()
    if len(bearer_splitted) < 1:
        return (
            jsonify(
                {
                    "success": False,
                    "message": "You need to log in first",
                }
            ),
            401,
        )

    token = bearer_splitted[1]

    result = pages.scrape_jadwal(token, periode_args or '')

    if result is None:
        return (
            jsonify(
                {
                    "success": False,
                    "message": "You need to log in first",
                }
            ),
            401,
        )

    return (
        jsonify(
            {
                "success": True,
                "data": result,
            }
        ),
        200,
    )


@app.route("/home", methods=["GET"])
def home():
    bearer = request.headers.get('Authorization')
    if bearer is None :
        return (
            jsonify(
                {
                    "success": False,
                    "message": "You need to log in first",
                }
            ),
            401,
        )

    bearer_splitted = bearer.split()
    if len(bearer_splitted) < 1:
        return (
            jsonify(
                {
                    "success": False,
                    "message": "You need to log in first",
                }
            ),
            401,
        )

    token = bearer_splitted[1]

    result = pages.scrape_home(token)
    if result is None:
        return (
            jsonify(
                {
                    "success": False,
                    "message": "You need to log in first",
                }
            ),
            401,
        )

    return (
        jsonify(
            {
                "success": True,
                "data": result,
            }
        ),
        200,
    )

if __name__ == "__main__":
    app.run()
