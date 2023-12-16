import datetime
from typing import Optional


class Article:
    def __init__(self, url: Optional[str], time: Optional[datetime.datetime], origin: Optional[str]):
        self.url = url
        self.time = time
        self.origin = origin

    def empty(self) -> bool:
        return self.url is None and self.time is None and self.origin is None

    def __str__(self):
        return f"Article(url={self.url}, time={self.time}, origin={self.origin})"
