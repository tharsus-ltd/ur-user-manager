import os
import aioredis

from aio_pika import connect_robust, Message, ExchangeType

from app.singleton import Singleton

REDIS_SERVICE = os.environ.get("REDIS_SERVICE", "user_man_db")


class Handlers(metaclass=Singleton):

    async def init(self):
        self.redis = aioredis.from_url(f"redis://{REDIS_SERVICE}", encoding="utf-8", decode_responses=True)
        self.rabbitmq = await connect_robust("amqp://guest:guest@rabbitmq/")
        self.channel = await self.rabbitmq.channel()
        self.exchange = await self.channel.declare_exchange("micro-rockets", ExchangeType.TOPIC, durable=True)

    async def send_msg(self, msg: str, topic: str):
        await self.exchange.publish(
            Message(body=msg.encode()),
            routing_key=topic,
        )
