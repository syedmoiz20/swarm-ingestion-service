import os
from dataclasses import dataclass
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    google_cloud_project: str
    pubsub_topic: str
    pubsub_subscription: str
    bigquery_dataset: str
    bigquery_table: str

    @property
    def topic_path(self) -> str:
        return f"projects/{self.google_cloud_project}/topics/{self.pubsub_topic}"

    @property
    def subscription_path(self) -> str:
        return (
            f"projects/{self.google_cloud_project}/subscriptions/{self.pubsub_subscription}"
        )

    @property
    def bigquery_table_id(self) -> str:
        return (
            f"{self.google_cloud_project}.{self.bigquery_dataset}.{self.bigquery_table}"
        )


@lru_cache
def get_settings() -> Settings:
    google_cloud_project = os.getenv("GOOGLE_CLOUD_PROJECT")
    if not google_cloud_project:
        raise RuntimeError("GOOGLE_CLOUD_PROJECT is not set.")

    return Settings(
        google_cloud_project=google_cloud_project,
        pubsub_topic=os.getenv("PUBSUB_TOPIC", "analytics-events"),
        pubsub_subscription=os.getenv("PUBSUB_SUBSCRIPTION", "analytics-events-sub"),
        bigquery_dataset=os.getenv("BIGQUERY_DATASET", "swarm_analytics"),
        bigquery_table=os.getenv("BIGQUERY_TABLE", "raw_events"),
    )
