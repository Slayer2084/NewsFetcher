import asyncio
import datetime
from typing import Callable, Coroutine, Optional, Any, Tuple
import logging
import pytz
import ciso8601
import requests
from ratelimit import limits, RateLimitException

from src.listeners.guardian.exceptions import GuardianException
from src.article import Article
from src.listeners.helpers import get_header_with_random_user_agent, sleep_and_retry, get_async
import src.config as config

logger = logging.getLogger(__name__)
logger.setLevel(config.LOGGING_LEVEL)


def get_listener(callback: Callable[[Article], None], *args, **kwargs) -> Callable[[Any], Coroutine]:
    guardian = Guardian(callback, *args, **kwargs)
    return guardian.listen_to_guardian


class Guardian:
    def __init__(self, callback: Callable[[Article], None], _=None):
        self.callback = callback

    async def listen_to_guardian(self) -> None:
        article = None
        newest_time = datetime.datetime.utcnow().replace(tzinfo=pytz.timezone("GMT"))
        while True:
            try:
                result = await self.get_new_guardian(newest_time)
                if result is not None:
                    newest_time, article = result
            except GuardianException:
                logger.exception("Exception occurred while trying to scrape Guardian")
            if not article.empty():
                self.callback(article)
            await asyncio.sleep(5)

    @staticmethod
    async def get_new_guardian(newest_time: datetime.datetime) -> Optional[Tuple[datetime.datetime, Article]]:
        now = datetime.datetime.now(pytz.timezone("GMT"))
        api_key = config.GUARDIAN_API_KEY
        url = f"https://content.guardianapis.com/world?api-key={api_key}" \
              f"&page-size=200" \
              f"&from-date={newest_time.strftime('%Y-%m-%d')}" \
              f"&to-date={now.strftime('%Y-%m-%d')}&page="
        data = (await request_guardian_api(url + "1")).json()["response"]
        pages = data["pages"]
        for page in range(1, pages + 1, 1):
            data = (await request_guardian_api(url + str(page))).json()["response"]
            t = ciso8601.parse_datetime(data["results"][-1]["webPublicationDate"])
            if t < newest_time:
                break
        articles = data["results"]

        articles.reverse()

        for article in articles:
            t = ciso8601.parse_datetime(article["webPublicationDate"])
            if t > newest_time:
                url = article["webUrl"]
                return t, Article(url, t, "g")


@sleep_and_retry
@limits(calls=10, period=60)
async def request_guardian_api(url: str) -> requests.Response:
    headers = get_header_with_random_user_agent()
    response = await get_async(url, headers=headers)
    if response.status_code != 200:
        logger.error(f"Guardian API returned status code {response.status_code}. Sleeping for 60 seconds.")
        raise RateLimitException("Rate limit exceeded.", 60)
    return response
