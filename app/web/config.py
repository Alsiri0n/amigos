import typing
from dataclasses import dataclass

import yaml

if typing.TYPE_CHECKING:
    from app.web.app import Application


@dataclass
class SessionConfig:
    key: str


@dataclass
class AdminConfig:
    email: str
    password: str
    vk_id: int


@dataclass
class BotConfig:
    token: str
    group_id: int
    timeout: int


@dataclass
class DatabaseConfig:
    host: str = "localhost"
    port: int = 5432
    user: str = "postgres"
    password: str = "postgres"
    database: str = "amigos"


@dataclass
class RabbitConfig:
    host: str = "localhost"
    port: int = 5672
    user: str = "guest"
    password: str = "guest"
    path: str = "amigos"
    queue: str = "amigos"


@dataclass
class Config:
    admin: AdminConfig
    session: SessionConfig = None
    bot: BotConfig = None
    database: DatabaseConfig = None
    rabbit: RabbitConfig = None


def setup_config(app: "Application", config_path: str):
    with open(config_path, "r") as f:
        raw_config = yaml.safe_load(f)
    
    app.config = Config(
        session=SessionConfig(
            key=raw_config["session"]["key"],
        ),
        admin=AdminConfig(
            email=raw_config["admin"]["email"],
            password=raw_config["admin"]["password"],
            vk_id=raw_config["admin"]["vk_id"],
        ),
        bot=BotConfig(
            token=raw_config["bot"]["token"],
            group_id=raw_config["bot"]["group_id"],
            timeout=raw_config["bot"]["timeout"],
        ),
        database=DatabaseConfig(**raw_config["database"]),
        rabbit=RabbitConfig(
            host=raw_config["rabbit"]["host"],
            port=raw_config["rabbit"]["port"],
            user=raw_config["rabbit"]["user"],
            password=raw_config["rabbit"]["password"],
            path=raw_config["rabbit"]["path"],
            queue=raw_config["rabbit"]["queue"]
        )
    )
