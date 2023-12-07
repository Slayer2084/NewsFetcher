import datetime
from typing import Optional


class Article:
    def __init__(self, url: Optional[str], time: Optional[datetime.datetime], origin: Optional[str]):
        self.url = url
        self.time = time
        self.origin = origin

    def empty(self) -> bool:
        return self.url is None and self.time is None and self.origin is None
