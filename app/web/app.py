from typing import Optional

from aiohttp.web import (
    Application as AiohttpApplication,
    Request as AiohttpRequest,
    View as AiohttpView,
)

from app.admin.models import Admin
from app.web.config import Config, setup_config
from app.web.middlewares import setup_middleware
from app.web.routes import setup_routes
from app.store.database.database import Database
from app.store import Store


class Application(AiohttpApplication):
    config: Optional[Config] = None
    database: Optional[Database] = None
    store: Optional[Store]

class Request(AiohttpRequest):
    admin: Optional[Admin] = None

    @property
    def app(self) -> Application:
        return super().app()


class View(AiohttpView):
    @property
    def request(self) -> Request:
        return super().request
    
    @property
    def database(self):
        return self.request.app.database
    
    @property
    def store(self):
        return self.request.app.store
    
    @property
    def data(self):
        return self.request.get("data", {})


app = Application()

def setup_app(config_path: str) -> Application:
    setup_config(app=app, config_path=config_path)
    setup_routes(app=app)
    setup_middleware(app=app)

    return app
