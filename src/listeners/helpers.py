import random
import decorator
import asyncio
import logging
from ratelimit import RateLimitException
from httpx import AsyncClient
import requests

from src.listeners.user_agents import user_agents
import src.config as config

logger = logging.getLogger(__name__)
logger.setLevel(config.LOGGING_LEVEL)


def get_random_user_agent() -> str:
    return random.choice(user_agents)


def get_header_with_random_user_agent() -> dict:
    return {"User-Agent": get_random_user_agent()}


@decorator.decorator
async def sleep_and_retry(func, *args, **kwargs):
    while True:
        try:
            return await func(*args, **kwargs)
        except RateLimitException as exception:
            logger.debug(f"Rate limit exceeded. Sleeping for {exception.period_remaining} seconds.")
            await asyncio.sleep(exception.period_remaining)
            logger.debug("Done sleeping. Executing request.")


async def get_async(url: str, **kwargs) -> requests.Response:
    async with AsyncClient() as client:
        response = await client.get(url, **kwargs)
        return response

if __name__ == "__main__":
    get_random_user_agent()
