import base64
from cryptography.fernet import Fernet

class AuthHelper():
    def __init__(self, encryptor: Fernet):
        self.encryptor = encryptor

    def encrypt(self, data: str) -> str:
        return self.encryptor.encrypt(data.encode()).decode()

    def decrypt(self, data: str) -> str:
        # return self.encryptor.decrypt(base64.b64encode(data)).decode()
        return self.encryptor.decrypt(data.encode()).decode()

