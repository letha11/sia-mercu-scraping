from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Integer, String
from models.base_model import Base

class User(Base):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(150))
    password: Mapped[str] = mapped_column(String(150))
    phpsessid: Mapped[str] = mapped_column(String(255))

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username={self.username}, password={self.password}, phpsessid={self.phpsessid})>"
