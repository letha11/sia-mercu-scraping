import logging

from flask import jsonify, request
from jwt.exceptions import (
    ExpiredSignatureError,
    InvalidSignatureError,
    InvalidTokenError,
)
from requests.exceptions import Timeout


def get_bearer_token() -> str | None:
    """Extract and validate the bearer token from the request headers."""
    bearer = request.headers.get("Authorization")
    if not bearer or len(bearer.split()) < 2:
        return None
    return bearer.split()[1]


def handle_exceptions(e: Exception):
    """Handle generic and specific exceptions."""
    if isinstance(e, ExpiredSignatureError):
        return (
            jsonify(
                {"success": False, "message": "Token expired, try logging in again"}
            ),
            401,
        )
    if isinstance(e, InvalidTokenError):
        return (
            jsonify(
                {"success": False, "message": "Invalid token, try logging in again"}
            ),
            401,
        )
    if isinstance(e, Timeout):
        return (
            jsonify(
                {
                    "success": False,
                    "message": "The host website is currently down, please try again later",
                }
            ),
            503,
        )
    logging.error(e)
    return jsonify({"success": False, "message": "Something went wrong"}), 500
