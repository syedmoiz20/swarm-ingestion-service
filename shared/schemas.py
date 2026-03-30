import json
from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field


class AnalyticsEvent(BaseModel):
    event_id: str
    tenant_id: str
    session_id: str
    user_id: str | None = None
    product_id: str
    event_type: Literal["product_view", "click", "add_to_cart", "purchase"]
    page_url: str
    event_ts: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)

    def _event_ts_utc(self) -> datetime:
        if self.event_ts.tzinfo is None:
            return self.event_ts.replace(tzinfo=timezone.utc)
        return self.event_ts.astimezone(timezone.utc)

    def to_pubsub_message(self) -> bytes:
        payload = self.model_dump(mode="json")
        return json.dumps(payload).encode("utf-8")

    def to_bigquery_row(self) -> dict[str, str | None]:
        created_at = datetime.now(timezone.utc).isoformat()
        return {
            "event_id": self.event_id,
            "tenant_id": self.tenant_id,
            "session_id": self.session_id,
            "user_id": self.user_id,
            "product_id": self.product_id,
            "event_type": self.event_type,
            "page_url": self.page_url,
            "event_ts": self._event_ts_utc().isoformat(),
            "metadata": json.dumps(self.metadata),
            "created_at": created_at,
        }

    @classmethod
    def from_message_bytes(cls, data: bytes) -> "AnalyticsEvent":
        payload = json.loads(data.decode("utf-8"))
        return cls.model_validate(payload)


class EventResponse(BaseModel):
    ok: bool = True


class HealthResponse(BaseModel):
    status: str
