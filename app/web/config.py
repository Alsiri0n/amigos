import typing
import os
from dataclasses import dataclass
from dotenv import load_dotenv
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
    # timeout: int


@dataclass
class DatabaseConfig:
    host: str = "localhost"
    port: int = 5432
    user: str = "postgres"
    password: str = "postgres"
    name: str = "amigos"


@dataclass
class RabbitConfig:
    host: str = "localhost"
    port: int = 5672
    user: str = "guest"
    password: str = "guest"
    vhost: str = "amigos"
    queue: str = "amigos"


@dataclass
class Config:
    admin: AdminConfig
    session: SessionConfig = None
    bot: BotConfig = None
    database: DatabaseConfig = None
    rabbit: RabbitConfig = None


def setup_config(app: "Application", config_path: str):
    load_dotenv(config_path)
    app.config = Config(
        session=SessionConfig(
            key=os.getenv("SESSION_KEY")
        ),
        admin=AdminConfig(
            email=os.getenv("ADMIN_EMAIL"),
            password=os.getenv("ADMIN_PASSWORD"),
            vk_id=int(os.getenv("ADMIN_VK_ID")),
        ),
        bot=BotConfig(
            token=os.getenv("BOT_TOKEN"),
            group_id=int(os.getenv("BOT_GROUP_ID")),
        ),
        database=DatabaseConfig(
            host=os.getenv("DATABASE_HOST"),
            port=int(os.getenv("DATABASE_PORT")),
            user=os.getenv("DATABASE_USER"),
            password=os.getenv("DATABASE_PASSWORD"),
            name=os.getenv("DATABASE_NAME"),
        ),
        rabbit=RabbitConfig(
            host=os.getenv("RABBIT_HOST"),
            port=int(os.getenv("RABBIT_PORT")),
            user=os.getenv("RABBIT_USER"),
            password=os.getenv("RABBIT_PASSWORD"),
            vhost=os.getenv("RABBIT_VHOST"),
            queue=os.getenv("RABBIT_QUEUE"),
        )
    )
