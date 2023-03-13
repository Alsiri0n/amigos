import pytest
from sqlalchemy import delete
from sqlalchemy.exc import IntegrityError
from sqlalchemy.future import select

from app.game.models import Answer, AnswerModel, Question, QuestionModel
from app.store import Store
from tests.game import question2dict
from tests.utils import check_empty_table_exists
from tests.utils import ok_response


class TestQuestionsStore:
    async def test_table_exists(self, cli):
        await check_empty_table_exists(cli, "questions")
        await check_empty_table_exists(cli, "answers")

    async def test_create_question(
        self, cli, store: Store, answers: list[Answer]
    ):
        question_title = "title"
        question = await store.games.create_question(
            question_title, answers
        )
        assert type(question) is Question

        async with cli.app.database.session() as session:
            res = await session.execute(select(QuestionModel))
            questions = res.scalars().all()

            res = await session.execute(select(AnswerModel))
            db_answers = res.scalars().all()

        assert len(questions) == 1
        db_question = questions[0]

        assert db_question.title == question_title

        assert len(db_answers) == len(answers)
        for have, expected in zip(db_answers, answers):
            assert have.title == expected.title
            assert have.score == expected.score

    async def test_create_question_unique_title_constraint(
        self, cli, store: Store, question_1: Question, answers: list[Answer]
    ):
        with pytest.raises(IntegrityError) as exc_info:
            await store.games.create_question(
                question_1.title, answers
            )
        assert exc_info.value.orig.pgcode == "23505"

    async def test_get_question_by_title(self, cli, store: Store, question_1: Question):
        assert question_1 == await store.games.get_question_by_title(question_1.title)

    async def test_list_questions(
        self, cli, store: Store, question_1: Question, question_2: Question
    ):
        questions = await store.games.get_list_questions()
        assert questions == [question_1, question_2]

    async def test_check_cascade_delete(self, cli, question_1: Question):
        async with cli.app.database.session() as session:
            await session.execute(
                delete(QuestionModel).where(QuestionModel.id == question_1.id)
            )
            await session.commit()

            res = await session.execute(
                select(AnswerModel).where(AnswerModel.question_id == question_1.id)
            )
            db_answers = res.scalars().all()

        assert len(db_answers) == 0


class TestQuestionAddView:
    async def test_success(self, authed_cli):
        resp = await authed_cli.post(
            "/game.add_question",
            json={
                "title": "How many legs does an octopus have?",
                "answers": [
                    {
                        "title": "2",
                        "score": 1,
                    },
                    {
                        "title": "8",
                        "score": 10,
                    },
                    {
                        "title": "7",
                        "score": 2,
                    },
                    {
                        "title": "6",
                        "score": 3,
                    },
                    {
                        "title": "5",
                        "score": 4,
                    },
                    {
                        "title": "4",
                        "score": 5,
                    },
                ],
            },
        )
        assert resp.status == 200
        data = await resp.json()
        assert data == ok_response(
            data=question2dict(
                Question(
                    id=data["data"]["id"],
                    title="How many legs does an octopus have?",
                    answers=[
                        Answer(title="2", score=1, id=data["data"]["answers"][0]["id"], question_id=data["data"]["id"]),
                        Answer(title="8", score=10, id=data["data"]["answers"][1]["id"], question_id=data["data"]["id"]),
                        Answer(title="7", score=2, id=data["data"]["answers"][2]["id"], question_id=data["data"]["id"]),
                        Answer(title="6", score=3, id=data["data"]["answers"][3]["id"], question_id=data["data"]["id"]),
                        Answer(title="5", score=4, id=data["data"]["answers"][4]["id"], question_id=data["data"]["id"]),
                        Answer(title="4", score=5, id=data["data"]["answers"][5]["id"], question_id=data["data"]["id"]),
                    ],
                )
            )
        )

    async def test_unauthorized(self, cli):
        resp = await cli.post(
            "/game.add_question",
            json={
                "title": "How many legs does an octopus have?",
                "answers": [
                    {
                        "title": "2",
                        "score": 1,
                    },
                    {
                        "title": "8",
                        "score": 10,
                    },
                    {
                        "title": "7",
                        "score": 2,
                    },
                    {
                        "title": "6",
                        "score": 3,
                    },
                    {
                        "title": "5",
                        "score": 4,
                    },
                    {
                        "title": "4",
                        "score": 5,
                    },
                ],
            },
        )
        assert resp.status == 401
        data = await resp.json()
        assert data["status"] == "unauthorized"

    async def test_only_one_answer(self, authed_cli):
        resp = await authed_cli.post(
            "/game.add_question",
            json={
                "title": "How many legs does an octopus have?",
                "answers": [
                    {
                        "title": "2",
                        "score": 1,
                    },
                ],
            },
        )
        assert resp.status == 400
        data = await resp.json()
        assert data["status"] == "bad_request"
