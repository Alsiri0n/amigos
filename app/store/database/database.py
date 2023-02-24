from typing import TYPE_CHECKING, Optional

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
        self.session: Optional[AsyncSession] = None

    async def connect(self, *_: list, **__: dict) -> None:
        self._db = db
        database_url = f"postgresql+asyncpg"
        self._engine = create_async_engine(database_url, echo=True, future=True)
        self.session = sessionmaker(self._engine, class_=AsyncEngine, expire_on_commit=False)

    async def disconnect(self, *_: list, **__: dict) -> None:
        if self._engine:
            await self._engine.dispose()