import datetime
from dataclasses import dataclass

from sqlalchemy import BigInteger, Boolean, Column, ForeignKey, Text, Integer, DateTime
from sqlalchemy.orm import relationship

from app.store.database.sqlalchemy_base import db


@dataclass
class Game:
    id: int
    started_at: datetime.datetime
    ended_at: datetime.datetime


@dataclass
class Statistic:
    id: int
    user_id: int
    game_id: int
    points: int
    failures: int


@dataclass
class Roadmap:
    id: int
    game_id: int
    question_id: int
    status: bool


@dataclass
class GameAnswer:
    id: int
    game_id: int
    answer_id: int
    user_id: int


@dataclass
class User:
    id: int
    vk_id: int
    first_name: str
    last_name: str


@dataclass
class Question:
    id: int
    title: str
    factor: int


@dataclass
class Answer:
    id: int
    title: str
    question_id: int
    score: int


class GameModel(db):
    __tablename__ = "Game"
    id = Column(BigInteger, primary_key=True, nullable=False)
    started_at = Column(DateTime)
    ended_ad = Column(DateTime)


class UserModel(db):
    __tablename__ = "User"
    id = Column(BigInteger, primary_key=True, nullable=False)
    vk_id = Column(BigInteger, nullable=False, unique=True)
    first_name = Column(Text, nullable=True)
    last_name = Column(Text, nullable=True)


class StatisticModel(db):
    __tablename__ = "Statistic"
    id = Column(BigInteger, primary_key=True, nullable=False)
    points = Column(BigInteger, nullable=False, default=0)
    failures = Column(BigInteger, default=0)

    game_id = Column(BigInteger, ForeignKey("Game.id"))
    user_id = Column(BigInteger, ForeignKey("User.id"))

class RoadMapModel(db):
    __tablename__ = "RoadMap"
    id = Column(BigInteger, primary_key=True, nullable=False)
    status = Column(Boolean, nullable=False, default=False)

    game_id = Column(BigInteger, ForeignKey("Question.id"))
    question_id = Column(BigInteger, ForeignKey("Question.id"))


class GameAnswersModel(db):
    __tablename__ = "GameAnswer"
    id = Column(BigInteger, primary_key=True, nullable=False)

    answer_id = Column(BigInteger, ForeignKey("Answer.id"))
    game_id = Column(BigInteger, ForeignKey("Game.id"))
    user_id = Column(BigInteger, ForeignKey("User.id"))


class QuestionModel(db):
    __tablename__ = "Question"
    id = Column(BigInteger, primary_key=True, nullable=False)
    title = Column(Text, nullable=False, unique=True)
    factor = Column(Integer, nullable=False, default=1)

    answers = relationship("AnswerModel", back_populates="question", cascade="all, delete")


class AnswerModel(db):
    __tablename__ = "Answer"
    id = Column(BigInteger, primary_key=True)
    title = Column(Text, unique=True, nullable=False)
    score = Column(Integer, nullable=False)

    question_id = Column(BigInteger, ForeignKey("Question.id", ondelete="CASCADE"))
    question = relationship("QuestionModel", back_populates="answers")
