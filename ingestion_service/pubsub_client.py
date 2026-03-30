from google.api_core.exceptions import GoogleAPICallError, RetryError
from google.cloud import pubsub_v1

from shared.config import Settings
from shared.schemas import AnalyticsEvent


class PublishEventError(Exception):
    pass


class PubSubPublisher:
    def __init__(self, settings: Settings):
        self._publisher = pubsub_v1.PublisherClient()
        self._topic_path = self._publisher.topic_path(
            settings.google_cloud_project,
            settings.pubsub_topic,
        )

    def publish_event(self, event: AnalyticsEvent) -> str:
        try:
            future = self._publisher.publish(
                self._topic_path,
                event.to_pubsub_message(),
                event_id=event.event_id,
                tenant_id=event.tenant_id,
                event_type=event.event_type,
            )
            return future.result(timeout=10)
        except (GoogleAPICallError, RetryError, TimeoutError) as exc:
            raise PublishEventError("Failed to publish event to Pub/Sub.") from exc
