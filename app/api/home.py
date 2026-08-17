from fastapi import APIRouter, Query
from app.models.event import HomeScreenResponse
from app.services.event_service import get_event_service

router = APIRouter(prefix="/home", tags=["Home Screen"])


@router.get("", response_model=HomeScreenResponse)
async def get_home_screen_feed(
    debug: bool = Query(False, description="Include provider debug details"),
):
    """
    Returns the comprehensive sports feed optimized for the Apple TV IPTV client.
    Includes Live now, Starting Soon, and curated rows for Football, Cricket, NBA, and Tennis.
    """
    event_service = get_event_service()
    feed = await event_service.get_home_screen()
    if debug:
        feed.debug = {"provider": "TheSportsDB + API-Sports (fallback)", "cached": True}
    return feed
