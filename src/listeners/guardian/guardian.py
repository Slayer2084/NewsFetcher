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
        article = Article(None, None, None)
        newest_time = datetime.datetime.utcnow().replace(tzinfo=pytz.timezone("GMT"))
        logger.info(f"Starting to listen to new guardian articles. From {newest_time}...")
        while True:
            try:
                result = await self.get_new_guardian(newest_time)
                if result is not None:
                    logger.info(f"Found new guardian article.")
                    newest_time, article = result
            except GuardianException:
                logger.exception("Exception occurred while trying to scrape Guardian")
            if not article.empty():
                logger.info(f"Calling callback with new guardian article.")
                self.callback(article)

    async def get_new_guardian(self, newest_time: datetime.datetime) -> Optional[Tuple[datetime.datetime, Article]]:
        now = datetime.datetime.now(pytz.timezone("GMT"))
        url = self._construct_url(newest_time, now)
        pages = await self._get_number_of_pages(url)
        logger.info(f"Number of pages: {pages}")
        articles = await self.__find_page_with_newest_article_after_time(url, newest_time, pages)
        logger.info("Got results from page containing the newest article.")
        return self._get_most_recent_article(articles, newest_time)

    @staticmethod
    async def _get_number_of_pages(url: str) -> int:
        data = (await request_guardian_api(url + "1")).json()["response"]
        return data["pages"]

    @staticmethod
    async def __find_page_with_newest_article_after_time(url: str,
                                                         newest_time: datetime.datetime,
                                                         n_pages: int) -> list:
        for page in range(1, n_pages + 1, 1):
            data = (await request_guardian_api(url + str(page))).json()["response"]
            t = ciso8601.parse_datetime(data["results"][-1]["webPublicationDate"])
            if t < newest_time:
                return data["results"][::-1]

    @staticmethod
    def _get_most_recent_article(articles: list,
                                 newest_time: datetime.datetime) -> Optional[Tuple[datetime.datetime, Article]]:
        for article in articles:
            t = ciso8601.parse_datetime(article["webPublicationDate"])
            if t > newest_time:
                url = article["webUrl"]
                return t, Article(url, t, "g")
        return None

    @staticmethod
    def _construct_url(from_time: datetime.datetime, to_time: datetime.datetime, page: int = None) -> str:
        if page is None:
            page = ""
        return f"https://content.guardianapis.com/world?api-key={config.GUARDIAN_API_KEY}" \
               f"&page-size=200" \
               f"&from-date={from_time.strftime('%Y-%m-%d')}" \
               f"&to-date={to_time.strftime('%Y-%m-%d')}&page={page}"


@sleep_and_retry
@limits(calls=10, period=60)
async def request_guardian_api(url: str) -> requests.Response:
    headers = get_header_with_random_user_agent()
    response = await get_async(url, headers=headers)
    if response.status_code != 200:
        logger.error(f"Guardian API returned status code {response.status_code}. Sleeping for 60 seconds.")
        raise RateLimitException("Rate limit exceeded.", 60)
    return response
