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
    answers: list["Answer"]
    #factor: int


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
    ended_at = Column(DateTime, nullable=True)

    statistic = relationship("StatisticModel", back_populates="game")
    road_map = relationship("RoadMapModel", back_populates="game")
    game_answer = relationship("GameAnswersModel", back_populates="game")

    def to_dc(self):
        return Game(
            id=self.id,
            started_at=self.started_at,
            ended_at=self.ended_at,
        )


class UserModel(db):
    __tablename__ = "User"
    id = Column(BigInteger, primary_key=True, nullable=False)
    vk_id = Column(BigInteger, nullable=False, unique=True)
    first_name = Column(Text, nullable=True)
    last_name = Column(Text, nullable=True)

    game_answer = relationship("GameAnswersModel", back_populates="user")
    statistic = relationship("StatisticModel", back_populates="user")

    def to_dc(self) -> User:
        return User(
            id=self.id,
            vk_id=self.vk_id,
            first_name=self.first_name,
            last_name=self.last_name,
        )


class StatisticModel(db):
    __tablename__ = "Statistic"
    id = Column(BigInteger, primary_key=True, nullable=False)
    points = Column(BigInteger, nullable=False, default=0)
    failures = Column(BigInteger, default=0)

    game_id = Column(BigInteger, ForeignKey("Game.id"))
    game = relationship("GameModel", back_populates="statistic")

    user_id = Column(BigInteger, ForeignKey("User.id"))
    user = relationship("UserModel", back_populates="statistic")


class RoadMapModel(db):
    __tablename__ = "RoadMap"
    id = Column(BigInteger, primary_key=True, nullable=False)
    status = Column(Boolean, nullable=False, default=False)

    game_id = Column(BigInteger, ForeignKey("Game.id"))
    game = relationship("GameModel", back_populates="road_map")

    question_id = Column(BigInteger, ForeignKey("Question.id"))
    question = relationship("QuestionModel", back_populates="road_map")


class GameAnswersModel(db):
    __tablename__ = "GameAnswer"
    id = Column(BigInteger, primary_key=True, nullable=False)

    answer_id = Column(BigInteger, ForeignKey("Answer.id"))
    answer = relationship("AnswerModel", back_populates="game_answer")

    game_id = Column(BigInteger, ForeignKey("Game.id"))
    game = relationship("GameModel", back_populates="game_answer")

    user_id = Column(BigInteger, ForeignKey("User.id"))
    user = relationship("UserModel", back_populates="game_answer")


class QuestionModel(db):
    __tablename__ = "Question"
    id = Column(BigInteger, primary_key=True, nullable=False)
    title = Column(Text, nullable=False, unique=True)

    answers = relationship("AnswerModel", back_populates="question", cascade="all, delete")
    road_map = relationship("RoadMapModel", back_populates="question")

    def to_dc(self):
        return Question(
            id=self.id,
            title=self.title,
            answers=[Answer(
                id=a.answers.id,
                title=a.answers.title,
                score=a.answers.score,
                question_id=self.id
            ) for a in self.answers]
        )


class AnswerModel(db):
    __tablename__ = "Answer"
    id = Column(BigInteger, primary_key=True)
    title = Column(Text, unique=True, nullable=False)
    score = Column(Integer, nullable=False)

    question_id = Column(BigInteger, ForeignKey("Question.id", ondelete="CASCADE"))
    question = relationship("QuestionModel", back_populates="answers")

    game_answer = relationship("GameAnswersModel", back_populates="answer")
