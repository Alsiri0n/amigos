from aiohttp.web_exceptions import HTTPConflict, HTTPBadRequest

from aiohttp_apispec import request_schema, response_schema
from app.game.schemes import QuestionSchema, AnswerSchema
from app.web.app import View
from app.web.mixins import AuthRequiredMixin
from app.web.utils import json_response


# class ThemeAddView(AuthRequiredMixin, View):
#     @request_schema(ThemeSchema)
#     @response_schema(ThemeSchema, 200)
#     async def post(self):
#         title = self.data["title"]
#         if await self.store.games.get_theme_by_title(title):
#             raise HTTPConflict
#         theme = await self.store.games.create_theme(title=title)
#         return json_response(data=ThemeSchema().dump(theme))


class QuestionAddView(AuthRequiredMixin, View):
    @request_schema(QuestionSchema)
    @response_schema(QuestionSchema, 200)
    async def post(self):
        title, answers = self.data["title"], self.data["answers"]
        if len(answers) != 6:
            raise HTTPBadRequest
        if await self.store.games.get_question_by_title(title):
            raise HTTPConflict
        question = await self.store.games.create_question(title, answers)
        return json_response(data=QuestionSchema().dump(question))
