from typing import Optional

from aiohttp.web import Application as AiohttpApplication


from app.web.config import Config, setup_config


class Application(AiohttpApplication):
    config: Optional[Config] = None




app = Application()

def setup_app(config_path: str) -> Application:
    setup_config(app, config_path)

    return app
