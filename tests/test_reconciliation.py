import pytest
from app.models.event import Event, EventStatus, EventScore
from app.models.league import LeagueInfo, ParticipantInfo
from app.models.broadcaster import BroadcasterInfo
from app.services.reconciliation import are_events_matching, merge_two_events, reconcile_events


def test_are_events_matching_exact():
    e1 = Event(
        id="soccer_epl_1",
        externalIds={"thesportsdb": "1"},
        sport="soccer",
        league=LeagueInfo(id="4328", name="Premier League"),
        home=ParticipantInfo(name="Arsenal"),
        away=ParticipantInfo(name="Liverpool"),
        startTime="2026-08-17T19:00:00Z",
        status=EventStatus.SCHEDULED,
    )
    e2 = Event(
        id="soccer_epl_2",
        externalIds={"apiFootball": "999"},
        sport="soccer",
        league=LeagueInfo(id="39", name="Premier League"),
        home=ParticipantInfo(name="Arsenal FC"),
        away=ParticipantInfo(name="Liverpool FC"),
        startTime="2026-08-17T19:00:00Z",
        status=EventStatus.LIVE,
    )

    assert are_events_matching(e1, e2) is True


def test_are_events_matching_different_sport():
    e1 = Event(
        id="soccer_epl_1",
        sport="soccer",
        league=LeagueInfo(id="4328", name="Premier League"),
        home=ParticipantInfo(name="Arsenal"),
        away=ParticipantInfo(name="Liverpool"),
        startTime="2026-08-17T19:00:00Z",
        status=EventStatus.SCHEDULED,
    )
    e2 = Event(
        id="cricket_match_1",
        sport="cricket",
        league=LeagueInfo(id="10", name="IPL"),
        home=ParticipantInfo(name="Arsenal"),
        away=ParticipantInfo(name="Liverpool"),
        startTime="2026-08-17T19:00:00Z",
        status=EventStatus.SCHEDULED,
    )

    assert are_events_matching(e1, e2) is False


def test_merge_two_events():
    e1 = Event(
        id="soccer_epl_1",
        externalIds={"thesportsdb": "1"},
        sport="soccer",
        league=LeagueInfo(id="4328", name="Premier League"),
        home=ParticipantInfo(name="Arsenal"),
        away=ParticipantInfo(name="Liverpool"),
        startTime="2026-08-17T19:00:00Z",
        status=EventStatus.SCHEDULED,
        broadcasters=[
            BroadcasterInfo(name="Sky Sports", normalizedName="sky sports", countryCode="GB"),
        ],
    )
    e2 = Event(
        id="soccer_epl_2",
        externalIds={"apiFootball": "999"},
        sport="soccer",
        league=LeagueInfo(id="39", name="Premier League"),
        home=ParticipantInfo(name="Arsenal"),
        away=ParticipantInfo(name="Liverpool"),
        startTime="2026-08-17T19:00:00Z",
        status=EventStatus.LIVE,
        score=EventScore(home=2, away=1),
        broadcasters=[
            BroadcasterInfo(name="USA Network", normalizedName="usa network", countryCode="US"),
        ],
    )

    merged = merge_two_events(e1, e2)

    assert merged.externalIds == {"thesportsdb": "1", "apiFootball": "999"}
    assert merged.status == EventStatus.LIVE
    assert merged.score is not None and merged.score.home == 2
    assert len(merged.broadcasters) == 2


def test_reconcile_events_deduplication():
    e1 = Event(
        id="soccer_1",
        externalIds={"thesportsdb": "1"},
        sport="soccer",
        league=LeagueInfo(id="4328", name="Premier League"),
        home=ParticipantInfo(name="Arsenal"),
        away=ParticipantInfo(name="Liverpool"),
        startTime="2026-08-17T19:00:00Z",
        status=EventStatus.SCHEDULED,
    )
    e2 = Event(
        id="soccer_2",
        externalIds={"apiFootball": "99"},
        sport="soccer",
        league=LeagueInfo(id="39", name="Premier League"),
        home=ParticipantInfo(name="Arsenal FC"),
        away=ParticipantInfo(name="Liverpool FC"),
        startTime="2026-08-17T19:00:00Z",
        status=EventStatus.LIVE,
    )
    e3 = Event(
        id="basketball_1",
        externalIds={"thesportsdb": "500"},
        sport="basketball",
        league=LeagueInfo(id="4387", name="NBA"),
        home=ParticipantInfo(name="Boston Celtics"),
        away=ParticipantInfo(name="New York Knicks"),
        startTime="2026-08-17T23:30:00Z",
        status=EventStatus.SCHEDULED,
    )

    result = reconcile_events([e1, e2, e3])

    # e1 and e2 should merge into 1 event, e3 remains distinct
    assert len(result) == 2
    sports = {e.sport for e in result}
    assert "soccer" in sports
    assert "basketball" in sports
