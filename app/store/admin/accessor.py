import typing
from hashlib import sha256

from sqlalchemy import select

from app.admin.models import Admin, AdminModel
from app.base.base_accessor import BaseAccessor

if typing.TYPE_CHECKING:
    from app.web.app import Application


class AdminAccessor(BaseAccessor):
    # async def connect(self, app: "Application"):
    #     self.app = app
    #     await self.create_admin(self.app.config.admin.email,
    #                             self.app.config.admin.password,
    #                             self.app.config.admin.vk_id)

    async def get_by_email(self, email: str) -> Admin | None:
        admin = None
        async with self.app.database.session() as session:
            async with session.begin():
                q = select(AdminModel).where(AdminModel.email == email)
            result = await session.execute(q)
            admin_model = result.scalars().first()
            if admin_model:
                admin = admin_model.to_dc()
            return admin

    async def create_admin(self, email: str, password: str, vk_id: int) -> Admin:
        admin = await self.get_by_email(email)
        if not admin:
            admin_model = AdminModel(email=email,
                                     password=sha256(password.encode()).hexdigest(),
                                     vk_id=vk_id,)
            async with self.app.database.session() as session:
                async with session.begin():
                    session.add(admin_model)
                await session.commit()
            admin = admin_model.to_dc()
        return admin
