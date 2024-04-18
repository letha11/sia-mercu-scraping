import requests
import os
import logging
import sqlalchemy

from jwt.exceptions import (
    ExpiredSignatureError,
    InvalidSignatureError,
    InvalidTokenError,
)
from requests.exceptions import Timeout
from requests.adapters import HTTPAdapter
from flask import Flask, jsonify, request, Blueprint
from flask_swagger_ui import get_swaggerui_blueprint
from sqlalchemy.orm import Session
from controller.controller import Controller
from models.base_model import Base
from models.user import User
from repository.user_repository import UserRepositoryImpl
from dotenv import load_dotenv
from cryptography.fernet import Fernet
from utils.auth_helper import AuthHelper
from utils.jwt_service import JWT_Service
from urllib3.util.retry import Retry
from flask_cors import CORS, cross_origin


load_dotenv(".env.local")
load_dotenv(".env.prod")
load_dotenv(".env")

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

allowed_origins = [
    "http://localhost:5000",
    "https://sia-mercu-scraping.vercel.app"
]

app = Flask(__name__)
CORS(app, origins="*", methods=["GET", "POST", "OPTIONS", "PUT", "DELETE"], allow_headers="*")

app.register_blueprint(swaggerui_blueprint)
app.register_blueprint(blueprint)

session = requests.session()
retry = Retry(connect=5, backoff_factor=0.5)
adapter = HTTPAdapter(max_retries=retry)
session.mount('http://', adapter)
session.mount('https://', adapter)
session.headers["user-agent"] = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
)

db_engine = sqlalchemy.create_engine(f"postgresql+psycopg2://{os.getenv('DB_USERNAME')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}?sslmode=require")
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

controller = Controller(
    session,
    jwt_service=jwt_service,
    user_repository=user_repository,
    auth_helper=auth_helper,
)


@app.route("/api/login", methods=["POST"])
@cross_origin(origins=allowed_origins)
def login_route():
    data = request.form

    try:
        username = data["username"]
        password = data["password"]
        result = controller.login(username=username, password=password)

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
                "token": result[0],
                "refresh_token": result[1],
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
    except Exception as e:
        logging.error(e)
        return (jsonify(
            {
                "success": False,
                "message": "Something went wrong",
            },
            500,
        ))


@app.route("/api/refresh-token", methods=["POST"])
@cross_origin(origins=allowed_origins)
def refresh_token():
    bearer = request.headers.get("Authorization")
    if bearer is None:
        return (
            jsonify(
                {
                    "success": False,
                    "message": "No refresh token provided",
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
                    "message": "No refresh token provided",
                }
            ),
            401,
        )

    refresh_token = bearer_splitted[1]

    try:
        new_token, new_refresh_token = controller.refresh_token(
            refresh_token=refresh_token
        )

        return jsonify(
            {
                "success": True,
                "token": new_token,
                "refresh_token": new_refresh_token,
            }
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
            500,
        )


@app.route("/api/jadwal", methods=["GET"])
@cross_origin(origins=allowed_origins)
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
        result = controller.scrape_jadwal(token, periode_args or "")

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
            500,
        )


@app.route("/api/attendance", methods=["GET"])
@cross_origin(origins=allowed_origins)
def attendance():
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
        result = controller.scrape_home(token)
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
            500,
        )


@app.route("/api/detail", methods=["GET"])
@cross_origin(origins=allowed_origins)
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
        result = controller.scrape_detail_mhs(token)
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
    except Exception as e:
        return (
            jsonify(
                {
                    "success": False,
                    "message": "Something went wrong",
                    "stacktrace": e,
                }
            ),
            500,
        )


if __name__ == "__main__":
    app.run(debug=True)
