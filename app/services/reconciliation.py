from difflib import SequenceMatcher
from typing import List, Dict, Tuple, Optional
from datetime import datetime

from app.models.event import Event, EventStatus
from app.models.broadcaster import BroadcasterInfo
from app.utils.time import parse_iso_datetime, is_time_proximate
from app.utils.normalization import normalize_channel_name
from app.utils.logging import logger


def _name_similarity(name1: str, name2: str) -> float:
    n1 = normalize_channel_name(name1)
    n2 = normalize_channel_name(name2)
    if not n1 or not n2:
        return 0.0
    if n1 == n2:
        return 1.0
    return SequenceMatcher(None, n1, n2).ratio()


def are_events_matching(e1: Event, e2: Event) -> bool:
    """
    Determines if two events from different providers represent the exact same match.
    Criteria:
      1. Same sport
      2. Start time within 90 minutes
      3. Team/participant names match with >= 0.70 similarity
    """
    if e1.sport != e2.sport:
        return False

    dt1 = parse_iso_datetime(e1.startTime)
    dt2 = parse_iso_datetime(e2.startTime)
    if not is_time_proximate(dt1, dt2, max_delta_minutes=90):
        return False

    home_sim = _name_similarity(e1.home.name, e2.home.name)
    away_sim = _name_similarity(e1.away.name, e2.away.name)

    # Check direct order: Home==Home and Away==Away
    if home_sim >= 0.70 and away_sim >= 0.70:
        return True

    # Check reversed order (e.g. tennis player listing variations)
    rev_home_sim = _name_similarity(e1.home.name, e2.away.name)
    rev_away_sim = _name_similarity(e1.away.name, e2.home.name)
    if rev_home_sim >= 0.70 and rev_away_sim >= 0.70:
        return True

    return False


def merge_two_events(primary: Event, secondary: Event) -> Event:
    """
    Merges data from secondary event into primary event.
    """
    # Merge external IDs
    merged_external_ids = dict(primary.externalIds)
    merged_external_ids.update(secondary.externalIds)

    # Prefer LIVE / FINISHED over SCHEDULED
    best_status = primary.status
    if primary.status == EventStatus.SCHEDULED and secondary.status in (EventStatus.LIVE, EventStatus.FINISHED):
        best_status = secondary.status

    # Merge Score
    best_score = primary.score or secondary.score

    # Merge Logos if missing
    if not primary.home.logo and secondary.home.logo:
        primary.home.logo = secondary.home.logo
    if not primary.away.logo and secondary.away.logo:
        primary.away.logo = secondary.away.logo
    if not primary.league.logo and secondary.league.logo:
        primary.league.logo = secondary.league.logo

    # Merge Broadcasters (deduplicated by normalized name and country)
    merged_broadcasters: List[BroadcasterInfo] = list(primary.broadcasters or [])
    seen_broadcasters = {
        (b.normalizedName, b.countryCode or "") for b in merged_broadcasters
    }

    for b in (secondary.broadcasters or []):
        key = (b.normalizedName, b.countryCode or "")
        if key not in seen_broadcasters:
            seen_broadcasters.add(key)
            merged_broadcasters.append(b)

    return Event(
        id=primary.id,
        externalIds=merged_external_ids,
        sport=primary.sport,
        league=primary.league,
        home=primary.home,
        away=primary.away,
        tennisPlayers=primary.tennisPlayers or secondary.tennisPlayers,
        cricketFormat=primary.cricketFormat or secondary.cricketFormat,
        startTime=primary.startTime,
        status=best_status,
        score=best_score,
        venue=primary.venue or secondary.venue,
        broadcasters=merged_broadcasters,
    )


EXCLUDED_LEAGUE_KEYWORDS = {
    "argentin",             # Matches Argentinian, Argentina, etc.
    "primera division",     # Argentine Primera División
    "primera nacional",     # Argentine Segunda División
    "liga profesional",     # Argentine top flight
    "brasileirao",          # Brazilian Série A
    "serie a brasil",       # Brazilian Série A
    "serie b brasil",       # Brazilian Série B
    "campeonato brasileiro",
    "copa do brasil",
    "copa argentina",
    "copa libertadores",
    "copa sudamericana",
    "recopa sudamericana",
    "chilean",
    "colombian",
    "uruguayan",
    "paraguayan",
    "ecuadorian",
    "peruvian",
    "bolivian",
    "venezuelan",
}


def is_event_excluded(event: Event) -> bool:
    """Checks if the event belongs to an excluded league/competition."""
    league_name = (event.league.name or "").lower()
    league_country = (event.league.country or "").lower()
    
    # Check league keywords
    for kw in EXCLUDED_LEAGUE_KEYWORDS:
        if kw in league_name:
            return True
            
    # Check if domestic event from excluded countries
    excluded_countries = {"argentina", "brazil", "chile", "colombia", "uruguay", "paraguay", "ecuador", "peru", "bolivia", "venezuela"}
    if event.sport == "soccer" and league_country in excluded_countries and "copa america" not in league_name:
        return True

    return False


def reconcile_events(events_list: List[Event]) -> List[Event]:
    """
    Deduplicates, merges, and filters a list of events collected from multiple providers.
    """
    if not events_list:
        return []

    reconciled: List[Event] = []

    for event in events_list:
        if is_event_excluded(event):
            continue

        matched_idx = -1
        for idx, existing in enumerate(reconciled):
            if are_events_matching(existing, event):
                matched_idx = idx
                break

        if matched_idx >= 0:
            reconciled[matched_idx] = merge_two_events(reconciled[matched_idx], event)
        else:
            reconciled.append(event)

    return reconciled
