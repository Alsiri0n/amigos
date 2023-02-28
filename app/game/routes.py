import typing

if typing.TYPE_CHECKING:
    from app.web.app import Application


def setup_routes(app: "Application"):
    from app.game.views import QuestionAddView

    app.router.add_view("/game.add_question", QuestionAddView)
