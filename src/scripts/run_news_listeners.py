from src.listeners.news_listener import NewsListener
from src.listeners.cnbc.cnbc import get_listener as cnbc_listener
from src.listeners.guardian.guardian import get_listener as guardian_listener
from src.listeners.nyt.nyt import get_listener as nyt_listener


def main():
    def print_(article):
        print(article.origin, article.time, article.url)

    nyt_subsections_to_include = ["Politics", "Europe", "Asia Pacific", "Middle East", "Africa", "Australia",
                                  "Americas",
                                  "Canada"]

    news_listener = NewsListener()
    news_listener.add_listener(cnbc_listener(print_))
    # news_listener.add_listener(guardian_listener(print_))
    # news_listener.add_listener(nyt_listener(print_, nyt_subsections_to_include))
    news_listener.start_listeners()


if __name__ == "__main__":
    import logging
    logger = logging.getLogger("src.listeners.cnbc.cnbc")
    logger.setLevel(logging.INFO)
    logger.addHandler(logging.StreamHandler())
    main()
