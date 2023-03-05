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
            self.store.bots_manager.logger.exception('polling failed', exc_info=future.exception())

    async def stop(self):
        print("app_store_bot_poller(RABBIT_CONSUMER)_stop_started")
        self.is_running = False
        if self.poll_task:
            await self.poll_task
            # await asyncio.wait([self.poll_task], timeout=2)
        print("app_store_bot_poller(RABBIT_CONSUMER)_stop_ended")

    async def rabbit_poll(self):
        # pass
        while self.is_running:
            updates = await self.store.rabbit.poll()
            if updates:
                await self.store.bots_manager.handle_updates_rabbit(updates)
