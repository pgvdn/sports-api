import pytest
from app.providers.curated_broadcasters import get_curated_broadcasters_for_event


def test_fa_cup_broadcasters():
    broadcasters = get_curated_broadcasters_for_event(
        sport="soccer",
        league_name="Emirates FA Cup",
        home_name="Manchester United",
        away_name="Liverpool",
    )
    names = [b.name for b in broadcasters]
    assert "BBC One" in names or "ITV 1" in names
    assert "ESPN+" in names
    assert "Sony Sports Ten 2" in names or "SuperSport Football" in names


def test_carabao_cup_broadcasters():
    broadcasters = get_curated_broadcasters_for_event(
        sport="soccer",
        league_name="Carabao Cup",
        home_name="Chelsea",
        away_name="Arsenal",
    )
    names = [b.name for b in broadcasters]
    assert "Sky Sports Main Event" in names
    assert "Sky Sports Football" in names
    assert "Paramount+" in names


def test_copa_del_rey_broadcasters():
    broadcasters = get_curated_broadcasters_for_event(
        sport="soccer",
        league_name="Copa del Rey",
        home_name="Real Madrid",
        away_name="Barcelona",
    )
    names = [b.name for b in broadcasters]
    assert any("Movistar" in n or "La 1" in n for n in names)
    assert "ESPN+" in names


def test_coppa_italia_broadcasters():
    broadcasters = get_curated_broadcasters_for_event(
        sport="soccer",
        league_name="Coppa Italia",
        home_name="Juventus",
        away_name="Inter Milan",
    )
    names = [b.name for b in broadcasters]
    assert "Canale 5" in names
    assert "Paramount+" in names or "Premier Sports 1" in names


def test_dfb_pokal_broadcasters():
    broadcasters = get_curated_broadcasters_for_event(
        sport="soccer",
        league_name="DFB-Pokal",
        home_name="Bayern Munich",
        away_name="Borussia Dortmund",
    )
    names = [b.name for b in broadcasters]
    assert "Sky Sport DFB-Pokal" in names or "ARD Das Erste" in names
    assert "ESPN+" in names


def test_coupe_de_france_broadcasters():
    broadcasters = get_curated_broadcasters_for_event(
        sport="soccer",
        league_name="Coupe de France",
        home_name="Paris Saint-Germain",
        away_name="Marseille",
    )
    names = [b.name for b in broadcasters]
    assert any("France" in n or "beIN" in n for n in names)


def test_us_open_cup_broadcasters():
    broadcasters = get_curated_broadcasters_for_event(
        sport="soccer",
        league_name="U.S. Open Cup",
        home_name="Inter Miami",
        away_name="LA Galaxy",
    )
    names = [b.name for b in broadcasters]
    assert "CBS Sports Golazo" in names or "Paramount+" in names or "Apple TV" in names
