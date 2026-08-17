from typing import List, Optional
from app.models.broadcaster import BroadcasterInfo
from app.models.channel import ChannelInput, ChannelMatch, ChannelMatchResponse
from app.utils.normalization import normalize_channel_name, channel_similarity


def match_channels_for_broadcasters(
    broadcasters: List[BroadcasterInfo],
    channels: List[ChannelInput],
    threshold: float = 0.80,
    event_id: str = "generic",
    event_name: Optional[str] = None,
) -> ChannelMatchResponse:
    """
    Matches a user's IPTV playlist channels against an event's verified broadcasters.
    Only returns matches with score >= threshold.
    """
    matches: List[ChannelMatch] = []
    seen_matches: set = set()

    for broadcaster in broadcasters:
        b_name = broadcaster.name
        b_norm = broadcaster.normalizedName

        best_for_broadcaster: Optional[ChannelMatch] = None
        best_score = 0.0

        for channel in channels:
            score = channel_similarity(b_name, channel.name)
            if score >= threshold:
                match_item = ChannelMatch(
                    broadcaster=b_name,
                    country=broadcaster.country,
                    channel=channel,
                    score=score,
                    matchedName=normalize_channel_name(channel.name),
                )
                
                # Deduplicate by (broadcaster, channel.id)
                key = (b_name, channel.id)
                if key not in seen_matches:
                    seen_matches.add(key)
                    matches.append(match_item)

    # Sort matches by score descending
    matches.sort(key=lambda m: m.score, reverse=True)

    return ChannelMatchResponse(
        eventId=event_id,
        eventName=event_name,
        threshold=threshold,
        totalBroadcasters=len(broadcasters),
        matches=matches,
    )
