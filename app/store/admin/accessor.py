import typing
from hashlib import sha256

from sqlalchemy import select

from app.admin.models import Admin, AdminModel
from app.base.base_accessor import BaseAccessor

if typing.TYPE_CHECKING:
    from app.web.app import Application


class AdminAccessor(BaseAccessor):
    async def connect(self, app: "Application"):
        self.app = app
        await self.create_admin(self.app.config.admin.email, self.app.config.admin.password)

    async def get_by_email(self, email: str) -> Admin | None:
        admin = None
        async with self.app.database.session() as session:
            async with session.begin():
                q = select(AdminModel).where(AdminModel.email == email)
            result = await session.execute(q)
            admin_model = result.scalar()
            if admin_model:
                admin = Admin(id=admin_model.id, email=admin_model.email, password=admin_model.password)
            return admin

    async def create_admin(self, email: str, password: str) -> Admin:
        adm = await self.get_by_email(email)
        if not adm:
            admin = AdminModel(email=email, password=sha256(password.encode()).hexdigest())
            async with self.app.database.session() as session:
                async with session.begin():
                    session.add(admin)
                await session.commit()
        adm = await self.get_by_email(email)
        return adm
