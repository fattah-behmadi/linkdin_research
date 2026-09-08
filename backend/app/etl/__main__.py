"""Dataset seeding CLI.

python -m app.etl                 # parse the dataset, load SQLite (+FTS5),
                                  # and index Elasticsearch when it is the
                                  # configured backend
python -m app.etl --es            # force Elasticsearch indexing
python -m app.etl --no-es         # relational store only
python -m app.etl --dataset path/to/file.csv
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from pathlib import Path

from app.core.config import SearchBackend, get_settings
from app.core.logging import configure_logging
from app.db.session import get_engine
from app.etl.load_sql import load
from app.etl.parse import ProfileRecord, load_profiles
from app.search.client import create_client
from app.search.index import bulk_index, recreate_index, to_document

logger = logging.getLogger("app.etl")


async def _index_elasticsearch(loaded: list[tuple[int, ProfileRecord]]) -> int:
    settings = get_settings()
    client = create_client(settings)
    try:
        await recreate_index(client, settings.elasticsearch_index)
        documents = [to_document(record, profile_id) for profile_id, record in loaded]
        return await bulk_index(client, settings.elasticsearch_index, documents)
    finally:
        await client.close()


async def seed(dataset: Path, index_elasticsearch: bool) -> int:
    records, report = load_profiles(dataset)
    if not records:
        logger.error("No usable records found in %s", dataset)
        return 1

    loaded = await load(get_engine(), records)
    logger.info("Parse report: %s", report.as_dict())

    if index_elasticsearch:
        try:
            await _index_elasticsearch(loaded)
        except Exception as error:
            logger.error("Elasticsearch indexing failed (%s). SQLite data is loaded.", error)
            return 2
    await get_engine().dispose()
    return 0


def main() -> int:
    settings = get_settings()
    parser = argparse.ArgumentParser(
        prog="python -m app.etl",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--dataset", type=Path, default=settings.dataset_path)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--es", dest="es", action="store_true", help="force Elasticsearch indexing")
    group.add_argument("--no-es", dest="es", action="store_false", help="skip Elasticsearch")
    parser.set_defaults(es=settings.search_backend is SearchBackend.ELASTICSEARCH)
    args = parser.parse_args()

    configure_logging(debug=False)
    if not args.dataset.exists():
        logger.error("Dataset not found: %s", args.dataset)
        return 1
    return asyncio.run(seed(args.dataset, index_elasticsearch=args.es))


if __name__ == "__main__":
    sys.exit(main())
