"""Minimal structured-ish logging setup. Called once from the app factory."""

from __future__ import annotations

import logging


def configure_logging(debug: bool = False) -> None:
    logging.basicConfig(
        level=logging.DEBUG if debug else logging.INFO,
        format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )
    logging.getLogger("elastic_transport.transport").setLevel(logging.WARNING)
