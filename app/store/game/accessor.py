
from sqlalchemy import select
from app.base.base_accessor import BaseAccessor
from app.game.models import (
    Theme,
    ThemeModel
)

class GameAccessor(BaseAccessor):
    async def create_theme(self, title: str) -> Theme:
        theme_model = ThemeModel(title=str(title))
        async with self.app.database.session() as session:
            async with session.begin():
                session.add(theme_model)
            await session.commit()
        theme = await self.get_theme_by_title(title)
        return theme

    async def get_theme_by_title(self, title: str) -> Theme | None:
        theme = None
        async with self.app.database.session() as session:
            async with session.begin():
                q = select(ThemeModel).wheere(ThemeModel.title == title)
            result = await session.execute(q)
            theme_model: ThemeModel = result.scalars().first()
            if theme_model:
                theme = Theme(id=theme_model.id, title=theme_model.title)
            await session.rollback()
        return theme
