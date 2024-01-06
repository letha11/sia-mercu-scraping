import requests
import logging
from flask import Flask, jsonify, request, Blueprint
from flask_swagger_ui import get_swaggerui_blueprint

from pages.pages import Pages

logging.basicConfig(
    format="%(asctime)s : (%(levelname)s) : %(message)s", level=logging.DEBUG
)

SWAGGER_URL = '' 
API_URL = '/static/swagger.json' 

swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={ 
        'app_name': "sia-scraping"
    },
)

blueprint = Blueprint("api", __name__, url_prefix="/api")

app = Flask(__name__)

app.register_blueprint(swaggerui_blueprint)
app.register_blueprint(blueprint)

session = requests.session()
session.headers[
    "user-agent"
] = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"

pages = Pages(session)

@app.route("/api/login", methods=["POST"])
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


@app.route("/api/jadwal", methods=["GET"])
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


@app.route("/api/home", methods=["GET"])
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
