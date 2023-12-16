import datetime
from typing import Callable, Coroutine, Optional, Any, Tuple
import logging
import pytz
import ciso8601
import requests
from ratelimit import limits, RateLimitException

from src.listeners.cnbc.exceptions import CNBCException
from src.article import Article
from src.listeners.helpers import get_header_with_random_user_agent, sleep_and_retry, get_async
import src.config as config

logger = logging.getLogger(__name__)
logger.setLevel(config.LOGGING_LEVEL)


def get_listener(callback: Callable[[Article], None], *args, **kwargs) -> Callable[[Any], Coroutine]:
    logger.info("Getting Listener.")
    cnbc = CNBC(callback, *args, **kwargs)
    return cnbc.listen_to_cnbc


class CNBC:
    def __init__(self, callback: Callable[[Article], None], _=None):
        self.callback = callback
        self.base_url = ("https://api.queryly.com/cnbc/json.aspx"
                         "?queryly_key=31a35d40a9a64ab3&query=Politics&endindex={}&batchsize=100&sort=date")

    async def listen_to_cnbc(self) -> None:
        article = Article(None, None, None)
        newest_time = datetime.datetime.utcnow().replace(tzinfo=pytz.timezone("GMT"))
        logger.info(f"Starting to listen to new CNBC articles. From {newest_time}...")
        while True:
            try:
                result = await self.get_new_cnbc(newest_time)
                if result is not None:
                    logger.info(f"Found new cnbc article.")
                    newest_time, article = result
            except CNBCException:
                logger.exception("Exception occurred while trying to scrape CNBC")
            if not article.empty():
                logger.info(f"Calling callback with new cnbc article.")
                self.callback(article)

    async def get_new_cnbc(self, newest_time: datetime.datetime) -> Optional[Tuple[datetime.datetime, Article]]:
        n_pages = await self._get_number_of_pages()
        logger.info(f"Number of pages: {n_pages}")
        results = await self._find_page_with_newest_article_after_time(newest_time, n_pages)
        logger.info("Got results from page containing the newest article.")
        return self._get_most_recent_article(results, newest_time)

    async def _get_number_of_pages(self) -> int:
        json = (await request_cnbc_api(self.base_url.format(0))).json()
        return json["metadata"]["totalpage"]

    async def _find_page_with_newest_article_after_time(self, newest_time: datetime.datetime, n_pages: int) -> list:
        results = []
        for page in range(0, n_pages, 1):
            to_request_url = self.base_url.format(page * 100)
            json = (await request_cnbc_api(to_request_url)).json()
            results = json["results"]
            if results:
                t = datetime.datetime.fromtimestamp(results[-1]["pubdateunix"], tz=pytz.timezone("GMT"))
                if t < newest_time:
                    break
        results = results[::-1]
        return results

    @staticmethod
    def _check_if_article_valid(result: dict) -> bool:
        premium = False
        if "cn:contentClassification" in result:
            clasf = result["cn:contentClassification"]
            if "premium" in clasf:
                premium = True
        if not premium:
            if result["cn:branding"] == "cnbc":
                if result["cn:type"] not in ["cnbcvideo", "live_story"]:
                    return True
        return False

    def _get_most_recent_article(self, articles: list,
                                 newest_time: datetime.datetime) -> Optional[Tuple[datetime.datetime, Article]]:
        for result in articles:
            t = ciso8601.parse_datetime(result["datePublished"])
            if newest_time < t:
                if self._check_if_article_valid(result):
                    article = Article(url=result["url"], time=t, origin="c")
                    return t, article


@sleep_and_retry
@limits(calls=120, period=60)
async def request_cnbc_api(url: str) -> requests.Response:
    headers = get_header_with_random_user_agent()
    response = await get_async(url, headers=headers)
    if response.status_code != 200:
        logger.error(f"CNBC API returned status code {response.status_code}. Sleeping for 60 seconds.")
        raise RateLimitException("Rate limit exceeded.", 60)
    return response

if __name__ == "__main__":
    result = {
        "cn:contentClassification": "",
        "cn:branding": "cnbc",
        "cn:type": "article"
    }
    import asyncio
    print(asyncio.run(CNBC._check_if_article_valid(result)))
