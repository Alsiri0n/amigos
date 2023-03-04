from typing import TYPE_CHECKING, Optional

import aiormq

from app.rabbit.rabbit_accessor import RabbitAccessor
from app.store.bot.dataclasses import Update
from app.store.bot.poller import Poller

if TYPE_CHECKING:
    from app.web.app import Application


class QueueAccessor(RabbitAccessor):
    def __init__(self, app: "Application", *args, **kwargs):
        super().__init__(app, *args, **kwargs)
        self.connection: Optional[aiormq.Connection] = None
        self.channel: Optional[aiormq.Channel] = None
        self.rabbit_queue = None
        self.poller: Poller = None
        self.consumer_tag: str = None

    async def connect(self, app: "Application") -> None:
        self.poller = Poller(app.store)
        self.logger.info("Start rabbitMQ")
        self.connection = self.app.rabbit.connection_consumer
        self.channel = await self.connection.channel()
        self.rabbit_queue = await self.channel.queue_declare("amigos")
        # self.consumer_tag = await self.channel.basic_consume(
        #     self.rabbit_queue.queue, self.on_message, no_ack=True)
        await self.poller.start()

    async def disconnect(self, app: "Application") -> None:
        print("store_bot_accessor_disconnect_started")
        if self.poller:
            await self.poller.stop()
        await self.channel.close()
        await self.connection.close()
        print("store_bot_accessor_disconnect_ended")

    # Если использовать коллбэк
    # async def on_message(self, message):
    #     if message:
    #         await self.app.store.bots_manager.handle_updates_rabbit(message)

    #TODO попробовать сделать поллер через basic_get а не basic_consume
    async def poll(self) -> Optional[Update]:
        raw_updates = await self.channel.basic_get(self.rabbit_queue.queue)

        if raw_updates.body:
            await self.channel.basic_ack(raw_updates.delivery_tag)
            return raw_updates
