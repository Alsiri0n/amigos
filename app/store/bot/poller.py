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
        self.is_running = True
        self.poll_task = asyncio.create_task(self.rabbit_poll())
        self.poll_task.add_done_callback(self._done_callback)

    def _done_callback(self, future: Future):
        if future.exception():
            self.store.vk_api.logger.exception('polling failed', exc_info=future.exception())

    async def stop(self):
        print("bot_poller_stop_started")
        self.is_running = False
        # await self.poll_task.cancel()
        if self.poll_task:
            await self.poll_task
        print("bot_poller_stop_ended")

    async def rabbit_poll(self):
        # pass
        while self.is_running:
            updates = await self.store.rabbit.poll()
            if updates:
                await self.store.bots_manager.handle_updates_rabbit(updates)
