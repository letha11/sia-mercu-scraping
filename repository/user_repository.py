from abc import ABC, abstractmethod
from sqlalchemy import select, update
from sqlalchemy.orm import Session
from models.user import User
from utils.auth_helper import AuthHelper

class UserRepository(ABC):
    @abstractmethod
    def get(self, username):
        pass

    @abstractmethod
    def save(self, username, password, PHPSESSID):
        pass

    @abstractmethod
    def update(
        self,
        username,
        PHPSESSID,
        password,
    ):
        pass


class UserRepositoryImpl(UserRepository):
    def __init__(self, db_session: Session, auth_helper: AuthHelper):
        self.db_session = db_session
        self.auth_helper = auth_helper

    def get(self, username: str):
        query = select(User).where(User.username == username)
        result = self.db_session.scalar(query)
        return result

    # Password in update are for edge cases when user change their password on the SIA website
    def update(
        self,
        username: str,
        password = None,
        PHPSESSID = None,
    ):
        user = self.get(username)

        if user is None:
            return False # User not found

        encrypted_password = (
            self.auth_helper.encrypt(password) if password is not None else user.password
        )
        encrypted_phpsessid = (
            self.auth_helper.encrypt(PHPSESSID) if PHPSESSID is not None else user.phpsessid
        )
        query = (
            update(User)
            .where(User.username == username)
            .values(password=encrypted_password, phpsessid=encrypted_phpsessid)
        )

        self.db_session.execute(query)
        self.db_session.commit()

        return True

    def save(self, username: str, password: str, PHPSESSID: str):
        encrypted_password = self.auth_helper.encrypt(password)
        encrypted_phpsessid = self.auth_helper.encrypt(PHPSESSID)
        new_user = User(
            username=username,
            password=encrypted_password,
            phpsessid=encrypted_phpsessid,
        )

        self.db_session.add(new_user)
        self.db_session.commit()

        return new_user
