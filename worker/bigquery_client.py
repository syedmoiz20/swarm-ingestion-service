from google.api_core.exceptions import GoogleAPICallError, RetryError
from google.cloud import bigquery

from shared.config import Settings
from shared.schemas import AnalyticsEvent


class BigQueryInsertError(Exception):
    pass


class BigQueryWriter:
    def __init__(self, settings: Settings):
        self._client = bigquery.Client(project=settings.google_cloud_project)
        self._table_id = settings.bigquery_table_id

    def insert_event(self, event: AnalyticsEvent) -> None:
        job_config = bigquery.LoadJobConfig(
            write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
        )

        try:
            job = self._client.load_table_from_json(
                [event.to_bigquery_row()],
                self._table_id,
                job_config=job_config,
            )
            job.result()
        except (GoogleAPICallError, RetryError) as exc:
            raise BigQueryInsertError(
                f"Failed to insert row into BigQuery table {self._table_id}."
            ) from exc

        if job.errors:
            raise BigQueryInsertError(f"Failed to insert row into BigQuery: {job.errors}")
