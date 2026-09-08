"""Elasticsearch index definition and bulk indexing.

The index is a denormalised view of a profile: one document per profile, with
`text` fields for keyword search and `keyword` sub-fields for filtering and
aggregations.
"""

from __future__ import annotations

import logging
from collections.abc import Sequence
from typing import Any

from elasticsearch import AsyncElasticsearch
from elasticsearch.helpers import async_bulk

from app.etl.parse import ProfileRecord

logger = logging.getLogger(__name__)

TEXT_WITH_KEYWORD: dict[str, Any] = {
    "type": "text",
    "fields": {"keyword": {"type": "keyword", "ignore_above": 256}},
}

INDEX_BODY: dict[str, Any] = {
    "settings": {
        "number_of_shards": 1,
        "number_of_replicas": 0,
        "analysis": {
            "analyzer": {
                "profile_text": {
                    "type": "custom",
                    "tokenizer": "standard",
                    "filter": ["lowercase", "asciifolding", "english_stop"],
                }
            },
            "filter": {"english_stop": {"type": "stop", "stopwords": "_english_"}},
        },
    },
    "mappings": {
        "properties": {
            "id": {"type": "integer"},
            "full_name": TEXT_WITH_KEYWORD,
            "headline": {"type": "text", "analyzer": "profile_text"},
            "job_title": {
                "type": "text",
                "analyzer": "profile_text",
                "fields": {"keyword": {"type": "keyword", "ignore_above": 256}},
            },
            "experience_titles": {"type": "text", "analyzer": "profile_text"},
            "company_name": TEXT_WITH_KEYWORD,
            "company_size": {"type": "keyword"},
            "industry": {"type": "keyword"},
            "seniority": {"type": "keyword"},
            "country": {"type": "keyword"},
            "region": {"type": "keyword"},
            "location_name": TEXT_WITH_KEYWORD,
            "years_experience": {"type": "float"},
            "summary": {"type": "text", "analyzer": "profile_text"},
            "education": {"type": "text", "analyzer": "profile_text"},
            "skills": {
                "type": "text",
                "analyzer": "profile_text",
                "fields": {"keyword": {"type": "keyword", "ignore_above": 128}},
            },
            "linkedin_url": {"type": "keyword", "index": False},
        }
    },
}


def to_document(record: ProfileRecord, profile_id: int) -> dict[str, Any]:
    """Flatten a parsed record into the indexed document."""
    headline = (
        f"{record.job_title} at {record.company_name}"
        if record.job_title and record.company_name
        else record.job_title or record.company_name
    )
    return {
        "id": profile_id,
        "full_name": record.full_name,
        "headline": headline,
        "job_title": record.job_title,
        "experience_titles": [item.title for item in record.experiences if item.title],
        "company_name": record.company_name,
        "company_size": record.company_size,
        "industry": record.industry,
        "seniority": record.seniority,
        "country": record.country,
        "region": record.region,
        "location_name": record.location_name,
        "years_experience": record.years_experience,
        "summary": record.summary,
        "education": [
            " ".join(filter(None, [item.school_name, *item.degrees, *item.majors]))
            for item in record.educations
        ],
        "skills": record.skills,
        "linkedin_url": record.linkedin_url,
    }


async def recreate_index(client: AsyncElasticsearch, index: str) -> None:
    """Drop and recreate the index. The dataset is a static snapshot."""
    await client.indices.delete(index=index, ignore_unavailable=True)
    await client.indices.create(index=index, **INDEX_BODY)


async def ensure_index(client: AsyncElasticsearch, index: str) -> None:
    if not await client.indices.exists(index=index):
        await client.indices.create(index=index, **INDEX_BODY)


async def bulk_index(
    client: AsyncElasticsearch,
    index: str,
    documents: Sequence[dict[str, Any]],
) -> int:
    actions = (
        {"_index": index, "_id": document["id"], "_source": document} for document in documents
    )
    indexed, _ = await async_bulk(client, actions, refresh=True)
    logger.info("Indexed %d documents into %s", indexed, index)
    return indexed
