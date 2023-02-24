from typing import Optional

from aiohttp.web import (
    Application as AiohttpApplication,
    Request as AiohttpRequest,
)

from app.admin.models import Admin
from app.web.config import Config, setup_config
from app.web.middlewares import setup_middleware


class Application(AiohttpApplication):
    config: Optional[Config] = None

class Request(AiohttpRequest):
    admin: Optional[Admin] = None

    @property
    def app(self) -> Application:
        return super().app()


app = Application()

def setup_app(config_path: str) -> Application:
    setup_config(app=app, config_path=config_path)
    setup_middleware(app=app)

    return app
