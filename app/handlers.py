import os
import aioredis

from app.singleton import Singleton

REDIS_SERVICE = os.environ.get("REDIS_SERVICE", "user_man_db")


class Handlers(metaclass=Singleton):

    async def init(self):
        self.redis = aioredis.from_url(f"redis://{REDIS_SERVICE}", encoding="utf-8", decode_responses=True)
