from app.game.models import Answer, Question


def question2dict(question: Question):
    return {
        "id": int(question.id),
        "title": str(question.title),
        "answers": [answer2dict(answer) for answer in question.answers],
    }


def answer2dict(answer: Answer):
    return {
        "id": answer.id,
        "title": answer.title,
        "score": answer.score,
        "question_id": answer.question_id,
    }
