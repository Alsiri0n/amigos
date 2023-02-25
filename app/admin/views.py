from aiohttp.web_exceptions import HTTPForbidden, HTTPUnauthorized
from aiohttp_apispec import request_schema, response_schema
from aiohttp_session import new_session

from app.admin.schemes import AdminSchema
from app.web.app import View
from app.web.utils import json_response


class AdminLoginView(View):
    @request_schema(AdminSchema)
    @response_schema(AdminSchema, 200)
    async def post(self):
        data = self.request["data"]
        admin = await self.request.app.store.admins.get_by_email(data["email"])
        if not admin or admin.is_password_valid(admin.password):
            raise HTTPForbidden
        session = new_session(request=self.request)
        session["admin"] = AdminSchema().dump(admin)
        return json_response(data=AdminSchema().dump(admin))


class AdminCurrentView(View):
    @response_schema(AdminSchema, 200)
    async def get(self):
        try:
            admin = self.request.admin
            return json_response(data=AdminSchema().dump(admin))
        except AttributeError as e:
            raise HTTPUnauthorized
