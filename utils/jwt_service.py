import jwt

from datetime import datetime, timedelta
from typing import Any

class JWT_Service:
    def __init__(self, secret_key: str):
        self.secret_key = secret_key

    def generate_token(self, payload: dict[str, Any]) -> str:
        payload["exp"] = datetime.utcnow() + timedelta(days=3)
        token = jwt.encode(payload, self.secret_key, algorithm="HS256")
        return token

    def decode_token(self, token: str) -> dict[str, Any]:
        return jwt.decode(token, self.secret_key, algorithms=["HS256"])
