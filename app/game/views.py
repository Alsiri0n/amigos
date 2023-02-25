from aiohttp.web_exceptions import HTTPConflict

from aiohttp_apispec import request_schema, response_schema
from app.game.schemes import ThemeSchema
from app.web.app import View
from app.web.mixins import AuthRequiredMixin
from app.web.utils import json_response


class ThemeAddView(AuthRequiredMixin, View):
    @request_schema(ThemeSchema)
    @response_schema(ThemeSchema, 200)
    async def post(self):
        title = self.data["title"]
        if await self.store.games.get_theme_by_title(title):
            raise HTTPConflict
        theme = await self.store.games.create_theme(title=title)
        return json_response(data=ThemeSchema().dump(theme))
