from google.cloud import pubsub_v1
import logging

from src.config import GCP_PROJECT

publisher = pubsub_v1.PublisherClient()


def publish_message(project_id: str, topic_id: str, msg: dict) -> None:
    """Publishes message to a Pub/Sub topic."""
    # [START pubsub_quickstart_publisher]
    # [START pubsub_publish]

    # The `topic_path` method creates a fully qualified identifier
    # in the form `projects/{project_id}/topics/{topic_id}`
    topic_path = publisher.topic_path(project_id, topic_id)

    data = "".encode("utf-8")
    # When you publish a message, the client returns a future.
    future = publisher.publish(topic_path, data, **msg)
    logging.debug(future.result())

    logging.info(f"Published messages to {topic_path}.")
    # [END pubsub_quickstart_publisher]
    # [END pubsub_publish]


def publish_event_new_news_article_url(article_id: int) -> None:
    publish_message(GCP_PROJECT, "news", {
        "type": "scraped_url",
        "article_id": article_id})
