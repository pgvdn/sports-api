from typing import List
from fastapi import APIRouter
from pydantic import BaseModel

from app.providers.base import ProviderStatus
from app.providers.registry import get_provider_registry

router = APIRouter(prefix="/providers", tags=["Providers"])


class ProvidersStatusResponse(BaseModel):
    total: int
    providers: List[ProviderStatus]


@router.get("/status", response_model=ProvidersStatusResponse)
async def get_providers_status():
    """
    Returns live health, rate-limit, and request quota metrics for all sports & broadcast providers.
    """
    registry = get_provider_registry()
    statuses = registry.get_all_statuses()
    return ProvidersStatusResponse(
        total=len(statuses),
        providers=statuses,
    )
