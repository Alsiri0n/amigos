from sqlalchemy import select, and_, update
from sqlalchemy.orm import subqueryload
from sqlalchemy.engine import Result

from app.base.base_accessor import BaseAccessor
from app.game.models import (
    Game,
    # GameModel,
    # GameStatus,
    # GameStatusModel,
    # GameResult,
    # GameResultModel,
    Question,
    QuestionModel,
    Answer,
    AnswerModel,
)


class GameAccessor(BaseAccessor):
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
                                          answers=[Answer(title=i.title, points=i.points)
                                                   for i in question_model.answers])
        return question

    async def create_answers(self, question_id: int, answers: [Answer]) -> list[Answer]:
        async with self.app.database.session() as session:
            async with session.begin():
                q = select(AnswerModel).where(AnswerModel.question_id == question_id)
            result: Result = await session.execute(q)
            answer_model = result.scalar()
            if not answer_model:
                for ans in answers:
                    answer_model = AnswerModel(title=ans.title, points=ans.points, question_id=question_id)
                    session.add(answer_model)
                await session.commit()
        return answers

    async def create_question(self, title: str, answers: list) -> Question:
        answer_list: [Answer] = []
        if not isinstance(answers[0], Answer):
            for ans in answers:
                answer_list.append(Answer(title=ans["title"], points=ans["points"]))
        question_model: QuestionModel = QuestionModel(title=title)
        # answer_list: list[Answer] = answers
        async with self.app.database.session() as session:
            async with session.begin():
                session.add(question_model)
                await session.flush()
                await session.refresh(question_model)
                q_id = question_model.id
                await session.commit()

        ans = await self.create_answers(question_id=q_id, answers=answer_list)
        question: Question = Question(answers=ans, id=q_id, title=title)
        return question

    async def get_question(self, game_id: int) -> Question:
        pass
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

    async def create_game(self, user_id: int) -> Game:
        pass
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

    async def user_answer(self, game_id: int, status_id: int, answer: str):
        pass
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
