import typing


from app.store.database.database import Database
from app.store.queue.queue import Queue


if typing.TYPE_CHECKING:
    from app.web.app import Application


class Store:
    def __init__(self, app: "Application"):
        from app.store.admin.accessor import AdminAccessor
        from app.store.game.accessor import GameAccessor
        from app.store.vk_api.accessor import VkApiAccessor
        from app.store.rabbit.accessor import RabbitAccessor
        from app.store.bot.manager import BotManager

        self.games = GameAccessor(app)
        self.admins = AdminAccessor(app)
        self.rabbit = RabbitAccessor(app)
        self.vk_api = VkApiAccessor(app)
        self.bots_manager = BotManager(app)


def setup_store(app: "Application"):
    app.database = Database(app)
    app.on_startup.append(app.database.connect)
    app.on_cleanup.append(app.database.disconnect)
    app.queue = Queue(app)
    app.on_startup.append(app.queue.connect)
    app.on_cleanup.append(app.queue.disconnect)

    app.store = Store(app)







