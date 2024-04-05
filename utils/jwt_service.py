import jwt

from datetime import datetime, timedelta, timezone
from typing import Any


class JWT_Service:
    def __init__(self, secret_key: str):
        self.secret_key = secret_key

    # expiration_time only support hours and days,
    # the format are: {number}{h/d}, 7h, 30d
    def generate_token(
        self, payload: dict[str, Any], expiration_time: str = "7h"
    ) -> str:
        expiration_timedelta: timedelta

        if expiration_time[-1] == "h":
            expiration_time = expiration_time[:-1]  # remove the last character
            expiration_timedelta = timedelta(hours=int(expiration_time))
        else:
            expiration_time = expiration_time[:-1]
            expiration_timedelta = timedelta(days=int(expiration_time))

        payload["exp"] = datetime.now(timezone.utc) + expiration_timedelta
        token = jwt.encode(payload, self.secret_key, algorithm="HS256")
        return token

    # This decode_token can be used for verifying a JWT token
    def decode_token(self, token: str) -> dict[str, Any]:
        return jwt.decode(token, self.secret_key, algorithms=["HS256"])
