"""AOI watchlist — persisted as a flat JSON file, no database needed for a demo of this size."""
from __future__ import annotations

import json

from fastapi import APIRouter, HTTPException

from app.core.config import settings
from app.models.schemas import AOI

router = APIRouter(prefix="/watchlist", tags=["watchlist"])


def _load() -> list[AOI]:
    if not settings.watchlist_file.exists():
        return []
    raw = json.loads(settings.watchlist_file.read_text(encoding="utf-8"))
    return [AOI(**item) for item in raw]


def _save(aois: list[AOI]) -> None:
    settings.watchlist_file.write_text(
        json.dumps([a.model_dump() for a in aois], indent=2), encoding="utf-8"
    )


@router.get("", response_model=list[AOI])
async def list_aois() -> list[AOI]:
    return _load()


@router.post("", response_model=list[AOI])
async def add_aoi(aoi: AOI) -> list[AOI]:
    aois = [a for a in _load() if a.name != aoi.name]
    aois.append(aoi)
    _save(aois)
    return aois


@router.delete("/{name}", response_model=list[AOI])
async def remove_aoi(name: str) -> list[AOI]:
    aois = _load()
    remaining = [a for a in aois if a.name != name]
    if len(remaining) == len(aois):
        raise HTTPException(status_code=404, detail=f"AOI '{name}' not found")
    _save(remaining)
    return remaining
