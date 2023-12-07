import asyncio
from typing import Any, Callable, Coroutine


class NewsListener:
    def __init__(self):
        self.loop = asyncio.get_event_loop()
        asyncio.set_event_loop(self.loop)
        self.tasks = []

    def add_listener(self, listener: Callable[[Any], Coroutine], *args, **kwargs) -> None:
        self.tasks.append(listener(*args, **kwargs))

    def start_listeners(self) -> None:
        future_tasks = asyncio.gather(*self.tasks)
        self.loop.run_until_complete(future_tasks)
