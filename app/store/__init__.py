import typing


from app.store.database.database import Database
from app.store.game.accessor import GameAccessor
from app.store.rabbit.rabbit import Rabbit

if typing.TYPE_CHECKING:
    from app.web.app import Application


class Store:
    def __init__(self, app: "Application"):
        from app.store.admin.accessor import AdminAccessor
        from app.store.bot.manager import BotManager
        from app.store.vk_api.accessor import VkApiAccessor
        from app.store.bot.accessor import QueueAccessor

        self.games = GameAccessor(app)
        self.admins = AdminAccessor(app)
        self.vk_api = VkApiAccessor(app)
        self.bots_manager = BotManager(app)
        self.rabbit = QueueAccessor(app)


def setup_store(app: "Application"):
    app.database = Database(app)
    app.on_startup.append(app.database.connect)
    app.on_cleanup.append(app.database.disconnect)
    app.on_startup.append(app.rabbit.connect)
    app.on_cleanup.append(app.rabbit.disconnect)

    app.store = Store(app)
    app.rabbit = Rabbit(app)
