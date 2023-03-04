from typing import TYPE_CHECKING, Optional

import aiormq


if TYPE_CHECKING:
    from app.web.app import Application


class Rabbit:
    def __init__(self, app: "Application"):
        self.app = app
        self.connection_producer: Optional[aiormq.Connection] = None
        self.connection_consumer: Optional[aiormq.Connection] = None
        self.channel_producer: Optional[aiormq.Channel] = None
        self.channel_consumer: Optional[aiormq.Channel] = None
        self.rabbit_queue_producer: Optional[aiormq.spec.Queue] = None
        self.rabbit_queue_consumer: Optional[aiormq.spec.Queue] = None
        self.consume_ok = None

    async def connect(self, *_: list, **__: dict) -> None:
        rabbit_url = aiormq.abc.URL.build(
            scheme="amqp",
            user=self.app.config.rabbit.user,
            password=self.app.config.rabbit.password,
            host=self.app.config.rabbit.host,
            port=self.app.config.rabbit.port,
            path=self.app.config.rabbit.path,
        )
        # print(rabbit_url)
        self.connection_producer = await aiormq.connect(rabbit_url)
        self.connection_consumer = await aiormq.connect(rabbit_url)
        # self.channel_producer = await self.connection_producer.channel()
        # self.channel_consumer = await self.connection_consumer.channel()
        # self.rabbit_queue_producer = await self.channel_producer.queue_declare('amigos')
        # self.rabbit_queue_consumer = await self.channel_consumer.queue_declare('amigos')
        # self.consume_ok = await self._channel.basic_consume(
        #     self._declare_ok.queue, self.on_message, np_ack=True)

    # async def on_message(self, message):
    #     print(f"RECEIVED NEW MESSAGE {message!r}")

    async def disconnect(self, *_: list, **__: dict) -> None:
        # if self.connection:
        #     await self.connection.close()
        pass