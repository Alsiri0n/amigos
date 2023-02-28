from dataclasses import dataclass
from hashlib import sha256
from typing import Optional

from sqlalchemy import Column, BigInteger, Text, Boolean

from app.store.database.sqlalchemy_base import db


@dataclass
class Admin:
    id: int
    vk_id: int
    email: str | None
    password: Optional[str] = None

    def is_password_valid(self, password: str):
        return self.password == sha256(password.encode()).hexdigest()

    @classmethod
    def from_session(cls, session: Optional[dict]) -> Optional["Admin"]:
        return cls(id=session["admin"]["id"],
                   email=session["admin"]["email"],
                   vk_id=session["admin"]["vk_id"])


class AdminModel(db):
    __tablename__ = "admins"
    id = Column(BigInteger, primary_key=True)
    vk_id = Column(BigInteger, nullable=False, unique=True)
    email = Column(Text, nullable=False, unique=True)
    password = Column(Text, nullable=False)

    def to_dc(self) -> Admin:
        return Admin(
            id=self.id,
            vk_id=self.vk_id,
            email=self.email,
            password=self.password,
        )