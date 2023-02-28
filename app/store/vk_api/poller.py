import asyncio
from asyncio import Task
from typing import Optional

from app.store import Store


class Poller:
    def __init__(self, store: Store):
        self.store = store
        self.is_running = False
        self.poll_task: Optional[Task] = None
        self.queue = asyncio.Queue()

    async def start(self):
        self.is_running = True
        self.poll_task = asyncio.create_task(self.poll())

    async def stop(self):
        self.is_running = False
        await self.queue.join()
        self.poll_task.cancel()
        await self.poll_task

    async def poll(self):
        while self.is_running:
            updates = await self.store.vk_api.poll()
            if updates:
                await self.store.bots_manager.handle_updates(updates)