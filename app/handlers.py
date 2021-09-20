import os
import aioredis

from aio_pika import connect_robust, Message

from app.singleton import Singleton

REDIS_SERVICE = os.environ.get("REDIS_SERVICE","user_man_db")


class Handlers(metaclass=Singleton):

    async def init(self):
        self.redis = aioredis.from_url(f"redis://{REDIS_SERVICE}", encoding="utf-8", decode_responses=True)
        self.rabbitmq = await connect_robust("amqp://guest:guest@rabbitmq/")
        self.channel = await self.rabbitmq.channel()

    async def send_msg(self, msg: str, topic: str):
        await self.channel.default_exchange.publish(
            Message(body=msg.encode()),
            routing_key=topic,
        )