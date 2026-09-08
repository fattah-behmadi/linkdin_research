"""Elasticsearch client factory. One client per process, owned by the app lifespan."""

from __future__ import annotations

from elasticsearch import AsyncElasticsearch

from app.core.config import Settings


def create_client(settings: Settings) -> AsyncElasticsearch:
    return AsyncElasticsearch(
        settings.elasticsearch_url,
        request_timeout=settings.elasticsearch_request_timeout,
        retry_on_timeout=True,
        max_retries=2,
    )
