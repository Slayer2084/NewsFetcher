import datetime
from typing import Callable, Coroutine, Optional, Any, Tuple
import logging
import pytz
import ciso8601
import requests
from ratelimit import limits, RateLimitException

from src.listeners.nyt.exceptions import NYTException
from src.article import Article
from src.listeners.helpers import get_header_with_random_user_agent, sleep_and_retry, get_async
import src.config as config

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def get_listener(callback: Callable[[Article], None], subsections: list, *args, **kwargs) -> Callable[[Any], Coroutine]:
    logger.info("Getting Listener.")
    nyt = NYT(callback, subsections, *args, **kwargs)
    return nyt.listen_to_nyt


class NYT:
    def __init__(self, callback: Callable[[Article], None], subsections: list, _=None):
        self.callback = callback
        self.subsections = subsections

    async def listen_to_nyt(self) -> None:
        article = None
        newest_time = datetime.datetime.utcnow().replace(tzinfo=pytz.timezone("GMT"))
        logger.info(f"Starting to listen to new NYT articles. From {newest_time}...")
        while True:
            try:
                result = await self.get_new_nyt(newest_time)
                if result is not None:
                    logger.info("Found new nyt article.")
                    newest_time, article = result
            except NYTException:
                logger.exception("Exception occurred while trying to scrape NYT")
            if not article.empty():
                logger.info("Calling callback with new nyt article.")
                self.callback(article)

    async def get_new_nyt(self, newest_time: datetime.datetime) -> Optional[Tuple[datetime.datetime, Article]]:
        is_recent = self._time_in_recent_range(newest_time)
        articles = await self._get_articles(is_recent, newest_time)
        logger.info("Got results from page containing the newest article.")
        return self._extract_most_recent_article(is_recent, articles, newest_time)

    @staticmethod
    def _time_in_recent_range(newest_time: datetime.datetime) -> bool:
        return (datetime.datetime.now(pytz.timezone("GMT")) - newest_time).total_seconds() <= 86400

    @staticmethod
    async def _get_articles(is_recent: bool, newest_time: datetime.datetime) -> list:
        if is_recent:
            url = f"https://api.nytimes.com/svc/news/v3/content/all/world.json?api-key={config.NYT_API_KEY}&limit=500"
            data = await request_nyt_api(url)
            json = data.json()
            results = json["results"]
        else:
            year = int(newest_time.strftime('%Y'))
            month = int(newest_time.strftime('%m'))
            url = f"https://api.nytimes.com/svc/archive/v1/{year}/{month}.json?api-key=" + config.NYT_API_KEY
            data = await request_nyt_api(url)
            json = data.json()
            results = json["response"]["docs"]
        return results

    def _extract_most_recent_article(self, is_recent: bool, articles: list,
                                     newest_time: datetime.datetime) -> Optional[Tuple[datetime.datetime, Article]]:
        t = 0
        i = 0
        if is_recent:
            for i in range(len(articles)):
                article = articles[i]
                subsection = article.get("subsection", None)
                if subsection not in self.subsections or subsection is None:
                    continue
                t = ciso8601.parse_datetime(article["published_date"])
                if t < newest_time:
                    break
            result_index = i + 1
            if result_index > len(articles):
                return None
            url = articles[result_index]["url"]
        else:
            for i in range(len(articles)):
                article = articles[i]
                subsection = article.get("subsection_name", None)
                if subsection not in self.subsections or subsection is None:
                    continue
                t = ciso8601.parse_datetime(article["pub_date"])
                if t > newest_time:
                    break
            result_index = i + 1
            if result_index > len(articles):
                return None
            url = articles[result_index]["web_url"]
        return t, Article(url, t, "n")


@sleep_and_retry
@limits(calls=5, period=60)
async def request_nyt_api(url: str) -> requests.Response:
    headers = get_header_with_random_user_agent()
    response = await get_async(url, headers=headers)
    if response.status_code != 200:
        logger.error(f"NYT API returned status code {response.status_code}. Sleeping for 60 seconds.")
        raise RateLimitException("Rate limit exceeded.", 60)
    return response
