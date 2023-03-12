import pytest
from sqlalchemy.ext.asyncio import AsyncSession

import app.store.game.accessor
from app.game.models import (
    Answer,
    AnswerModel,
    Question,
    QuestionModel,
)


@pytest.fixture
def answers(store) -> list[Answer]:
    return [
        Answer(id=1, title="11", score=11, question_id=1),
        Answer(id=2, title="12", score=12, question_id=1),
        Answer(id=3, title="13", score=13, question_id=1),
        Answer(id=4, title="14", score=14, question_id=1),
        Answer(id=5, title="15", score=15, question_id=1),
        Answer(id=6, title="16", score=16, question_id=1),
        Answer(id=7, title="21", score=21, question_id=2),
        Answer(id=8, title="22", score=22, question_id=2),
        Answer(id=9, title="23", score=23, question_id=2),
        Answer(id=10, title="24", score=24, question_id=2),
        Answer(id=11, title="25", score=25, question_id=2),
        Answer(id=12, title="26", score=26, question_id=2),
    ]


@pytest.fixture
async def question_1(db_session) -> Question:
    title = "how are you?"
    async with db_session.begin() as session:

        question = QuestionModel(
            title=title,
        )
        session.add(question)

    async with db_session.begin() as session:
        answers = [
            AnswerModel(
                title="well",
                score=1,
                question_id=question.id,
            ),
            AnswerModel(
                title="not well",
                score=2,
                question_id=question.id,
            ),
            AnswerModel(
                title="very well",
                score=3,
                question_id=question.id,
            ),
            AnswerModel(
                title="bad",
                score=4,
                question_id=question.id,
            ),
            AnswerModel(
                title="so bad",
                score=5,
                question_id=question.id,
            ),
            AnswerModel(
                title="good",
                score=6,
                question_id=question.id,
            ),
        ]
        session.add_all(answers)
    question: Question = Question(answers=answers, id=question.id, title=question.title)

    return Question(
        id=question.id,
        title=title,
        answers=[
            Answer(
                id=a.id,
                title=a.title,
                score=a.score,
                question_id=question.id,
            )
            for a in question.answers
        ],
    )


@pytest.fixture
async def question_2(db_session) -> Question:
    title = "are you doing fine?"
    async with db_session.begin() as session:

        question = QuestionModel(
            title=title,
        )
        session.add(question)
    async with db_session.begin() as session:
        answers = [
            AnswerModel(
                title="nice",
                score=1,
                question_id=question.id,
            ),
            AnswerModel(
                title="okay",
                score=2,
                question_id=question.id,
            ),
            AnswerModel(
                title="nop",
                score=3,
                question_id=question.id,
            ),
            AnswerModel(
                title="fine",
                score=4,
                question_id=question.id,
            ),
            AnswerModel(
                title="so bad",
                score=5,
                question_id=question.id,
            ),
            AnswerModel(
                title="good",
                score=6,
                question_id=question.id,
            ),
        ]
        session.add_all(answers)
    question: Question = Question(answers=answers, id=question.id, title=question.title)
    return Question(
        id=question.id,
        title=title,
        answers=[
            Answer(
                id=a.id,
                title=a.title,
                score=a.score,
                question_id=question.id,
            )
            for a in question.answers
        ],
    )
