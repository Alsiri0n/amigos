import asyncio
import json
from asyncio import Task, Future
from typing import Optional

import aio_pika

from app.store import Store


class Poller:
    def __init__(self, store: Store):
        self.store = store
        self.is_running = False
        self.poll_task: Optional[Task] = None
        # self.rabbit_connection: Optional[aio_pika.Connection] = None
        # self.rabbit_channel: Optional[aio_pika.Channel] = None

        # self.queue = asyncio.Queue()

    async def start(self):
        self.poll_task = asyncio.create_task(self.poll())
        self.is_running = True
        self.poll_task.add_done_callback(self._done_callback)

    def _done_callback(self, future: Future):
        if future.exception():
            self.store.vk_api.logger.exception('polling failed', exc_info=future.exception())

    async def stop(self):
        # print("vk_api_poller_stop_started")
        self.is_running = False
        if self.poll_task:
            await self.poll_task
        # print("vk_api_poller_stop_ended")

    async def poll(self):
        while self.is_running:
            updates = await self.store.vk_api.poll()
            if updates:
                await self.store.rabbit.rabbit_produce(updates)
