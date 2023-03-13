import datetime
from dataclasses import dataclass, field
from typing import Optional

from sqlalchemy import BigInteger, Boolean, Column, ForeignKey, Text, Integer, DateTime
from sqlalchemy.orm import relationship

from app.store.database.sqlalchemy_base import db


@dataclass
class Game:
    id: int
    peer_id: int
    started_at: datetime.datetime
    ended_at: datetime.datetime

    road_map: list["Roadmap"] = field(default_factory=list)
    statistic: list["Statistic"] = field(default_factory=list)
    game_answer: list["GameAnswer"] = field(default_factory=list)


@dataclass
class User:
    id: int
    vk_id: int
    first_name: str
    last_name: str

    statistic: list["Statistic"] = field(default_factory=list)
    game_answer: list["GameAnswer"] = field(default_factory=list)


@dataclass
class Statistic:
    id: int
    game_id: int
    user_id: int
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
class Question:
    id: int
    title: str

    answers: list["Answer"] = field(default_factory=list)
    road_map: list["Roadmap"] = field(default_factory=list)


@dataclass
class Answer:
    id: int
    title: str
    score: int
    question_id: int

    game_answer: list["GameAnswer"] = field(default_factory=list)


@dataclass
class GameEntity:
    game: Game
    status: str | None = None
    current_question: Question | None = None
    past_user_answers: set = field(default_factory=set)
    game_over_users: list = field(default_factory=list)
    answered_questions: list[int] = field(default_factory=list)


class GameModel(db):
    __tablename__ = "games"
    id = Column(BigInteger, primary_key=True, nullable=False)
    peer_id = Column(BigInteger, nullable=False)
    started_at = Column(DateTime)
    ended_at = Column(DateTime, nullable=True)

    statistic = relationship("StatisticModel", back_populates="game", cascade="all, delete")
    road_map = relationship("RoadmapModel", back_populates="game", cascade="all, delete")
    game_answer = relationship("GameAnswersModel", back_populates="game", cascade="all, delete")

    def to_dc(self):
        return Game(
            id=self.id,
            peer_id=self.peer_id,
            started_at=self.started_at,
            ended_at=self.ended_at,

            statistic=[s.to_dc() for s in self.statistic],
            road_map=[rm.to_dc() for rm in self.road_map],
            game_answer=[ga.to_dc() for ga in self.game_answer]
        )


class UserModel(db):
    __tablename__ = "users"
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

            statistic=[st.to_dc() for st in self.statistic],
            game_answer=[ga.to_dc() for ga in self.game_answer],
        )


class StatisticModel(db):
    __tablename__ = "statistics"
    id = Column(BigInteger, primary_key=True, nullable=False)
    points = Column(BigInteger, nullable=False, default=0)
    failures = Column(BigInteger, default=0)

    game_id = Column(BigInteger, ForeignKey("games.id", ondelete="CASCADE"))
    game = relationship("GameModel", back_populates="statistic")

    user_id = Column(BigInteger, ForeignKey("users.id"))
    user = relationship("UserModel", back_populates="statistic")

    def to_dc(self):
        return Statistic(
            id=self.id,
            points=self.points,
            failures=self.failures,
            game_id=self.game_id,
            user_id=self.user_id,
        )


class RoadmapModel(db):
    __tablename__ = "road_maps"
    id = Column(BigInteger, primary_key=True, nullable=False)
    status = Column(Boolean, nullable=False, default=False)

    game_id = Column(BigInteger, ForeignKey("games.id", ondelete="CASCADE"))
    game = relationship("GameModel", back_populates="road_map")

    question_id = Column(BigInteger, ForeignKey("questions.id"))
    question = relationship("QuestionModel", back_populates="road_map")

    def to_dc(self):
        return Roadmap(
            id=self.id,
            status=self.status,
            game_id=self.game_id,
            question_id=self.question_id,
        )


class GameAnswersModel(db):
    __tablename__ = "game_answers"
    id = Column(BigInteger, primary_key=True, nullable=False)

    answer_id = Column(BigInteger, ForeignKey("answers.id"))
    answer = relationship("AnswerModel", back_populates="game_answer")

    game_id = Column(BigInteger, ForeignKey("games.id", ondelete="CASCADE"))
    game = relationship("GameModel", back_populates="game_answer")

    user_id = Column(BigInteger, ForeignKey("users.id"))
    user = relationship("UserModel", back_populates="game_answer")

    def to_dc(self):
        return GameAnswer(
            id=self.id,
            answer_id=self.answer_id,
            game_id=self.game_id,
            user_id=self.user_id,
        )


class QuestionModel(db):
    __tablename__ = "questions"
    id = Column(BigInteger, primary_key=True, nullable=False)
    title = Column(Text, nullable=False, unique=True)

    answers = relationship("AnswerModel", back_populates="question", cascade="all, delete")
    road_map = relationship("RoadmapModel", back_populates="question")

    def to_dc(self):
        return Question(
            id=self.id,
            title=self.title,
            answers=[a.to_dc() for a in self.answers],
            road_map=[rm.to_dc() for rm in self.road_map],
        )


class AnswerModel(db):
    __tablename__ = "answers"
    id = Column(BigInteger, primary_key=True)
    title = Column(Text, nullable=False)
    score = Column(Integer, nullable=False)

    question_id = Column(BigInteger, ForeignKey("questions.id", ondelete="CASCADE"))
    question = relationship("QuestionModel", back_populates="answers")

    game_answer = relationship("GameAnswersModel", back_populates="answer")

    def to_dc(self):
        return Answer(
            id=self.id,
            title=self.title,
            score=self.score,
            question_id=self.question_id,
        )
