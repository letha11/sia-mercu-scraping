import requests
import os
import logging
import sqlalchemy
import io

from sqlalchemy.sql import except_
from sqlalchemy_utils import database_exists, create_database
from requests.exceptions import Timeout
from requests.adapters import HTTPAdapter
from flask import Flask, jsonify, request, Blueprint, send_file
from flask_swagger_ui import get_swaggerui_blueprint
from sqlalchemy.orm import Session
from controller.controller import Controller
from models.base_model import Base
from models.status import Status
from models.flavor import Flavor
from repository.user_repository import UserRepositoryImpl
from dotenv import load_dotenv
from cryptography.fernet import Fernet
import utils
from utils.auth_helper import AuthHelper
from utils.jwt_service import JWT_Service
from urllib3.util.retry import Retry
from flask_cors import CORS, cross_origin
from utils.helper import handle_exceptions, get_bearer_token
from xhtml2pdf import pisa


load_dotenv()
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

allowed_origins = ["http://localhost:5000", "https://sia-mercu-scraping.vercel.app"]

app = Flask(__name__)
CORS(
    app,
    origins="*",
    methods=["GET", "POST", "OPTIONS", "PUT", "DELETE"],
    allow_headers="*",
)

base_url = ""

raw_flavor = os.getenv("ENV")
assert raw_flavor is not None
flavor: Flavor = Flavor.parse(raw_flavor)

if flavor.is_dev:
    base_url = "http://localhost:5000"
else:
    base_url = "https://sia-mercu-scraping.vercel.app"

app.register_blueprint(swaggerui_blueprint)
app.register_blueprint(blueprint)

session = requests.session()
retry = Retry(total=2, backoff_factor=0.1)
adapter = HTTPAdapter(max_retries=retry)
session.mount("http://", adapter)
session.mount("https://", adapter)
session.headers["user-agent"] = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
)

if flavor.is_dev:
    db_engine = sqlalchemy.create_engine(
        f"postgresql+psycopg2://{os.getenv('DB_USERNAME')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
    )
else:
    db_engine = sqlalchemy.create_engine(
        f"postgresql+psycopg2://{os.getenv('DB_USERNAME')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}?sslmode=require"
    )

if not database_exists(db_engine.url):
    create_database(db_engine.url)

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
        captcha = data["captcha"]
        result = controller.login(username=username, password=password, captcha=captcha)

        if result is None:
            return (
                jsonify(
                    {
                        "success": False,
                        "message": "Invalid Credentials or captcha",
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
                    "message": "You need to fill username and password and captcha",
                },
            ),
            400,
        )
    except Exception as e:
        return handle_exceptions(e)


@app.route("/api/refresh-token", methods=["POST"])
@cross_origin(origins=allowed_origins)
def refresh_token():
    refresh_token = get_bearer_token()
    if refresh_token is None:
        return (
            jsonify(
                {
                    "success": False,
                    "message": "No refresh token provided",
                }
            ),
            401,
        )

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
    except Exception as e:
        return handle_exceptions(e)


@app.route("/api/jadwal", methods=["GET"])
@cross_origin(origins=allowed_origins)
def jadwal():
    periode_args = request.args.get("periode")

    token = get_bearer_token()
    if token is None:
        return (
            jsonify(
                {
                    "success": False,
                    "message": "You need to log in first",
                }
            ),
            401,
        )

    try:
        result = controller.scrape_jadwal(token, periode_args or "")

        if result is None:
            return (
                jsonify(
                    {
                        "success": False,
                        "message": "Something went wrong within the server, contact administrator.",
                    }
                ),
                500,
            )

        if result is Status.UNAUTHORIZED:
            return (
                jsonify(
                    {
                        "success": False,
                        "message": "You need to log in first",
                    }
                ),
                401,
            )

        if result is Status.RELOGIN_NEEDED:
            return (
                jsonify(
                    {
                        "success": False,
                        "message": "You need to relog in first",
                        "captcha_url": f"{base_url}/api/captcha",
                        "relog_url": f"{base_url}/api/relogin",
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
    except Exception as e:
        return handle_exceptions(e)

@app.route("/api/attendance", methods=["GET"])
@cross_origin(origins=allowed_origins)
def attendance():
    token = get_bearer_token()
    if token is None:
        return (
            jsonify(
                {
                    "success": False,
                    "message": "You need to log in first",
                }
            ),
            401,
        )

    try:
        result = controller.scrape_attendance(token)

        if result is None:
            return (
                jsonify(
                    {
                        "success": False,
                        "message": "Something went wrong within the server, contact administrator.",
                    }
                ),
                500,
            )

        if result is Status.UNAUTHORIZED:
            return (
                jsonify(
                    {
                        "success": False,
                        "message": "You need to log in first",
                    }
                ),
                401,
            )

        if result is Status.RELOGIN_NEEDED:
            return (
                jsonify(
                    {
                        "success": False,
                        "message": "You need to relog in first",
                        "captcha_url": f"{base_url}/api/captcha",
                        "relog_url": f"{base_url}/api/relogin",
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
    except Exception as e:
        return handle_exceptions(e)

@app.route("/api/captcha", methods=["GET"])
@cross_origin(origins=allowed_origins)
def captcha_image():
    try:
        isPreview = request.args.get("preview")

        if isPreview is not None and isPreview == "true":
            return f"<img src='{base_url}/api/captcha' />"

        result = controller.get_captcha()

        return result
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

@app.route("/api/transcript/download", methods=["GET"])
@cross_origin(origins=allowed_origins)
def download_transcript():
    token = get_bearer_token()

    if token is None:
        return (
            jsonify(
                {
                    "success": False,
                    "message": "You need to log in first",
                }
            ),
            401,
        )

    try:
        result = controller.download_transcript(token)
        return result
    except Exception as e:
        return handle_exceptions(e)

@app.route("/api/transcript")
@cross_origin(origins=allowed_origins)
def transcript():
    token = get_bearer_token()

    if token is None:
        return (
            jsonify(
                {
                    "success": False,
                    "message": "You need to log in first",
                }
            ),
            401,
        )

    try:
        result = controller.scrape_transcript(token)

        if result is None:
            return (
                jsonify(
                    {
                        "success": False,
                        "message": "Something went wrong within the server, contact administrator.",
                    }
                ),
                500,
            )

        if result is Status.UNAUTHORIZED:
            return (
                jsonify(
                    {
                        "success": False,
                        "message": "You need to log in first",
                    }
                ),
                401,
            )
        
        if result is Status.RELOGIN_NEEDED:
            return (
                jsonify(
                    {
                        "success": False,
                        "message": "You need to relog in first",
                        "captcha_url": f"{base_url}/api/captcha",
                        "relog_url": f"{base_url}/api/relogin",
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
    except Exception as e:
        return handle_exceptions(e)


@app.route("/api/detail", methods=["GET"])
@cross_origin(origins=allowed_origins)
def detail():
    token = get_bearer_token()

    if token is None:
        return (
            jsonify(
                {
                    "success": False,
                    "message": "You need to log in first",
                }
            ),
            401,
        )

    try:
        result = controller.scrape_detail_mhs(token)
        if result is None:
            return (
                jsonify(
                    {
                        "success": False,
                        "message": "Something went wrong within the server, contact administrator.",
                    }
                ),
                500,
            )

        if result is Status.UNAUTHORIZED:
            return (
                jsonify(
                    {
                        "success": False,
                        "message": "You need to log in first",
                    }
                ),
                401,
            )

        if result is Status.RELOGIN_NEEDED:
            return (
                jsonify(
                    {
                        "success": False,
                        "message": "You need to relog in first",
                        "captcha_url": f"{base_url}/api/captcha",
                        "relog_url": f"{base_url}/api/relogin",
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
    except Exception as e:
        return handle_exceptions(e)


@app.route("/api/relogin", methods=["POST"])
@cross_origin(origins=allowed_origins)
def relogin_route():
    token = get_bearer_token()

    if token is None:
        return (
            jsonify(
                {
                    "success": False,
                    "message": "Unauthorized, token required to relogin",
                }
            ),
            401,
        )

    data = request.form

    try:
        captcha = data["captcha"]
        result = controller.relogin(token, captcha)

        if result is Status.UNAUTHORIZED:
            return (
                jsonify(
                    {
                        "success": False,
                        "message": "You need to log in first",
                    }
                ),
                401,
            )

        if result is None:
            return (
                jsonify(
                    {
                        "success": False,
                        "message": "Captcha is invalid, try again",
                    }
                ),
                400,
            )

        return (
            jsonify(
                {
                    "success": True,
                }
            ),
            200,
        )
    except Exception as e:
        return handle_exceptions(e)


if __name__ == "__main__":
    app.run(debug=True)
