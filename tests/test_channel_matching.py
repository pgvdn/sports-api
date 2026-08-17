import pytest
from app.utils.normalization import normalize_channel_name, channel_similarity
from app.services.channel_matcher import match_channels_for_broadcasters
from app.models.broadcaster import BroadcasterInfo
from app.models.channel import ChannelInput


def test_normalize_channel_name():
    # Resolution & Codec removal
    assert normalize_channel_name("UK | SKY SPORTS MAIN EVENT FHD") == "sky sports main event"
    assert normalize_channel_name("USA NETWORK HD") == "usa network"
    assert normalize_channel_name("US: NBC Sports 1080P 60FPS HEVC") == "nbc sports"
    assert normalize_channel_name("[UK] TNT Sports 1 4K UHD") == "tnt sports 1"
    assert normalize_channel_name("IN - Star Sports 1 HD (Hindi)") == "star sports 1 hindi"
    assert normalize_channel_name("CA | TSN 1 720p RAW") == "tsn 1"
    assert normalize_channel_name("AUS: Fox Cricket 50fps") == "fox cricket"


def test_channel_similarity_high_matches():
    # Exact normalized
    assert channel_similarity("USA Network", "USA NETWORK HD") == 1.0
    assert channel_similarity("Willow Cricket", "WILLOW CRICKET") == 1.0

    # Prefix & quality tags
    score_sky = channel_similarity("Sky Sports Main Event", "UK | SKY SPORTS MAIN EVENT FHD")
    assert score_sky >= 0.90, f"Expected >= 0.90, got {score_sky}"

    score_tnt = channel_similarity("TNT Sports 1", "[UK] TNT SPORTS 1 HD")
    assert score_tnt >= 0.90, f"Expected >= 0.90, got {score_tnt}"


def test_channel_similarity_distinguishes_numbered_channels():
    # Distinct channel numbers must NOT match
    score_diff_num = channel_similarity("Sky Sports 1", "UK | SKY SPORTS 2 HD")
    assert score_diff_num == 0.0 or score_diff_num < 0.5, f"Numbered channels shouldn't match: {score_diff_num}"

    score_star_diff = channel_similarity("Star Sports 1", "Star Sports 2 HD")
    assert score_star_diff == 0.0 or score_star_diff < 0.5


def test_match_channels_for_broadcasters():
    broadcasters = [
        BroadcasterInfo(
            name="Sky Sports Main Event",
            normalizedName="sky sports main event",
            countryCode="GB",
            country="United Kingdom",
        ),
        BroadcasterInfo(
            name="USA Network",
            normalizedName="usa network",
            countryCode="US",
            country="United States",
        ),
        BroadcasterInfo(
            name="Willow Cricket",
            normalizedName="willow cricket",
            countryCode="US",
            country="United States",
        ),
    ]

    playlist_channels = [
        ChannelInput(id="1001", name="UK | SKY SPORTS MAIN EVENT FHD"),
        ChannelInput(id="1002", name="USA NETWORK HD"),
        ChannelInput(id="1003", name="WILLOW CRICKET"),
        ChannelInput(id="1004", name="UK | SKY CINEMA ACTION HD"),  # Non-matching
    ]

    response = match_channels_for_broadcasters(
        broadcasters=broadcasters,
        channels=playlist_channels,
        threshold=0.80,
        event_id="soccer_epl_123456",
        event_name="Arsenal vs Liverpool",
    )

    assert response.eventId == "soccer_epl_123456"
    assert len(response.matches) == 3

    matched_ids = {m.channel.id for m in response.matches}
    assert "1001" in matched_ids
    assert "1002" in matched_ids
    assert "1003" in matched_ids
    assert "1004" not in matched_ids
