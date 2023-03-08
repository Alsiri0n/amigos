from typing import Optional, TYPE_CHECKING

from sqlalchemy import URL
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.store.database import db

if TYPE_CHECKING:
    from app.web.app import Application


class Database:
    def __init__(self, app: "Application"):
        self.app = app
        self._engine: Optional[AsyncEngine] = None
        self._db: Optional[declarative_base] = None
        self.session: Optional[sessionmaker] = None

    async def connect(self, *_: list, **__: dict) -> None:
        self._db = db
        database_url = URL.create(
            drivername="postgresql+asyncpg",
            username=self.app.config.database.user,
            password=self.app.config.database.password,
            host=self.app.config.database.host,
            port=self.app.config.database.port,
            database=self.app.config.database.name,
        )
        self._engine = create_async_engine(database_url, echo=True)
        self.session = sessionmaker(self._engine, class_=AsyncSession, expire_on_commit=False)

    async def disconnect(self, *_: list, **__: dict) -> None:
        if self._engine:
            await self._engine.dispose()
