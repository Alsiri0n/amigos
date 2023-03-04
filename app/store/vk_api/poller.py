import asyncio
import json
from asyncio import Task, Future
from typing import Optional

import aiormq

from app.store import Store


class Poller:
    def __init__(self, store: Store):
        self.store = store
        self.is_running = False
        #self.is_round_timer = False
        self.poll_task: Optional[Task] = None
        # self.round_timer_task: Optional[Task] = None
        # self.queue = asyncio.Queue()

    async def start(self):
        self.poll_task = asyncio.create_task(self.poll())
        self.is_running = True
        self.poll_task.add_done_callback(self._done_callback)

    def _done_callback(self, future: Future):
        if future.exception():
            self.store.vk_api.logger.exception('polling failed', exc_info=future.exception())

    async def stop(self):
        print("vk_api_poller_stop_started")
        self.is_running = False
        if self.poll_task:
            await self.poll_task
        print("vk_api_poller_stop_ended")
        # if self.round_timer_task:
        #     await self.round_timer_task

    async def poll(self):
        # counter_2 = 100
        while self.is_running:
            updates = await self.store.vk_api.poll()
            # print(counter_2)
            # counter_2 += 1
            if updates:
                # await self.store.bots_manager.handle_updates(updates)
                # channel: aiormq.Channel = self.store.vk_api.channel
                # declare_ok = await channel.queue_declare("amigos")
                # await channel.basic_publish(bytes(json.dumps(updates), "utf-8"))
                await self.store.vk_api.channel.basic_publish(bytes(json.dumps(updates), "utf-8"), routing_key='amigos')
                # await channel.close()
                #


    # async def round_timer(self, timeout: int):
    #     self.is_round_timer = True
    #     self.round_timer_task = asyncio.create_task(self._waiting_round_task(timeout))
    #     self.round_timer_task.add_done_callback(self._done_callback)
    #     await asyncio.sleep(timeout)
    #     await self.stop_round_timer()
    #
    # async def _waiting_round_task(self, timeout: int):
    #     count = 0
    #     # while count < timeout:
    #     while self.is_round_timer:
    #         await asyncio.sleep(1)
    #         print(count)
    #         count += 1
    #     print(f'{timeout} background task finished')
    #
    # async def stop_round_timer(self):
    #     self.is_round_timer = False
    #     if self.round_timer_task:
    #         await self.round_timer_task
