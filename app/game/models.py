from dataclasses import dataclass

from sqlalchemy import BigInteger, Column, ForeignKey, Text, Integer
from sqlalchemy.orm import relationship

from app.store.database.sqlalchemy_base import db


@dataclass
class Question:
    id: int | None
    title: str
    answers: list["Answer"]


@dataclass
class Answer:
    title: str
    points: int


class QuestionModel(db):
    __tablename__ = "questions"
    id = Column(BigInteger, primary_key=True, nullable=False)
    title = Column(Text, nullable=False, unique=True)

    answers = relationship("AnswerModel", back_populates="question", cascade="all, delete")


class AnswerModel(db):
    __tablename__ = "answers"
    id = Column(BigInteger, primary_key=True)
    title = Column(Text, unique=True, nullable=False)
    points = Column(Integer, nullable=False)

    question_id = Column(BigInteger, ForeignKey("questions.id", ondelete="CASCADE"))
    question = relationship("QuestionModel", back_populates="answers")
