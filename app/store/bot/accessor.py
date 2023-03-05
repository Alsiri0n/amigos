import asyncio
from typing import TYPE_CHECKING, Optional

import aiormq
from aiormq.abc import DeliveredMessage

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
        self.rabbit_queue: Optional[aiormq.spec.Queue] = None
        self.poller: Poller = None
        self.consumer_tag: str = None

    async def connect(self, app: "Application") -> None:
        self.poller = Poller(app.store)
        self.logger.info("Start rabbitMQ")
        self.connection = self.app.rabbit.connection_consumer
        self.channel = await self.connection.channel()
        self.rabbit_queue = await self.channel.queue_declare("amigos")
        self.consumer_tag = await self.channel.basic_consume(
            self.rabbit_queue.queue, self.on_message, no_ack=True)
        # await self.poller.start()

    async def disconnect(self, app: "Application") -> None:
        print("app_store_bot_accessor(RABBIT_CONSUMER)_disconnect_started")
        if self.poller:
            await self.poller.stop()
        print("app_store_bot_accessor(RABBIT_CONSUMER)_disconnect_poller_stopped")
        # await asyncio.Future()
        # await asyncio.sleep(5)
        # consumer_tag self.channel.consumers.keys()
        # queue name self.rabbit_queue.queue
        # await self.channel.queue_unbind()
        # await self.rabbit_queue.cancel(self.consumer_tag)
        print("app_store_bot_accessor(RABBIT_CONSUMER)_disconnect_queue_cancel")
        # await self.connection.closing()
        # await self.channel.closing()
        # await self.channel.basic_cancel(self.channel.consumers.keys())
        # await self.rabbit_queue.Unbind()
        print("app_store_bot_accessor(RABBIT_CONSUMER)_disconnect_queue_close")
        await self.channel.close()
        await self.connection.close()
        # await self.channel.basic_cancel(self.consumer_tag, nowait=True)
        print("app_store_bot_accessor(RABBIT_CONSUMER)_disconnect_channel_basic_cancel")
        # await self.channel.close(0)
        # await self.connection.closing()
        print("app_store_bot_accessor(RABBIT_CONSUMER)_disconnect_ended")

    # Если использовать коллбэк
    async def on_message(self, message):
        if message:
            await self.app.store.bots_manager.handle_updates_rabbit(message)

    #TODO попробовать сделать поллер через basic_get а не basic_consume
    async def poll(self) -> Optional[DeliveredMessage]:
        raw_updates = await self.channel.basic_get(self.rabbit_queue.queue)

        if raw_updates.body:
            await self.channel.basic_ack(raw_updates.delivery_tag)
            return raw_updates
