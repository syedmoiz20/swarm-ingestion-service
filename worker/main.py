import logging

from google.cloud import pubsub_v1
from google.cloud.pubsub_v1.subscriber.message import Message

from shared.config import get_settings
from shared.schemas import AnalyticsEvent
from worker.bigquery_client import BigQueryInsertError, BigQueryWriter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EventSubscriberWorker:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.subscriber = pubsub_v1.SubscriberClient()
        self.writer = BigQueryWriter(self.settings)
        self.subscription_path = self.subscriber.subscription_path(
            self.settings.google_cloud_project,
            self.settings.pubsub_subscription,
        )

    def handle_message(self, message: Message) -> None:
        try:
            event = AnalyticsEvent.from_message_bytes(message.data)
            self.writer.insert_event(event)
        except (ValueError, BigQueryInsertError) as exc:
            logger.exception("Failed to process message: %s", exc)
            message.nack()
            return
        except Exception as exc:
            logger.exception("Unexpected worker error: %s", exc)
            message.nack()
            return

        logger.info("Processed event_id=%s", event.event_id)
        message.ack()

    def run(self) -> None:
        logger.info("Listening on %s", self.subscription_path)
        streaming_pull_future = self.subscriber.subscribe(
            self.subscription_path,
            callback=self.handle_message,
        )

        try:
            streaming_pull_future.result()
        except KeyboardInterrupt:
            streaming_pull_future.cancel()
            logger.info("Worker shutdown requested.")


if __name__ == "__main__":
    EventSubscriberWorker().run()
