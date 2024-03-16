from cryptography.fernet import Fernet

class AuthHelper():
    def __init__(self, encryptor: Fernet):
        self.encryptor = encryptor

    def encrypt(self, data: str) -> bytes:
        return self.encryptor.encrypt(data.encode())

    def decrypt(self, data: str) -> str:
        return self.encryptor.decrypt(data).decode()

