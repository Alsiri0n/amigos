from dataclasses import dataclass
from typing import Optional
from sqlalchemy import Column, BigInteger, Text


from app.store.database.sqlalchemy_base import db

@dataclass
class Admin:
    id: int
    email: str
    password: Optional[str] = None

    def is_password_valid(self, password: str):
        pass

    @classmethod
    def from_method(cls, session:Optional[dict]) -> Optional["Admin"]:
        pass


class AdminModel(db):
    __tablename__ = "admins"
    id = Column(BigInteger, primary_key=True)
    email = Column(Text, nullable=False)
    password = Column(Text, nullable=False)
