from src.listeners.news_listener import NewsListener
from src.listeners.cnbc.cnbc import get_listener as cnbc_listener
from src.listeners.guardian.guardian import get_listener as guardian_listener
from src.listeners.nyt.nyt import get_listener as nyt_listener
from src.scripts.gcloud_message_broker import publish_event_new_news_article_url
from src.scripts.database import DataBase


def main():
    db = DataBase()

    def callback(article):
        article_id = db.add_article(article)
        publish_event_new_news_article_url(article_id)

    nyt_subsections_to_include = ["Politics", "Europe", "Asia Pacific", "Middle East", "Africa", "Australia",
                                  "Americas",
                                  "Canada"]

    news_listener = NewsListener()
    news_listener.add_listener(cnbc_listener(callback))
    news_listener.add_listener(guardian_listener(callback))
    # news_listener.add_listener(nyt_listener(print_, nyt_subsections_to_include))
    news_listener.start_listeners()


if __name__ == "__main__":
    main()
