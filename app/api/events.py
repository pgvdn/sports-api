from typing import Optional, List
from fastapi import APIRouter, Query, HTTPException, status

from app.models.event import Event, EventsListResponse
from app.models.broadcaster import BroadcasterInfo, EventBroadcastersResponse
from app.models.channel import ChannelMatchRequest, ChannelMatchResponse
from app.services.event_service import get_event_service
from app.services.broadcast_service import get_broadcast_service
from app.services.channel_matcher import match_channels_for_broadcasters
from app.utils.time import format_iso_datetime, utc_now

router = APIRouter(prefix="/events", tags=["Events"])


@router.get("/live", response_model=EventsListResponse)
async def get_live_events(
    sport: Optional[str] = Query(None, description="Filter by sport e.g. soccer, basketball, cricket, tennis"),
    debug: bool = Query(False, description="Include debug metadata"),
):
    """
    Returns all currently LIVE sports events across all configured providers.
    """
    event_service = get_event_service()
    events = await event_service.get_live_events(sport=sport)

    debug_data = None
    if debug:
        debug_data = {
            "querySport": sport,
            "timestamp": format_iso_datetime(utc_now()),
            "cached": True,
        }

    return EventsListResponse(
        total=len(events),
        sport=sport,
        status="LIVE",
        events=events,
        debug=debug_data,
    )


@router.get("/today", response_model=EventsListResponse)
async def get_today_events(
    sport: Optional[str] = Query(None, description="Filter by sport: soccer, basketball, cricket, tennis"),
    timezone: Optional[str] = Query(None, description="Timezone name e.g. America/New_York, Europe/London, Asia/Kolkata"),
    debug: bool = Query(False, description="Include debug metadata"),
):
    """
    Returns all sports events scheduled for today (in the specified or local timezone).
    """
    event_service = get_event_service()
    events = await event_service.get_today_events(sport=sport, tz_name=timezone)

    debug_data = None
    if debug:
        debug_data = {
            "querySport": sport,
            "timezone": timezone or "UTC",
            "timestamp": format_iso_datetime(utc_now()),
        }

    return EventsListResponse(
        total=len(events),
        sport=sport,
        date="today",
        events=events,
        debug=debug_data,
    )


@router.get("/upcoming", response_model=EventsListResponse)
async def get_upcoming_events(
    sport: Optional[str] = Query(None, description="Filter by sport: soccer, basketball, cricket, tennis"),
    hours: int = Query(24, ge=1, le=168, description="Upcoming time window in hours (default 24)"),
    limit: int = Query(100, ge=1, le=500, description="Max number of events to return"),
    debug: bool = Query(False, description="Include debug metadata"),
):
    """
    Returns upcoming sports events within the next N hours.
    """
    event_service = get_event_service()
    events = await event_service.get_upcoming_events(sport=sport, hours=hours, limit=limit)

    debug_data = None
    if debug:
        debug_data = {
            "querySport": sport,
            "hours": hours,
            "limit": limit,
            "timestamp": format_iso_datetime(utc_now()),
        }

    return EventsListResponse(
        total=len(events),
        sport=sport,
        status="UPCOMING",
        events=events,
        debug=debug_data,
    )


@router.get("/{event_id}", response_model=Event)
async def get_event_details(
    event_id: str,
    debug: bool = Query(False, description="Include debug metadata"),
):
    """
    Returns full details for a single event including teams, scores, venue, and broadcaster channels.
    """
    event_service = get_event_service()
    event = await event_service.get_event_by_id(event_id)

    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event with ID '{event_id}' was not found.",
        )

    # Ensure broadcasters are loaded
    broadcast_service = get_broadcast_service()
    broadcasters = await broadcast_service.get_broadcasters_for_event(event)
    event.broadcasters = broadcasters

    if debug:
        event.debug = {
            "externalIds": event.externalIds,
            "fetchedAt": format_iso_datetime(utc_now()),
        }

    return event


@router.get("/{event_id}/channels", response_model=EventBroadcastersResponse)
async def get_event_channels(
    event_id: str,
):
    """
    Returns legitimate TV and broadcast channels carrying this sporting event.
    The Apple TV IPTV client matches these broadcaster names against the user's Xtream/M3U playlist.
    """
    event_service = get_event_service()
    event = await event_service.get_event_by_id(event_id)

    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event with ID '{event_id}' was not found.",
        )

    broadcast_service = get_broadcast_service()
    broadcasters = await broadcast_service.get_broadcasters_for_event(event)

    event_title = f"{event.home.name} vs {event.away.name}"

    return EventBroadcastersResponse(
        eventId=event.id,
        eventName=event_title,
        sport=event.sport,
        startTime=event.startTime,
        broadcasters=broadcasters,
        totalCount=len(broadcasters),
    )


@router.post("/{event_id}/match-channels", response_model=ChannelMatchResponse)
async def match_playlist_channels_for_event(
    event_id: str,
    request: ChannelMatchRequest,
):
    """
    Optional server-side channel matching utility.
    Matches a user's playlist channels against the event's official broadcasters and returns matched streams.
    """
    event_service = get_event_service()
    event = await event_service.get_event_by_id(event_id)

    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event with ID '{event_id}' was not found.",
        )

    broadcast_service = get_broadcast_service()
    broadcasters = await broadcast_service.get_broadcasters_for_event(event)

    threshold = request.threshold if request.threshold is not None else 0.80
    event_title = f"{event.home.name} vs {event.away.name}"

    return match_channels_for_broadcasters(
        broadcasters=broadcasters,
        channels=request.channels,
        threshold=threshold,
        event_id=event.id,
        event_name=event_title,
    )
