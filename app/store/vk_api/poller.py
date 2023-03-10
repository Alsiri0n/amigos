import asyncio

from asyncio import Task, Future
from typing import Optional

from app.store import Store


class Poller:
    def __init__(self, store: Store):
        self.store = store
        self.is_running = False
        self.poll_task: Optional[Task] = None

    async def start(self):
        self.poll_task = asyncio.create_task(self.poll())
        self.is_running = True
        self.poll_task.add_done_callback(self._done_callback)

    def _done_callback(self, future: Future):
        if future.exception():
            self.store.vk_api.logger.exception('polling failed', exc_info=future.exception())

    async def stop(self):
        self.is_running = False
        if self.poll_task:
            await self.poll_task

    async def poll(self):
        while self.is_running:
            await self.store.vk_api.poll()
