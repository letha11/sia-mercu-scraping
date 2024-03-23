import requests
import os
import logging
from requests.exceptions import Timeout
import sqlalchemy

from jwt.exceptions import (
    ExpiredSignatureError,
    InvalidSignatureError,
    InvalidTokenError,
)
from flask import Flask, jsonify, request, Blueprint
from flask_swagger_ui import get_swaggerui_blueprint
from sqlalchemy.orm import Session
from models.base_model import Base
from models.user import User
from pages.pages import Pages
from repository.user_repository import UserRepositoryImpl
from dotenv import load_dotenv
from cryptography.fernet import Fernet
from utils.auth_helper import AuthHelper
from utils.jwt_service import JWT_Service

load_dotenv()

logging.basicConfig(
    format="%(asctime)s : (%(levelname)s) : %(message)s", level=logging.DEBUG
)

SWAGGER_URL = ""
API_URL = "/static/swagger.json"

swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={"app_name": "sia-scraping"},
)

blueprint = Blueprint("api", __name__, url_prefix="/api")

app = Flask(__name__)

app.register_blueprint(swaggerui_blueprint)
app.register_blueprint(blueprint)

session = requests.session()
session.headers["user-agent"] = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
)

db_engine = sqlalchemy.create_engine("sqlite:///data.db")
Base.metadata.create_all(db_engine)
db_session = Session(db_engine)

encryption_key = os.getenv("ENCRYPT_KEY")
JWT_SECRET = os.getenv("JWT_SECRET")
assert encryption_key is not None
assert JWT_SECRET is not None

FERNET = Fernet(encryption_key)

jwt_service = JWT_Service(secret_key=JWT_SECRET)

auth_helper = AuthHelper(encryptor=FERNET)
user_repository = UserRepositoryImpl(db_session, auth_helper)

pages = Pages(
    session,
    jwt_service=jwt_service,
    user_repository=user_repository,
    auth_helper=auth_helper,
)


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
    except KeyError as _:
        return (
            jsonify(
                {
                    "success": False,
                    "message": "You need to fill username and password",
                },
            ),
            400,
        )
    except Timeout as _:
        return (
            jsonify(
                {
                    "success": False,
                    "message": "The host website are currently down, please try again later.",
                },
            ),
            503,
        )
    except Exception as _:
        return jsonify(
            {
                "success": False,
                "message": "Something went wrong",
            },
        )


@app.route("/api/jadwal", methods=["GET"])
def jadwal():
    periode_args = request.args.get("periode")
    bearer = request.headers.get("Authorization")
    if bearer is None:
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

    try:
        result = pages.scrape_jadwal(token, periode_args or "")

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
    except ExpiredSignatureError as _:
        return (
            jsonify(
                {
                    "success": False,
                    "message": "Token expired, try logging in again",
                }
            ),
            401,
        )
    except InvalidTokenError as _:
        return (
            jsonify(
                {
                    "success": False,
                    "message": "Invalid token, try logging in again",
                }
            ),
            401,
        )
    except Timeout as _:
        return (
            jsonify(
                {
                    "success": False,
                    "message": "The host website are currently down, please try again later.",
                },
            ),
            503,
        )
    except Exception as _:
        return (
            jsonify(
                {
                    "success": False,
                    "message": "Something went wrong",
                }
            ),
            401,
        )


@app.route("/api/home", methods=["GET"])
def home():
    bearer = request.headers.get("Authorization")
    if bearer is None:
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

    try:
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
    except ExpiredSignatureError as _:
        return (
            jsonify(
                {
                    "success": False,
                    "message": "Token expired, try logging in again",
                }
            ),
            401,
        )
    except InvalidSignatureError as _:
        return (
            jsonify(
                {
                    "success": False,
                    "message": "Invalid signature, try logging in again",
                }
            ),
            401,
        )
    except InvalidTokenError as _:
        return (
            jsonify(
                {
                    "success": False,
                    "message": "Invalid token, try logging in again",
                }
            ),
            401,
        )
    except Timeout as _:
        return (
            jsonify(
                {
                    "success": False,
                    "message": "The host website are currently down, please try again later.",
                },
            ),
            503,
        )
    except Exception as _:
        return (
            jsonify(
                {
                    "success": False,
                    "message": "Something went wrong",
                }
            ),
            401,
        )


@app.route("/api/detail", methods=["GET"])
def detail():
    bearer = request.headers.get("Authorization")
    if bearer is None:
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

    try:
        result = pages.scrape_detail_mhs(token)
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
    except Exception as _:
        return (
            jsonify(
                {
                    "success": False,
                    "message": "Something went wrong",
                }
            ),
            401,
        )


@app.route("/api/dump", methods=["GET"])
def dump():
    user = user_repository.get("41522010137")
    print(user)
    if type(user) is User:
        print(f"user after before: {auth_helper.decrypt(user.phpsessid)}")
        result_update = user_repository.update("41522010137", PHPSESSID="123450132921")
        print(result_update)
        print(f"user after update: {user}")

    return "success"


if __name__ == "__main__":
    app.run()
