from functools import lru_cache

from fastapi import FastAPI, HTTPException, status

from ingestion_service.pubsub_client import PubSubPublisher, PublishEventError
from shared.config import get_settings
from shared.schemas import AnalyticsEvent, EventResponse, HealthResponse

app = FastAPI(title="Swarm Analytics Ingestion Service", version="0.1.0")


@lru_cache
def get_publisher() -> PubSubPublisher:
    return PubSubPublisher(get_settings())


@app.get("/health", response_model=HealthResponse)
def healthcheck() -> HealthResponse:
    return HealthResponse(status="ok")


@app.post("/events", response_model=EventResponse, status_code=status.HTTP_202_ACCEPTED)
def ingest_event(event: AnalyticsEvent) -> EventResponse:
    try:
        get_publisher().publish_event(event)
    except PublishEventError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected error while publishing event.",
        ) from exc

    return EventResponse(ok=True)
