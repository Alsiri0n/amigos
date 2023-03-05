from typing import TYPE_CHECKING, Optional
from datetime import datetime

from sqlalchemy import select, update, func, and_, or_
from sqlalchemy.orm import subqueryload
from sqlalchemy.engine import Result


from app.base.base_accessor import BaseAccessor
from app.game.models import (
    Game,
    Question,
    QuestionModel,
    Answer,
    AnswerModel,
    User,
    UserModel, GameModel, RoadmapModel, Roadmap, GameAnswersModel, StatisticModel,
)
if TYPE_CHECKING:
    from app.web.app import Application


class GameAccessor(BaseAccessor):
    def __init__(self, app: "Application"):
        self.app = app

    async def get_users_count_in_db(self) -> int:
        async with self.app.database.session() as session:
            async with session.begin():
                q = select(func.count(UserModel.id))
            result: Result = await session.execute(q)
        cnt_users = result.scalar()
        return cnt_users

    async def add_users(self, list_users: [UserModel]) -> None:
        async with self.app.database.session() as session:
            async with session.begin():
                for user in list_users:
                    session.add(user)
            await session.commit()

    async def get_user_by_vk_id(self, vk_id: int) -> User | None:
        user = None
        async with self.app.database.session() as session:
            async with session.begin():
                q = select(UserModel). \
                    where(UserModel.vk_id == vk_id). \
                    options(subqueryload(UserModel.statistic)). \
                    options(subqueryload(UserModel.game_answer))
            result: Result = await session.execute(q)
        user_model: UserModel = result.scalar()
        if user_model:
            user: User = user_model.to_dc()
        return user

    async def get_question_by_title(self, title: str) -> Question | None:
        question = None
        async with self.app.database.session() as session:
            async with session.begin():
                q = select(QuestionModel). \
                    where(QuestionModel.title == title). \
                    options(subqueryload(QuestionModel.answers))
            result: Result = await session.execute(q)
            question_model: QuestionModel = result.scalar()
        if question_model:
            question: Question = question_model.to_dc()
        return question

    async def get_question_by_id(self, id_: int) -> Question | None:
        question = None
        async with self.app.database.session() as session:
            async with session.begin():
                q = select(QuestionModel).\
                    where(QuestionModel.id == id_). \
                    options(subqueryload(QuestionModel.answers)). \
                    options(subqueryload(QuestionModel.road_map))
            result: Result = await session.execute(q)
            question_model: QuestionModel = result.scalar()
        if question_model:
            question: Question = question_model.to_dc()
        return question

    async def create_answers(self, question_id: int, answers: list[dict]) -> list[Answer]:
        async with self.app.database.session() as session:
            async with session.begin():
                q = select(AnswerModel).where(AnswerModel.question_id == question_id)
            result: Result = await session.execute(q)
            answer_model = result.scalar()
            if not answer_model:
                answer_model_list: [AnswerModel] = []
                for ans in answers:
                    answer_model_list.append(
                        AnswerModel(title=ans["title"],
                                    score=ans["score"],
                                    question_id=question_id))
                session.add_all(answer_model_list)
            await session.commit()
        return [answer.to_dc() for answer in answer_model_list]

    async def create_question(self, title: str, answers: list[dict]) -> Question:
        question_model: QuestionModel = QuestionModel(title=title)
        async with self.app.database.session() as session:
            async with session.begin():
                session.add(question_model)
                await session.flush()
                await session.refresh(question_model)
                await session.commit()
        # if not isinstance(answers[0], Answer):

        ans = await self.create_answers(question_id=question_model.id, answers=answers)
        question: Question = Question(answers=ans, id=question_model.id, title=title)
        return question

    async def create_game(self) -> Game:
        game_model: GameModel = GameModel(started_at=datetime.now())
        async with self.app.database.session() as session:
            async with session.begin():
                session.add(game_model)
                await session.commit()
                await self.create_roadmap(game_model)
                q = select(GameModel).\
                    where(GameModel.id == game_model.id). \
                    options(subqueryload(GameModel.statistic)). \
                    options(subqueryload(GameModel.road_map)). \
                    options(subqueryload(GameModel.game_answer))
            result: Result = await session.execute(q)
        game_model = result.scalar()
        game: Game = game_model.to_dc()
        return game

    # TODO создать gameanswer
    async def save_user_answer(self, game_id: int, user_id: int, answer_id: int, answer_score: int= 0):
        if answer_id > 0:
            game_answers_model: GameAnswersModel = GameAnswersModel(
                answer_id=answer_id, game_id=game_id, user_id=user_id
            )
            async with self.app.database.session() as session:
                async with session.begin():
                    session.add(game_answers_model)
                    q = select(StatisticModel). \
                        where(and_(StatisticModel.game_id == game_id,
                                   StatisticModel.user_id == user_id,
                                   StatisticModel.failures == 0)). \
                        options(subqueryload(StatisticModel.game)). \
                        options(subqueryload(StatisticModel.user))
                    await session.commit()
                result: Result = await session.execute(q)
            statistic_model: StatisticModel = result.scalar()
            if statistic_model:
                statistic_model.points = statistic_model.points + answer_score
            else:
                statistic_model: StatisticModel = StatisticModel(
                    points=answer_score, failures=0, game_id=game_id, user_id=user_id)
            await self._store_statistics(statistic_model)
        else:
            await self._store_statistics(StatisticModel(game_id=game_id, user_id=user_id, points=answer_score, failures=1))

    async def create_roadmap(self, cur_game: GameModel) -> None:
        list_questions: list[Question] = await self.list_questions(2)
        roadmap_model_list: [RoadmapModel] = []
        for question in list_questions:
            roadmap_model_list.append(
                RoadmapModel(
                    status=False,
                    game_id=cur_game.id,
                    question_id=question.id)
            )
        async with self.app.database.session() as session:
            async with session.begin():
                session.add_all(roadmap_model_list)
            await session.commit()

    async def close_roadmap_step(self, roadmap: Roadmap) -> None:
        async with self.app.database.session() as session:
            async with session.begin():
                q = update(RoadmapModel). \
                    where(and_(RoadmapModel.id == roadmap.id,
                               RoadmapModel.question_id == roadmap.question_id)). \
                    values(status=True)
            # result: Result = await session.execute(q)
            await session.execute(q)
            await session.commit()

    async def list_questions(self, number: int) -> list[Question]:
        async with self.app.database.session() as session:
            async with session.begin():
                q = select(QuestionModel). \
                    limit(number). \
                    options(subqueryload(QuestionModel.answers))
            result: Result = await session.execute(q)
        questions: [Question] = result.scalars()
        return questions

    async def end_game(self, game: Game = None) -> None:
        async with self.app.database.session() as session:
            async with session.begin():
                if game:
                    q = update(GameModel). \
                        where(GameModel.id == game.id). \
                        values(ended_at=datetime.now())
                else:
                    q = update(GameModel). \
                        where(GameModel.ended_at.is_(None)). \
                        values(ended_at=datetime.now())
                await session.execute(q)
                await session.commit()
        # Update возвращает только result.rowcount

    async def _store_statistics(self, statistic_model: StatisticModel):
        # self, game_id: int, user_id: int, points: int, failures: bool
        async with self.app.database.session() as session:
            async with session.begin():
                q = select(StatisticModel).where(and_(StatisticModel.game_id == statistic_model.game_id,
                                                      StatisticModel.user_id == statistic_model.user_id))
                result: Result = await session.execute(q)
                st_model: StatisticModel = result.scalar()
                if st_model:
                    q = update(StatisticModel). \
                        where(and_(StatisticModel.game_id == statistic_model.game_id,
                                   StatisticModel.user_id == statistic_model.user_id)). \
                        values(points=statistic_model.points, failures=statistic_model.failures)
                    await session.execute(q)
                else:
                    session.add(statistic_model)
            await session.commit()

    async def get_statistics(self, game_id: int) -> list((str, str, int)):
        async with self.app.database.session() as session:
            async with session.begin():
                q = select(StatisticModel). \
                    where(StatisticModel.game_id == game_id).\
                    options(subqueryload(StatisticModel.user))
                result: Result = await session.execute(q)
        statistics_model_list: [StatisticModel] = result.scalars()
        output = []
        for st_model in statistics_model_list:
            output.append((st_model.user.first_name, st_model.user.last_name, st_model.points))
        return output
