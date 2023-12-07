import asyncio
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
    nyt = NYT(callback, subsections, *args, **kwargs)
    return nyt.listen_to_nyt


class NYT:
    def __init__(self, callback: Callable[[Article], None], subsections: list, _=None):
        self.callback = callback
        self.subsections = subsections

    async def listen_to_nyt(self) -> None:
        article = None
        newest_time = datetime.datetime.utcnow().replace(tzinfo=pytz.timezone("GMT"))
        while True:
            try:
                result = await self.get_new_nyt(newest_time)
                if result is not None:
                    newest_time, article = result
            except NYTException:
                logger.exception("Exception occurred while trying to scrape NYT")
            if not article.empty():
                self.callback(article)
            await asyncio.sleep(5)

    async def get_new_nyt(self, newest_time: datetime.datetime) -> Optional[Tuple[datetime.datetime, Article]]:
        t = 0
        if (datetime.datetime.now(pytz.timezone("GMT")) - newest_time).total_seconds() <= 86400:
            data = (await request_nyt_api(f"https://api.nytimes.com/svc/news/v3/content/all/world.json?"
                                          f"api-key={config.NYT_API_KEY}&limit=500"))
            json = data.json()
            results = json["results"]
            i = 0
            for i in range(len(results)):
                subsection = results[i]["subsection"]
                if subsection not in self.subsections:
                    continue
                t = ciso8601.parse_datetime(results[i]["published_date"])
                if t < newest_time:
                    break
            result_index = i + 1
            if result_index > len(results):
                return None
            url = results[result_index]["url"]
        else:
            year = int(newest_time.strftime('%Y'))
            month = int(newest_time.strftime('%m'))
            url = f"https://api.nytimes.com/svc/archive/v1/{year}/{month}.json?api-key=" + config.NYT_API_KEY
            data = (await request_nyt_api(url))
            json = data.json()
            results = json["response"]["docs"]
            i = 0
            for i in range(len(results)):
                subsection = results[i].get("subsection_name", None)
                if subsection not in self.subsections or subsection is None:
                    continue
                t = ciso8601.parse_datetime(results[i]["pub_date"])
                if t > newest_time:
                    break
            result_index = i + 1
            if result_index > len(results):
                return None
            url = results[result_index]["web_url"]

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
