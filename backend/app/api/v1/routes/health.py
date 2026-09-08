"""Liveness / readiness endpoint."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.deps import ServiceDep

router = APIRouter(tags=["health"])


@router.get("/health", summary="Service and search-backend status")
async def health(service: ServiceDep) -> dict[str, object]:
    return {"status": "ok", **await service.health()}
