import typing
import random
from datetime import datetime

from sqlalchemy import select, update, func
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
    UserModel, GameModel, RoadMapModel,
)
if typing.TYPE_CHECKING:
    from app.web.app import Application


class GameAccessor(BaseAccessor):
    def __init__(self, app: "Application"):
        self.app = app
        self.current_game_id: int = -1

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
                q = select(UserModel).\
                    where(UserModel.vk_id == vk_id)
            result: Result = await session.execute(q)
            user_model: UserModel = result.scalar()
        if user_model:
            user: User = user_model.to_dc()
        return user

    async def get_question_by_title(self, title: str) -> Question | None:
        question = None
        async with self.app.database.session() as session:
            async with session.begin():
                q = select(QuestionModel).\
                    where(QuestionModel.title == title).\
                    options(subqueryload(QuestionModel.answers))
            result: Result = await session.execute(q)
            question_model: QuestionModel = result.scalar()
        if question_model:
            question: Question = Question(id=question_model.id,
                                          title=question_model.title,
                                          answers=[Answer(title=i.title, score=i.score)
                                                   for i in question_model.answers])
        return question

    async def create_answers(self, question_id: int, answers: [AnswerModel]) -> list[Answer]:
        async with self.app.database.session() as session:
            async with session.begin():
                q = select(AnswerModel).where(AnswerModel.question_id == question_id)
            result: Result = await session.execute(q)
            answer_model = result.scalar()
            if not answer_model:
                for ans in answers:
                    session.add(ans)
            await session.commit()
        return answers

    async def create_question(self, title: str, answers: list) -> Question:
        question_model: QuestionModel = QuestionModel(title=title)
        async with self.app.database.session() as session:
            async with session.begin():
                session.add(question_model)
                await session.flush()
                await session.refresh(question_model)
                await session.commit()
        if not isinstance(answers[0], Answer):
            answer_model_list: [AnswerModel] = []
            for ans in answers:
                answer_model_list.append(
                    AnswerModel(title=ans["title"],
                                score=ans["score"],
                                question_id=question_model.id))
        ans = await self.create_answers(question_id=question_model.id, answers=answer_model_list)
        question: Question = Question(answers=ans, id=question_model.id, title=title)
        return question

    async def create_game(self) -> None:
        game_model: GameModel = GameModel(started_at=datetime.now())
        async with self.app.database.session() as session:
            async with session.begin():
                session.add(game_model)
            await session.commit()
        # print(game_model)
        self.current_game_id = game_model.id
        # TODO создать roadmap
        await self.create_roadmap(game_model)
        # TODO создать gameanswer

    async def create_roadmap(self, cur_game: GameModel) -> None:
        list_questions_id: list[int] = await self.list_questions(1)
        async with self.app.database.session() as session:
            async with session.begin():
                for question in list_questions_id:
                    roadmap_model: RoadMapModel = RoadMapModel(
                        status=False,
                        game_id=cur_game.id,
                        question_id=question
                    )
                    session.add(roadmap_model)
            await session.commit()

    async def list_questions(self, number: int) -> list[int]:

        async with self.app.database.session() as session:
            async with session.begin():
                q = select(QuestionModel).\
                    options(subqueryload(QuestionModel.answers))
            result: Result = await session.execute(q)
        questions: [Question] = result.scalars()
        output: list[int] = []
        for q in questions:
            output.append(q.id)
        return output

    async def end_game(self) -> None:
        async with self.app.database.session() as session:
            async with session.begin():
                q = update(GameModel).\
                    where(GameModel.ended_at.is_(None)).\
                    values(ended_at=datetime.now())
                await session.execute(q)
        # Update возвращает только result.rowcount
        self.current_game_id = -1
        # TODO записать статистику по игре



    # async def get_question(self, game_id: int) -> Question:
    #     pass
        # async with self.app.database.session() as session:
        #     async with session.begin():
        #         q = select(QuestionModel).\
        #             where(QuestionModel.id == 5).\
        #             options(subqueryload(QuestionModel.answers))
        #     result: Result = await session.execute(q)
        #     question_model: QuestionModel = result.scalar()
        # question = Question(id=question_model.id,
        #                     title=question_model.title,
        #                     answers=question_model.answers)
        # return question

    # async def get_last_status(self, user_id: int) -> GameStatus | None:
    #     pass
        # async with self.app.database.session() as session:
        #     async with session.begin():`
        #         q = select(GameResultModel).\
        #             where(and_(GameResultModel.user_id == user_id,
        #                        GameResultModel.game_status_id != 8)).\
        #             order_by(GameResultModel.game_id).\
        #             options(subqueryload(GameResultModel.game_status))
        #         result: Result = await session.execute(q)
        #         game_result_model: GameResultModel = result.scalar()
        #         if game_result_model:
        #             game_status: GameStatus = GameStatus(id=game_result_model.game_status_id,
        #                                                  title=game_result_model.game_status.title,
        #                                                  game_result=GameResult(id=game_result_model.id,
        #                                                                         user_id=game_result_model.user_id,
        #                                                                         result=game_result_model.result,
        #                                                                         game_id=game_result_model.game_id,
        #                                                                         game_status_id=game_result_model.game_status_id,
        #                                                                         question_id=game_result_model.question_id
        #                                                                         )
        #                                                  )
        #             return game_status
        # return None

    # async def create_game(self, user_id: int) -> Game:
    #     pass
        # game_model: GameModel = GameModel(creator_id=user_id)
        # async with self.app.database.session() as session:
        #     async with session.begin():
        #         session.add(game_model)
        #         await session.flush()
        #         await session.refresh(game_model)
        #         game_id = game_model.id
        #         game_result: GameResultModel = GameResultModel(user_id=user_id,
        #                                                        result=0,
        #                                                        game_id=game_id,
        #                                                        game_status_id=3
        #                                                        )
        #         session.add(game_result)
        #     await session.commit()
        # game: Game = Game(creator_id=user_id, id=game_id)
        # return game

    # async def end_game(self, game_id: int) -> [GameResult]:
    #     pass
    #     self.set_status(game_id=game_id, status=8)
    #     async with self.app.database.session() as session:
    #         async with session.begin():
    #             q = select(GameResultModel).\
    #                 where(GameResultModel.game_id == game_id)
    #         result: Result = await session.execute(q)
    #     game_result_models: [GameResultModel] = result.scalars().all()
    #
    #     game_result: [GameResult] = []
    #     for gr in game_result_models:
    #         game_result.append(GameResult(
    #             id=gr.id,
    #             user_id=gr.user_id,
    #             result=gr.result,
    #             game_id=gr.game_id,
    #             game_status_id=gr.game_status_id,
    #             question_id=None)
    #         )
    #     return game_result
    #
    # async def start_game(self, user_id):
    #     pass
    #
    # async def set_status(self, game_id: int, status: int) -> None:
    #     async with self.app.database.session() as session:
    #         async with session.begin():
    #             q = update(GameResultModel). \
    #                 where(GameResultModel.game_id == game_id). \
    #                 values(game_status_id=status)
    #             await session.execute(q)

    # async def user_answer(self, game_id: int, status_id: int, answer: str):
    #     pass
    # async def create_theme(self, title: str) -> Theme:
    #     theme_model = ThemeModel(title=str(title))
    #     async with self.app.database.session() as session:
    #         async with session.begin():
    #             session.add(theme_model)
    #         await session.commit()
    #     theme = await self.get_theme_by_title(title)
    #     return theme

    # async def get_theme_by_title(self, title: str) -> Theme | None:
    #     theme = None
    #     async with self.app.database.session() as session:
    #         async with session.begin():
    #             q = select(ThemeModel).where(ThemeModel.title == title)
    #         result = await session.execute(q)
    #         theme_model: ThemeModel = result.scalars().first()
    #         if theme_model:
    #             theme = Theme(id=theme_model.id, title=theme_model.title)
    #         await session.rollback()
    #     return theme
