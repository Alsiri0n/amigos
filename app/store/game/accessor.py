import random
from typing import TYPE_CHECKING, Optional, Set
from datetime import datetime

from sqlalchemy import select, update, func, and_, or_
from sqlalchemy.orm import subqueryload
from sqlalchemy.engine import Result


from app.base.base_accessor import BaseAccessor
from app.game.models import (
    Game, GameModel,
    Question, QuestionModel,
    Answer, AnswerModel,
    User, UserModel,
    Roadmap, RoadmapModel,
    GameAnswersModel, StatisticModel,
)
if TYPE_CHECKING:
    from app.web.app import Application


class GameAccessor(BaseAccessor):
    def __init__(self, app: "Application", *args, **kwargs):
        super().__init__(app, *args, **kwargs)

    async def get_users_count_in_db(self) -> Set[int]:
        async with self.app.database.session() as session:
            q = select(UserModel.vk_id)
            result: Result = await session.execute(q)
        user_ids = set(result.scalars().all())
        return user_ids

    async def add_users(self, list_users: list[UserModel]) -> None:
        async with self.app.database.session() as session:
            async with session.begin():
                session.add_all(list_users)
        # await session.commit()

    async def get_user_by_vk_id(self, vk_id: int) -> Optional[User]:
        async with self.app.database.session() as session:
            q = select(UserModel). \
                where(UserModel.vk_id == vk_id). \
                options(subqueryload(UserModel.statistic)). \
                options(subqueryload(UserModel.game_answer))
            result: Result = await session.execute(q)
        user_model: UserModel = result.scalar()
        if user_model:
            return user_model.to_dc()
        return None

    async def get_question_by_title(self, title: str) -> Optional[Question]:
        async with self.app.database.session() as session:
            q = select(QuestionModel). \
                where(QuestionModel.title == title). \
                options(subqueryload(QuestionModel.answers)). \
                options(subqueryload(QuestionModel.road_map))
            result: Result = await session.execute(q)
        question_model: QuestionModel = result.scalars().first()
        if question_model:
            return question_model.to_dc()
        return None

    async def get_question_by_id(self, id_: int) -> Optional[Question]:
        async with self.app.database.session() as session:
            q = select(QuestionModel).\
                where(QuestionModel.id == id_). \
                options(subqueryload(QuestionModel.answers)). \
                options(subqueryload(QuestionModel.road_map))
            result: Result = await session.execute(q)
        question_model: QuestionModel = result.scalar()
        if question_model:
            return question_model.to_dc()
        return None

    async def get_list_questions(self, number: int = 0) -> list[Question]:
        """
        Возвращает все вопросы
        :param number: Количество вопросов которые нужно вернуть
        :return:
        """
        async with self.app.database.session() as session:
            # q = select(QuestionModel). \
            #     limit(number). \
            #     options(subqueryload(QuestionModel.answers)). \
            #     options(subqueryload(QuestionModel.road_map))
            q = select(QuestionModel). \
                options(subqueryload(QuestionModel.answers)). \
                options(subqueryload(QuestionModel.road_map))
            result: Result = await session.execute(q)
        questions: list[Question] = [q.to_dc() for q in result.scalars().all()]
        return questions

    async def create_answers(self, question_id: int, answers: list[dict]) -> list[Answer]:
        async with self.app.database.session() as session:
            async with session.begin():
                q = select(AnswerModel).where(AnswerModel.question_id == question_id)
                result: Result = await session.execute(q)
                answer_model = result.scalar()
                if not answer_model:
                    answer_model_list: list[AnswerModel] = []
                    if isinstance(answers[0], Answer):
                        for ans in answers:
                            answer_model_list.append(
                                AnswerModel(title=ans.title,
                                            score=ans.score,
                                            question_id=question_id))
                    else:
                        for ans in answers:
                            answer_model_list.append(
                                AnswerModel(title=ans["title"],
                                            score=ans["score"],
                                            question_id=question_id))
                session.add_all(answer_model_list)
        return [answer.to_dc() for answer in answer_model_list]

    async def create_question(self, title: str, answers: list[dict]) -> Question:
        question_model: QuestionModel = QuestionModel(title=title)
        async with self.app.database.session() as session:
            async with session.begin():
                session.add(question_model)
                await session.flush()
                await session.refresh(question_model)
                await session.commit()
        ans = await self.create_answers(question_id=question_model.id, answers=answers)
        question: Question = Question(answers=ans, id=question_model.id, title=title)
        return question

    async def create_game(self, peer_id: int) -> Game:
        game_model: GameModel = GameModel(started_at=datetime.now(), peer_id=peer_id)
        async with self.app.database.session() as session:
            async with session.begin():
                session.add(game_model)
                await session.commit()
                await self.create_roadmap(game_model)
                q = select(GameModel).\
                    where(GameModel.id == game_model.id). \
                    where(GameModel.peer_id == peer_id). \
                    options(subqueryload(GameModel.statistic)). \
                    options(subqueryload(GameModel.road_map)). \
                    options(subqueryload(GameModel.game_answer))
            result: Result = await session.execute(q)
        game_model = result.scalar()
        game: Game = game_model.to_dc()
        return game

    async def create_roadmap(self, cur_game: GameModel) -> None:
        list_questions: list[Question] = await self.get_list_questions()
        roadmap_model_list: list[RoadmapModel] = []
        random.shuffle(list_questions)
        for question in list_questions[:4]:
            roadmap_model_list.append(
                RoadmapModel(
                    status=False,
                    game_id=cur_game.id,
                    question_id=question.id))
        async with self.app.database.session() as session:
            async with session.begin():
                session.add_all(roadmap_model_list)
        # await session.commit()

    async def finish_roadmap_step(self, roadmap: Roadmap) -> None:
        async with self.app.database.session() as session:
            async with session.begin():
                q = update(RoadmapModel). \
                    where(and_(RoadmapModel.id == roadmap.id,
                               RoadmapModel.question_id == roadmap.question_id)). \
                    values(status=True)
            await session.execute(q)
            await session.commit()

    async def end_game(self, peer_id: int, game: Game = None) -> int:
        async with self.app.database.session() as session:
            async with session.begin():
                if game:
                    # Update возвращает только result.rowcount
                    q = update(GameModel). \
                        where(GameModel.id == game.id). \
                        where(GameModel.peer_id == peer_id). \
                        values(ended_at=datetime.now())
                else:
                    q = select(GameModel). \
                        where(GameModel.peer_id == peer_id). \
                        where(GameModel.ended_at.is_(None))
                    result_game_ended: Result = await session.execute(q)
                    game_model: GameModel = result_game_ended.scalar()
                    q = update(GameModel). \
                        where(GameModel.ended_at.is_(None)). \
                        values(ended_at=datetime.now())
            await session.execute(q)
            await session.commit()
            if game:
                return game.id
            elif game_model:
                return game_model.id
            else:
                # Если был сбой и игра не создалась, но inline-кнопка всё равно горит красным
                return -1

    async def save_user_answer(self, game_id: int, user_id: int, answer_id: int, answer_score: int = 0) -> None:
        async with self.app.database.session() as session:
            async with session.begin():
                # Если ответ был правильный, записываем в таблицу game_answers
                if answer_id > 0:
                    game_answers_model: GameAnswersModel = GameAnswersModel(
                        answer_id=answer_id, game_id=game_id, user_id=user_id
                    )
                    session.add(game_answers_model)
                # Получаем статистику, для записи в таблицу statistic
            q = select(StatisticModel). \
                where(and_(StatisticModel.game_id == game_id,
                           StatisticModel.user_id == user_id)). \
                options(subqueryload(StatisticModel.game)). \
                options(subqueryload(StatisticModel.user))
            result: Result = await session.execute(q)
        statistic_model: StatisticModel = result.scalar()
        # Если уже есть статистика, то добавляем изменения в текущую статистику игры
        if statistic_model:
            if answer_id == -1:
                statistic_model.failures += 1
            else:
                statistic_model.points = statistic_model.points + answer_score
        # Если не было статистики, то создаём
        else:
            if answer_id == -1:
                statistic_model: StatisticModel = StatisticModel(
                    points=answer_score, failures=1, game_id=game_id, user_id=user_id)
            else:
                statistic_model: StatisticModel = StatisticModel(
                    points=answer_score, failures=0, game_id=game_id, user_id=user_id)
        await self._store_statistics(statistic_model)

    async def get_statistics(self, game_id: int) -> list[(str, str, int)]:
        async with self.app.database.session() as session:
            q = select(StatisticModel). \
                where(StatisticModel.game_id == game_id). \
                order_by(StatisticModel.points.desc()). \
                options(subqueryload(StatisticModel.user))
            result: Result = await session.execute(q)
            # await session.commit()
        statistics_model_list = result.scalars().all()
        output = []
        for st_model in statistics_model_list:
            output.append((st_model.user.first_name, st_model.user.last_name, st_model.points))
        return output

    async def get_user_failures(self, game_id: int, user_id: int) -> int:
        async with self.app.database.session() as session:
            q = select(StatisticModel). \
                where(and_(StatisticModel.game_id == game_id, StatisticModel.user_id == user_id))
            result: Result = await session.execute(q)
        statistics_model_list = result.scalar()
        return statistics_model_list.failures

    # Для проверки того, что игра не была запущена одновременно несколькими участниками
    async def is_current_game(self, peer_id: int) -> Optional[list[Game]]:
        async with self.app.database.session() as session:
            if peer_id == -1:
                q = select(GameModel). \
                    where(GameModel.ended_at.is_(None)). \
                    options(subqueryload(GameModel.statistic)). \
                    options(subqueryload(GameModel.road_map)). \
                    options(subqueryload(GameModel.game_answer))
            else:
                q = select(GameModel). \
                    where(and_(GameModel.peer_id == peer_id, GameModel.ended_at.is_(None))). \
                    options(subqueryload(GameModel.statistic)). \
                    options(subqueryload(GameModel.road_map)). \
                    options(subqueryload(GameModel.game_answer))
            result_game_ended: Result = await session.execute(q)
        game_model: GameModel = result_game_ended.scalars().all()
        if game_model:
            return [game.to_dc() for game in game_model]
        else:
            return False

    async def _store_statistics(self, statistic_model: StatisticModel):
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
                    await session.commit()
                else:
                    session.add(statistic_model)
            # await session.commit()
