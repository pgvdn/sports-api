from typing import List, Dict, Any, Optional
from app.models.broadcaster import BroadcasterInfo
from app.utils.normalization import normalize_channel_name

# Canonical directory of verified official TV broadcasters for major sports leagues and domestic cups
# Keyed by lowercase league keyword or tournament name
LEAGUE_BROADCASTER_MAPPINGS: Dict[str, List[Dict[str, Any]]] = {
    # -------------------------------------------------------------
    # 1. TOP DOMESTIC LEAGUES
    # -------------------------------------------------------------
    "premier league": [
        {"name": "Sky Sports Main Event", "countryCode": "GB", "country": "United Kingdom", "language": "English"},
        {"name": "Sky Sports Premier League", "countryCode": "GB", "country": "United Kingdom", "language": "English"},
        {"name": "TNT Sports 1", "countryCode": "GB", "country": "United Kingdom", "language": "English"},
        {"name": "USA Network", "countryCode": "US", "country": "United States", "language": "English"},
        {"name": "NBC Sports", "countryCode": "US", "country": "United States", "language": "English"},
        {"name": "Peacock", "countryCode": "US", "country": "United States", "language": "English", "type": "ott"},
        {"name": "Star Sports Select 1", "countryCode": "IN", "country": "India", "language": "English"},
        {"name": "Star Sports Select 2", "countryCode": "IN", "country": "India", "language": "English"},
        {"name": "JioCinema", "countryCode": "IN", "country": "India", "language": "English", "type": "ott"},
        {"name": "SuperSport Premier League", "countryCode": "ZA", "country": "South Africa", "language": "English"},
        {"name": "SuperSport Grandstand", "countryCode": "ZA", "country": "South Africa", "language": "English"},
        {"name": "Optus Sport 1", "countryCode": "AU", "country": "Australia", "language": "English"},
        {"name": "beIN Sports 1", "countryCode": "QA", "country": "Middle East", "language": "Arabic"},
        {"name": "beIN Sports 1 English", "countryCode": "QA", "country": "Middle East", "language": "English"},
        {"name": "DAZN 1", "countryCode": "ES", "country": "Spain", "language": "Spanish"},
        {"name": "Canal+ Sport", "countryCode": "FR", "country": "France", "language": "French"},
        {"name": "Sky Sport Premier League", "countryCode": "DE", "country": "Germany", "language": "German"},
        {"name": "Sky Sport Calcio", "countryCode": "IT", "country": "Italy", "language": "Italian"},
    ],
    "la liga": [
        {"name": "ITV 4", "countryCode": "GB", "country": "United Kingdom", "language": "English"},
        {"name": "Premier Sports 1", "countryCode": "GB", "country": "United Kingdom", "language": "English"},
        {"name": "ESPN+", "countryCode": "US", "country": "United States", "language": "English", "type": "ott"},
        {"name": "ESPN Deportes", "countryCode": "US", "country": "United States", "language": "Spanish"},
        {"name": "Sports18 1", "countryCode": "IN", "country": "India", "language": "English"},
        {"name": "JioCinema", "countryCode": "IN", "country": "India", "language": "English", "type": "ott"},
        {"name": "SuperSport LaLiga", "countryCode": "ZA", "country": "South Africa", "language": "English"},
        {"name": "Optus Sport 1", "countryCode": "AU", "country": "Australia", "language": "English"},
        {"name": "Movistar LaLiga", "countryCode": "ES", "country": "Spain", "language": "Spanish"},
        {"name": "DAZN LaLiga", "countryCode": "ES", "country": "Spain", "language": "Spanish"},
        {"name": "beIN Sports 3", "countryCode": "QA", "country": "Middle East", "language": "Arabic"},
    ],
    "serie a": [
        {"name": "TNT Sports 1", "countryCode": "GB", "country": "United Kingdom", "language": "English"},
        {"name": "CBS Sports Network", "countryCode": "US", "country": "United States", "language": "English"},
        {"name": "Paramount+", "countryCode": "US", "country": "United States", "language": "English", "type": "ott"},
        {"name": "Sports18 1", "countryCode": "IN", "country": "India", "language": "English"},
        {"name": "SuperSport Football", "countryCode": "ZA", "country": "South Africa", "language": "English"},
        {"name": "beIN Sports 4", "countryCode": "QA", "country": "Middle East", "language": "Arabic"},
        {"name": "DAZN Serie A", "countryCode": "IT", "country": "Italy", "language": "Italian"},
        {"name": "Sky Sport Uno", "countryCode": "IT", "country": "Italy", "language": "Italian"},
    ],
    "bundesliga": [
        {"name": "Sky Sports Football", "countryCode": "GB", "country": "United Kingdom", "language": "English"},
        {"name": "ESPN+", "countryCode": "US", "country": "United States", "language": "English", "type": "ott"},
        {"name": "Sony Sports Ten 2", "countryCode": "IN", "country": "India", "language": "English"},
        {"name": "Sony Sports Ten 5", "countryCode": "IN", "country": "India", "language": "English"},
        {"name": "SuperSport Variety 3", "countryCode": "ZA", "country": "South Africa", "language": "English"},
        {"name": "Sky Sport Bundesliga 1", "countryCode": "DE", "country": "Germany", "language": "German"},
        {"name": "beIN Sports 5", "countryCode": "QA", "country": "Middle East", "language": "Arabic"},
    ],
    "ligue 1": [
        {"name": "beIN Sports 1", "countryCode": "US", "country": "United States", "language": "French/English"},
        {"name": "beIN Sports en Español", "countryCode": "US", "country": "United States", "language": "Spanish"},
        {"name": "DAZN 1", "countryCode": "FR", "country": "France", "language": "French"},
        {"name": "beIN Sports 1 FR", "countryCode": "FR", "country": "France", "language": "French"},
        {"name": "Sports18 1", "countryCode": "IN", "country": "India", "language": "English"},
        {"name": "SuperSport Football", "countryCode": "ZA", "country": "South Africa", "language": "English"},
    ],
    "mls": [
        {"name": "Apple TV - MLS Season Pass", "countryCode": "US", "country": "Worldwide", "language": "English", "type": "ott"},
        {"name": "FOX Sports 1", "countryCode": "US", "country": "United States", "language": "English"},
        {"name": "FOX Deportes", "countryCode": "US", "country": "United States", "language": "Spanish"},
        {"name": "TSN 1", "countryCode": "CA", "country": "Canada", "language": "English"},
    ],
    "saudi pro league": [
        {"name": "SSC 1 HD", "countryCode": "SA", "country": "Saudi Arabia", "language": "Arabic"},
        {"name": "SSC 5 HD", "countryCode": "SA", "country": "Saudi Arabia", "language": "Arabic"},
        {"name": "Shahid", "countryCode": "SA", "country": "Worldwide", "language": "Arabic", "type": "ott"},
        {"name": "FOX Soccer Plus", "countryCode": "US", "country": "United States", "language": "English"},
        {"name": "Sony Sports Ten 2", "countryCode": "IN", "country": "India", "language": "English"},
        {"name": "Canal+ Sport", "countryCode": "FR", "country": "France", "language": "French"},
        {"name": "DAZN 1", "countryCode": "GB", "country": "United Kingdom", "language": "English"},
    ],
    "indian super league": [
        {"name": "Sports18 1", "countryCode": "IN", "country": "India", "language": "English"},
        {"name": "Sports18 Khel", "countryCode": "IN", "country": "India", "language": "Hindi"},
        {"name": "JioCinema", "countryCode": "IN", "country": "India", "language": "English/Hindi", "type": "ott"},
        {"name": "OneFootball", "countryCode": "DE", "country": "Worldwide", "language": "English", "type": "ott"},
    ],
    "primeira liga": [
        {"name": "Sport TV 1", "countryCode": "PT", "country": "Portugal", "language": "Portuguese"},
        {"name": "Benfica TV", "countryCode": "PT", "country": "Portugal", "language": "Portuguese"},
        {"name": "GolTV", "countryCode": "US", "country": "United States", "language": "Portuguese/Spanish"},
        {"name": "Triller TV+", "countryCode": "GB", "country": "United Kingdom", "language": "English", "type": "ott"},
    ],
    "eredivisie": [
        {"name": "ESPN 1 NL", "countryCode": "NL", "country": "Netherlands", "language": "Dutch"},
        {"name": "ESPN 2 NL", "countryCode": "NL", "country": "Netherlands", "language": "Dutch"},
        {"name": "ESPN+", "countryCode": "US", "country": "United States", "language": "English", "type": "ott"},
        {"name": "Triller TV+", "countryCode": "GB", "country": "United Kingdom", "language": "English"},
    ],

    # -------------------------------------------------------------
    # 2. DOMESTIC CUPS & SUPER CUPS (ALL COUNTRIES)
    # -------------------------------------------------------------
    # England
    "fa cup": [
        {"name": "BBC One", "countryCode": "GB", "country": "United Kingdom", "language": "English"},
        {"name": "BBC Two", "countryCode": "GB", "country": "United Kingdom", "language": "English"},
        {"name": "ITV 1", "countryCode": "GB", "country": "United Kingdom", "language": "English"},
        {"name": "ITV 4", "countryCode": "GB", "country": "United Kingdom", "language": "English"},
        {"name": "ESPN+", "countryCode": "US", "country": "United States", "language": "English", "type": "ott"},
        {"name": "Sony Sports Ten 2", "countryCode": "IN", "country": "India", "language": "English"},
        {"name": "Sony Sports Ten 3", "countryCode": "IN", "country": "India", "language": "Hindi"},
        {"name": "SuperSport Football", "countryCode": "ZA", "country": "South Africa", "language": "English"},
        {"name": "SuperSport Premier League", "countryCode": "ZA", "country": "South Africa", "language": "English"},
        {"name": "Optus Sport 1", "countryCode": "AU", "country": "Australia", "language": "English"},
        {"name": "beIN Sports 1", "countryCode": "QA", "country": "Middle East", "language": "Arabic"},
    ],
    "carabao cup": [
        {"name": "Sky Sports Main Event", "countryCode": "GB", "country": "United Kingdom", "language": "English"},
        {"name": "Sky Sports Football", "countryCode": "GB", "country": "United Kingdom", "language": "English"},
        {"name": "ITV 4", "countryCode": "GB", "country": "United Kingdom", "language": "English"},
        {"name": "Paramount+", "countryCode": "US", "country": "United States", "language": "English", "type": "ott"},
        {"name": "CBS Sports Network", "countryCode": "US", "country": "United States", "language": "English"},
        {"name": "Sony Sports Ten 1", "countryCode": "IN", "country": "India", "language": "English"},
        {"name": "FanCode", "countryCode": "IN", "country": "India", "language": "English", "type": "ott"},
        {"name": "SuperSport Premier League", "countryCode": "ZA", "country": "South Africa", "language": "English"},
        {"name": "beIN Sports 2", "countryCode": "QA", "country": "Middle East", "language": "Arabic"},
    ],
    "efl cup": [
        {"name": "Sky Sports Main Event", "countryCode": "GB", "country": "United Kingdom", "language": "English"},
        {"name": "Sky Sports Football", "countryCode": "GB", "country": "United Kingdom", "language": "English"},
        {"name": "Paramount+", "countryCode": "US", "country": "United States", "language": "English", "type": "ott"},
        {"name": "Sony Sports Ten 1", "countryCode": "IN", "country": "India", "language": "English"},
        {"name": "SuperSport Premier League", "countryCode": "ZA", "country": "South Africa", "language": "English"},
    ],
    "community shield": [
        {"name": "ITV 1", "countryCode": "GB", "country": "United Kingdom", "language": "English"},
        {"name": "ESPN+", "countryCode": "US", "country": "United States", "language": "English", "type": "ott"},
        {"name": "Sony Sports Ten 2", "countryCode": "IN", "country": "India", "language": "English"},
        {"name": "SuperSport Premier League", "countryCode": "ZA", "country": "South Africa", "language": "English"},
    ],

    # Spain
    "copa del rey": [
        {"name": "La 1 (TVE)", "countryCode": "ES", "country": "Spain", "language": "Spanish"},
        {"name": "Movistar Copa del Rey", "countryCode": "ES", "country": "Spain", "language": "Spanish"},
        {"name": "ESPN+", "countryCode": "US", "country": "United States", "language": "English", "type": "ott"},
        {"name": "ESPN Deportes", "countryCode": "US", "country": "United States", "language": "Spanish"},
        {"name": "Fanatiz", "countryCode": "US", "country": "United States", "language": "Spanish", "type": "ott"},
        {"name": "Sports18 1", "countryCode": "IN", "country": "India", "language": "English"},
        {"name": "JioCinema", "countryCode": "IN", "country": "India", "language": "English", "type": "ott"},
        {"name": "L'Équipe", "countryCode": "FR", "country": "France", "language": "French"},
        {"name": "SuperSport LaLiga", "countryCode": "ZA", "country": "South Africa", "language": "English"},
        {"name": "Shahid", "countryCode": "SA", "country": "Middle East", "language": "Arabic", "type": "ott"},
    ],
    "supercopa de espana": [
        {"name": "Movistar Supercopa", "countryCode": "ES", "country": "Spain", "language": "Spanish"},
        {"name": "ESPN+", "countryCode": "US", "country": "United States", "language": "English", "type": "ott"},
        {"name": "ABC", "countryCode": "US", "country": "United States", "language": "English"},
        {"name": "Sports18 1", "countryCode": "IN", "country": "India", "language": "English"},
        {"name": "SuperSport LaLiga", "countryCode": "ZA", "country": "South Africa", "language": "English"},
    ],

    # Italy
    "coppa italia": [
        {"name": "Canale 5", "countryCode": "IT", "country": "Italy", "language": "Italian"},
        {"name": "Italia 1", "countryCode": "IT", "country": "Italy", "language": "Italian"},
        {"name": "Premier Sports 1", "countryCode": "GB", "country": "United Kingdom", "language": "English"},
        {"name": "Paramount+", "countryCode": "US", "country": "United States", "language": "English", "type": "ott"},
        {"name": "CBS Sports Network", "countryCode": "US", "country": "United States", "language": "English"},
        {"name": "Sports18 1", "countryCode": "IN", "country": "India", "language": "English"},
        {"name": "SuperSport Football", "countryCode": "ZA", "country": "South Africa", "language": "English"},
        {"name": "DAZN 1", "countryCode": "DE", "country": "Germany", "language": "German"},
        {"name": "L'Équipe", "countryCode": "FR", "country": "France", "language": "French"},
    ],
    "supercoppa italiana": [
        {"name": "Canale 5", "countryCode": "IT", "country": "Italy", "language": "Italian"},
        {"name": "Premier Sports 1", "countryCode": "GB", "country": "United Kingdom", "language": "English"},
        {"name": "Paramount+", "countryCode": "US", "country": "United States", "language": "English", "type": "ott"},
        {"name": "Sports18 1", "countryCode": "IN", "country": "India", "language": "English"},
        {"name": "SuperSport Football", "countryCode": "ZA", "country": "South Africa", "language": "English"},
    ],

    # Germany
    "dfb-pokal": [
        {"name": "ARD Das Erste", "countryCode": "DE", "country": "Germany", "language": "German"},
        {"name": "ZDF", "countryCode": "DE", "country": "Germany", "language": "German"},
        {"name": "Sky Sport DFB-Pokal", "countryCode": "DE", "country": "Germany", "language": "German"},
        {"name": "Premier Sports 1", "countryCode": "GB", "country": "United Kingdom", "language": "English"},
        {"name": "ESPN+", "countryCode": "US", "country": "United States", "language": "English", "type": "ott"},
        {"name": "Sony Sports Ten 2", "countryCode": "IN", "country": "India", "language": "English"},
        {"name": "SuperSport Variety 3", "countryCode": "ZA", "country": "South Africa", "language": "English"},
        {"name": "L'Équipe", "countryCode": "FR", "country": "France", "language": "French"},
    ],
    "dfl-supercup": [
        {"name": "Sat.1", "countryCode": "DE", "country": "Germany", "language": "German"},
        {"name": "Sky Sport Bundesliga 1", "countryCode": "DE", "country": "Germany", "language": "German"},
        {"name": "ESPN+", "countryCode": "US", "country": "United States", "language": "English", "type": "ott"},
        {"name": "Sony Sports Ten 2", "countryCode": "IN", "country": "India", "language": "English"},
        {"name": "SuperSport Variety 3", "countryCode": "ZA", "country": "South Africa", "language": "English"},
    ],

    # France
    "coupe de france": [
        {"name": "France 2", "countryCode": "FR", "country": "France", "language": "French"},
        {"name": "France 3", "countryCode": "FR", "country": "France", "language": "French"},
        {"name": "beIN Sports 1 FR", "countryCode": "FR", "country": "France", "language": "French"},
        {"name": "FOX Sports 1", "countryCode": "US", "country": "United States", "language": "English"},
        {"name": "FOX Sports 2", "countryCode": "US", "country": "United States", "language": "English"},
        {"name": "beIN Sports 1", "countryCode": "QA", "country": "Middle East", "language": "Arabic"},
    ],

    # Scotland
    "scottish cup": [
        {"name": "BBC One Scotland", "countryCode": "GB", "country": "United Kingdom", "language": "English"},
        {"name": "Premier Sports 1", "countryCode": "GB", "country": "United Kingdom", "language": "English"},
        {"name": "Paramount+", "countryCode": "US", "country": "United States", "language": "English", "type": "ott"},
    ],
    "scottish league cup": [
        {"name": "Premier Sports 1", "countryCode": "GB", "country": "United Kingdom", "language": "English"},
        {"name": "Paramount+", "countryCode": "US", "country": "United States", "language": "English", "type": "ott"},
    ],

    # Portugal
    "taca de portugal": [
        {"name": "RTP 1", "countryCode": "PT", "country": "Portugal", "language": "Portuguese"},
        {"name": "Sport TV 1", "countryCode": "PT", "country": "Portugal", "language": "Portuguese"},
        {"name": "RTP Internacional", "countryCode": "PT", "country": "Worldwide", "language": "Portuguese"},
        {"name": "FOX Soccer Plus", "countryCode": "US", "country": "United States", "language": "English"},
    ],

    # Netherlands
    "knvb beker": [
        {"name": "ESPN 1 NL", "countryCode": "NL", "country": "Netherlands", "language": "Dutch"},
        {"name": "ESPN Deportes", "countryCode": "US", "country": "United States", "language": "Spanish"},
        {"name": "GolTV", "countryCode": "US", "country": "United States", "language": "Spanish"},
    ],

    # Turkey
    "turkiye kupasi": [
        {"name": "A Spor", "countryCode": "TR", "country": "Turkey", "language": "Turkish"},
        {"name": "ATV", "countryCode": "TR", "country": "Turkey", "language": "Turkish"},
    ],

    # Saudi Arabia
    "king's cup": [
        {"name": "SSC 1 HD", "countryCode": "SA", "country": "Saudi Arabia", "language": "Arabic"},
        {"name": "SSC 5 HD", "countryCode": "SA", "country": "Saudi Arabia", "language": "Arabic"},
        {"name": "Shahid", "countryCode": "SA", "country": "Worldwide", "language": "Arabic", "type": "ott"},
        {"name": "FOX Soccer Plus", "countryCode": "US", "country": "United States", "language": "English"},
    ],
    "saudi super cup": [
        {"name": "SSC 1 HD", "countryCode": "SA", "country": "Saudi Arabia", "language": "Arabic"},
        {"name": "Shahid", "countryCode": "SA", "country": "Worldwide", "language": "Arabic", "type": "ott"},
        {"name": "FOX Soccer Plus", "countryCode": "US", "country": "United States", "language": "English"},
    ],

    # United States
    "us open cup": [
        {"name": "CBS Sports Golazo", "countryCode": "US", "country": "United States", "language": "English"},
        {"name": "Paramount+", "countryCode": "US", "country": "United States", "language": "English", "type": "ott"},
        {"name": "Universo", "countryCode": "US", "country": "United States", "language": "Spanish"},
        {"name": "Apple TV", "countryCode": "US", "country": "Worldwide", "language": "English", "type": "ott"},
    ],
    "leagues cup": [
        {"name": "Apple TV - MLS Season Pass", "countryCode": "US", "country": "Worldwide", "language": "English", "type": "ott"},
        {"name": "FOX Sports 1", "countryCode": "US", "country": "United States", "language": "English"},
        {"name": "Univision", "countryCode": "US", "country": "United States", "language": "Spanish"},
        {"name": "TUDN", "countryCode": "US", "country": "United States", "language": "Spanish"},
    ],

    # Brazil & Argentina
    "copa do brasil": [
        {"name": "TV Globo", "countryCode": "BR", "country": "Brazil", "language": "Portuguese"},
        {"name": "SporTV", "countryCode": "BR", "country": "Brazil", "language": "Portuguese"},
        {"name": "Premiere", "countryCode": "BR", "country": "Brazil", "language": "Portuguese"},
        {"name": "Prime Video", "countryCode": "BR", "country": "Brazil", "language": "Portuguese", "type": "ott"},
    ],
    "copa argentina": [
        {"name": "TyC Sports", "countryCode": "AR", "country": "Argentina", "language": "Spanish"},
        {"name": "TyC Sports Internacional", "countryCode": "AR", "country": "Worldwide", "language": "Spanish"},
        {"name": "Fanatiz", "countryCode": "US", "country": "United States", "language": "Spanish", "type": "ott"},
    ],

    # India
    "durand cup": [
        {"name": "Sony Sports Ten 2", "countryCode": "IN", "country": "India", "language": "English"},
        {"name": "Sony LIV", "countryCode": "IN", "country": "India", "language": "English", "type": "ott"},
    ],
    "super cup india": [
        {"name": "Sports18 1", "countryCode": "IN", "country": "India", "language": "English"},
        {"name": "JioCinema", "countryCode": "IN", "country": "India", "language": "English", "type": "ott"},
    ],

    # -------------------------------------------------------------
    # 3. EUROPEAN & INTERNATIONAL CLUB TOURNAMENTS
    # -------------------------------------------------------------
    "champions league": [
        {"name": "TNT Sports 1", "countryCode": "GB", "country": "United Kingdom", "language": "English"},
        {"name": "TNT Sports 2", "countryCode": "GB", "country": "United Kingdom", "language": "English"},
        {"name": "TNT Sports Ultimate", "countryCode": "GB", "country": "United Kingdom", "language": "English"},
        {"name": "CBS Sports Network", "countryCode": "US", "country": "United States", "language": "English"},
        {"name": "Paramount+", "countryCode": "US", "country": "United States", "language": "English", "type": "ott"},
        {"name": "Univision", "countryCode": "US", "country": "United States", "language": "Spanish"},
        {"name": "Sony Sports Ten 1", "countryCode": "IN", "country": "India", "language": "English"},
        {"name": "Sony Sports Ten 2", "countryCode": "IN", "country": "India", "language": "English"},
        {"name": "Sony Sports Ten 5", "countryCode": "IN", "country": "India", "language": "English"},
        {"name": "SuperSport Football", "countryCode": "ZA", "country": "South Africa", "language": "English"},
        {"name": "Stan Sport", "countryCode": "AU", "country": "Australia", "language": "English"},
        {"name": "beIN Sports 1", "countryCode": "QA", "country": "Middle East", "language": "Arabic"},
        {"name": "Movistar Liga de Campeones", "countryCode": "ES", "country": "Spain", "language": "Spanish"},
        {"name": "DAZN 1", "countryCode": "DE", "country": "Germany", "language": "German"},
    ],
    "europa league": [
        {"name": "TNT Sports 1", "countryCode": "GB", "country": "United Kingdom", "language": "English"},
        {"name": "TNT Sports 2", "countryCode": "GB", "country": "United Kingdom", "language": "English"},
        {"name": "Paramount+", "countryCode": "US", "country": "United States", "language": "English", "type": "ott"},
        {"name": "Sony Sports Ten 2", "countryCode": "IN", "country": "India", "language": "English"},
        {"name": "SuperSport Football", "countryCode": "ZA", "country": "South Africa", "language": "English"},
        {"name": "Movistar Liga de Campeones", "countryCode": "ES", "country": "Spain", "language": "Spanish"},
    ],
    "conference league": [
        {"name": "TNT Sports 2", "countryCode": "GB", "country": "United Kingdom", "language": "English"},
        {"name": "TNT Sports 3", "countryCode": "GB", "country": "United Kingdom", "language": "English"},
        {"name": "Paramount+", "countryCode": "US", "country": "United States", "language": "English", "type": "ott"},
        {"name": "Sony Sports Ten 5", "countryCode": "IN", "country": "India", "language": "English"},
        {"name": "SuperSport Football", "countryCode": "ZA", "country": "South Africa", "language": "English"},
    ],
    "uefa super cup": [
        {"name": "TNT Sports 1", "countryCode": "GB", "country": "United Kingdom", "language": "English"},
        {"name": "CBS Sports Network", "countryCode": "US", "country": "United States", "language": "English"},
        {"name": "Paramount+", "countryCode": "US", "country": "United States", "language": "English", "type": "ott"},
        {"name": "Sony Sports Ten 1", "countryCode": "IN", "country": "India", "language": "English"},
        {"name": "SuperSport Football", "countryCode": "ZA", "country": "South Africa", "language": "English"},
    ],
    "fifa club world cup": [
        {"name": "TNT Sports 1", "countryCode": "GB", "country": "United Kingdom", "language": "English"},
        {"name": "FOX Sports 1", "countryCode": "US", "country": "United States", "language": "English"},
        {"name": "DAZN", "countryCode": "GB", "country": "Worldwide", "language": "English", "type": "ott"},
        {"name": "beIN Sports 1", "countryCode": "QA", "country": "Middle East", "language": "Arabic"},
        {"name": "SuperSport Football", "countryCode": "ZA", "country": "South Africa", "language": "English"},
    ],
    "copa libertadores": [
        {"name": "beIN Sports 1", "countryCode": "US", "country": "United States", "language": "Spanish/English"},
        {"name": "beIN Sports en Español", "countryCode": "US", "country": "United States", "language": "Spanish"},
        {"name": "ESPN 4", "countryCode": "BR", "country": "Brazil", "language": "Portuguese"},
        {"name": "Star+", "countryCode": "AR", "country": "South America", "language": "Spanish", "type": "ott"},
        {"name": "Paramount+", "countryCode": "BR", "country": "Brazil", "language": "Portuguese", "type": "ott"},
    ],
    "afc champions league": [
        {"name": "SSC 1 HD", "countryCode": "SA", "country": "Saudi Arabia", "language": "Arabic"},
        {"name": "beIN Sports AFC", "countryCode": "QA", "country": "Middle East", "language": "Arabic"},
        {"name": "CBS Sports Golazo", "countryCode": "US", "country": "United States", "language": "English"},
        {"name": "Paramount+", "countryCode": "US", "country": "United States", "language": "English", "type": "ott"},
        {"name": "FanCode", "countryCode": "IN", "country": "India", "language": "English", "type": "ott"},
    ],

    # -------------------------------------------------------------
    # 4. INTERNATIONAL TOURNAMENTS
    # -------------------------------------------------------------
    "world cup": [
        {"name": "BBC One", "countryCode": "GB", "country": "United Kingdom", "language": "English"},
        {"name": "ITV 1", "countryCode": "GB", "country": "United Kingdom", "language": "English"},
        {"name": "FOX", "countryCode": "US", "country": "United States", "language": "English"},
        {"name": "FOX Sports 1", "countryCode": "US", "country": "United States", "language": "English"},
        {"name": "Telemundo", "countryCode": "US", "country": "United States", "language": "Spanish"},
        {"name": "Sports18 1", "countryCode": "IN", "country": "India", "language": "English"},
        {"name": "JioCinema", "countryCode": "IN", "country": "India", "language": "English/Hindi", "type": "ott"},
        {"name": "SuperSport Grandstand", "countryCode": "ZA", "country": "South Africa", "language": "English"},
        {"name": "Optus Sport 1", "countryCode": "AU", "country": "Australia", "language": "English"},
        {"name": "beIN Sports MAX 1", "countryCode": "QA", "country": "Middle East", "language": "Arabic"},
    ],
    "euro": [
        {"name": "BBC One", "countryCode": "GB", "country": "United Kingdom", "language": "English"},
        {"name": "ITV 1", "countryCode": "GB", "country": "United Kingdom", "language": "English"},
        {"name": "FOX", "countryCode": "US", "country": "United States", "language": "English"},
        {"name": "FOX Sports 1", "countryCode": "US", "country": "United States", "language": "English"},
        {"name": "Sony Sports Ten 2", "countryCode": "IN", "country": "India", "language": "English"},
        {"name": "Sony Sports Ten 3", "countryCode": "IN", "country": "India", "language": "Hindi"},
        {"name": "SuperSport Premier League", "countryCode": "ZA", "country": "South Africa", "language": "English"},
        {"name": "Optus Sport 1", "countryCode": "AU", "country": "Australia", "language": "English"},
        {"name": "beIN Sports MAX 1", "countryCode": "QA", "country": "Middle East", "language": "Arabic"},
    ],
    "copa america": [
        {"name": "Premier Sports 1", "countryCode": "GB", "country": "United Kingdom", "language": "English"},
        {"name": "FOX", "countryCode": "US", "country": "United States", "language": "English"},
        {"name": "FOX Sports 1", "countryCode": "US", "country": "United States", "language": "English"},
        {"name": "Univision", "countryCode": "US", "country": "United States", "language": "Spanish"},
        {"name": "TUDN", "countryCode": "US", "country": "United States", "language": "Spanish"},
        {"name": "Sports18 1", "countryCode": "IN", "country": "India", "language": "English"},
        {"name": "SuperSport Football", "countryCode": "ZA", "country": "South Africa", "language": "English"},
        {"name": "Optus Sport 1", "countryCode": "AU", "country": "Australia", "language": "English"},
    ],
    "nations league": [
        {"name": "ITV 1", "countryCode": "GB", "country": "United Kingdom", "language": "English"},
        {"name": "Premier Sports 1", "countryCode": "GB", "country": "United Kingdom", "language": "English"},
        {"name": "FOX Sports 1", "countryCode": "US", "country": "United States", "language": "English"},
        {"name": "FOX Sports 2", "countryCode": "US", "country": "United States", "language": "English"},
        {"name": "Sony Sports Ten 2", "countryCode": "IN", "country": "India", "language": "English"},
        {"name": "SuperSport Football", "countryCode": "ZA", "country": "South Africa", "language": "English"},
    ],
    "africa cup of nations": [
        {"name": "Sky Sports Football", "countryCode": "GB", "country": "United Kingdom", "language": "English"},
        {"name": "BBC Three", "countryCode": "GB", "country": "United Kingdom", "language": "English"},
        {"name": "beIN Sports 1", "countryCode": "US", "country": "United States", "language": "English"},
        {"name": "beIN Sports en Español", "countryCode": "US", "country": "United States", "language": "Spanish"},
        {"name": "SuperSport Football", "countryCode": "ZA", "country": "South Africa", "language": "English"},
        {"name": "beIN Sports MAX 1", "countryCode": "QA", "country": "Middle East", "language": "Arabic"},
    ],

    # -------------------------------------------------------------
    # 5. BASKETBALL / NBA
    # -------------------------------------------------------------
    "nba": [
        {"name": "ABC", "countryCode": "US", "country": "United States", "language": "English"},
        {"name": "ESPN", "countryCode": "US", "country": "United States", "language": "English"},
        {"name": "ESPN 2", "countryCode": "US", "country": "United States", "language": "English"},
        {"name": "TNT", "countryCode": "US", "country": "United States", "language": "English"},
        {"name": "NBA TV", "countryCode": "US", "country": "United States", "language": "English"},
        {"name": "TNT Sports 1", "countryCode": "GB", "country": "United Kingdom", "language": "English"},
        {"name": "TNT Sports 2", "countryCode": "GB", "country": "United Kingdom", "language": "English"},
        {"name": "Sports18 1", "countryCode": "IN", "country": "India", "language": "English"},
        {"name": "JioCinema", "countryCode": "IN", "country": "India", "language": "English", "type": "ott"},
        {"name": "ESPN Australia", "countryCode": "AU", "country": "Australia", "language": "English"},
        {"name": "SuperSport Action", "countryCode": "ZA", "country": "South Africa", "language": "English"},
        {"name": "beIN Sports NBA", "countryCode": "QA", "country": "Middle East", "language": "English"},
    ],

    # -------------------------------------------------------------
    # 6. CRICKET
    # -------------------------------------------------------------
    "sri lanka": [
        {"name": "Sony Sports Ten 1", "countryCode": "IN", "country": "India", "language": "English"},
        {"name": "Sony Sports Ten 3", "countryCode": "IN", "country": "India", "language": "Hindi"},
        {"name": "Sony Sports Ten 5", "countryCode": "IN", "country": "India", "language": "English"},
        {"name": "Sony LIV", "countryCode": "IN", "country": "India", "language": "English", "type": "ott"},
        {"name": "Supreme TV", "countryCode": "LK", "country": "Sri Lanka", "language": "Sinhala/English"},
        {"name": "Ten Cricket", "countryCode": "LK", "country": "Sri Lanka", "language": "English"},
        {"name": "TNT Sports 1", "countryCode": "GB", "country": "United Kingdom", "language": "English"},
        {"name": "TNT Sports 2", "countryCode": "GB", "country": "United Kingdom", "language": "English"},
        {"name": "Willow Cricket", "countryCode": "US", "country": "United States", "language": "English"},
        {"name": "Willow Xtra", "countryCode": "US", "country": "United States", "language": "English"},
        {"name": "Fox Cricket", "countryCode": "AU", "country": "Australia", "language": "English"},
        {"name": "SuperSport Cricket", "countryCode": "ZA", "country": "South Africa", "language": "English"},
        {"name": "SuperSport Grandstand", "countryCode": "ZA", "country": "South Africa", "language": "English"},
        {"name": "Sky Sport 1 NZ", "countryCode": "NZ", "country": "New Zealand", "language": "English"},
        {"name": "A Sports HD", "countryCode": "PK", "country": "Pakistan", "language": "Urdu"},
        {"name": "T Sports", "countryCode": "BD", "country": "Bangladesh", "language": "Bengali"},
    ],
    "tour of england": [
        {"name": "Sky Sports Cricket", "countryCode": "GB", "country": "United Kingdom", "language": "English"},
        {"name": "Sky Sports Main Event", "countryCode": "GB", "country": "United Kingdom", "language": "English"},
        {"name": "Sony Sports Ten 1", "countryCode": "IN", "country": "India", "language": "English"},
        {"name": "Sony Sports Ten 5", "countryCode": "IN", "country": "India", "language": "English"},
        {"name": "Sony LIV", "countryCode": "IN", "country": "India", "language": "English", "type": "ott"},
        {"name": "Willow Cricket", "countryCode": "US", "country": "United States", "language": "English"},
        {"name": "Fox Cricket", "countryCode": "AU", "country": "Australia", "language": "English"},
        {"name": "SuperSport Cricket", "countryCode": "ZA", "country": "South Africa", "language": "English"},
    ],
    "cricket": [
        {"name": "Star Sports 1", "countryCode": "IN", "country": "India", "language": "English"},
        {"name": "Star Sports 1 Hindi", "countryCode": "IN", "country": "India", "language": "Hindi"},
        {"name": "Star Sports 2", "countryCode": "IN", "country": "India", "language": "English"},
        {"name": "JioCinema", "countryCode": "IN", "country": "India", "language": "Hindi/English", "type": "ott"},
        {"name": "Sports18 1", "countryCode": "IN", "country": "India", "language": "English"},
        {"name": "Sky Sports Cricket", "countryCode": "GB", "country": "United Kingdom", "language": "English"},
        {"name": "Sky Sports Main Event", "countryCode": "GB", "country": "United Kingdom", "language": "English"},
        {"name": "TNT Sports 1", "countryCode": "GB", "country": "United Kingdom", "language": "English"},
        {"name": "Willow Cricket", "countryCode": "US", "country": "United States", "language": "English"},
        {"name": "Willow Xtra", "countryCode": "US", "country": "United States", "language": "English"},
        {"name": "Fox Cricket", "countryCode": "AU", "country": "Australia", "language": "English"},
        {"name": "Channel 7", "countryCode": "AU", "country": "Australia", "language": "English"},
        {"name": "SuperSport Cricket", "countryCode": "ZA", "country": "South Africa", "language": "English"},
        {"name": "SuperSport Grandstand", "countryCode": "ZA", "country": "South Africa", "language": "English"},
        {"name": "A Sports HD", "countryCode": "PK", "country": "Pakistan", "language": "Urdu"},
        {"name": "Ten Sports", "countryCode": "PK", "country": "Pakistan", "language": "English"},
        {"name": "T Sports", "countryCode": "BD", "country": "Bangladesh", "language": "Bengali"},
        {"name": "GTV", "countryCode": "BD", "country": "Bangladesh", "language": "Bengali"},
        {"name": "Sky Sport 1 NZ", "countryCode": "NZ", "country": "New Zealand", "language": "English"},
    ],
    "ipl": [
        {"name": "Star Sports 1", "countryCode": "IN", "country": "India", "language": "English"},
        {"name": "Star Sports 1 Hindi", "countryCode": "IN", "country": "India", "language": "Hindi"},
        {"name": "Star Sports Select 1", "countryCode": "IN", "country": "India", "language": "English"},
        {"name": "JioCinema", "countryCode": "IN", "country": "India", "language": "Hindi/English", "type": "ott"},
        {"name": "Sky Sports Cricket", "countryCode": "GB", "country": "United Kingdom", "language": "English"},
        {"name": "Willow Cricket", "countryCode": "US", "country": "United States", "language": "English"},
        {"name": "Fox Cricket", "countryCode": "AU", "country": "Australia", "language": "English"},
        {"name": "SuperSport Cricket", "countryCode": "ZA", "country": "South Africa", "language": "English"},
    ],

    # -------------------------------------------------------------
    # 7. TENNIS
    # -------------------------------------------------------------
    "tennis": [
        {"name": "Tennis Channel", "countryCode": "US", "country": "United States", "language": "English"},
        {"name": "ESPN", "countryCode": "US", "country": "United States", "language": "English"},
        {"name": "ESPN 2", "countryCode": "US", "country": "United States", "language": "English"},
        {"name": "Sky Sports Tennis", "countryCode": "GB", "country": "United Kingdom", "language": "English"},
        {"name": "BBC One", "countryCode": "GB", "country": "United Kingdom", "language": "English"},
        {"name": "BBC Two", "countryCode": "GB", "country": "United Kingdom", "language": "English"},
        {"name": "Eurosport 1", "countryCode": "EU", "country": "Europe", "language": "English"},
        {"name": "Eurosport 2", "countryCode": "EU", "country": "Europe", "language": "English"},
        {"name": "Sony Sports Ten 2", "countryCode": "IN", "country": "India", "language": "English"},
        {"name": "Sony Sports Ten 5", "countryCode": "IN", "country": "India", "language": "English"},
        {"name": "Nine Network", "countryCode": "AU", "country": "Australia", "language": "English"},
        {"name": "Stan Sport", "countryCode": "AU", "country": "Australia", "language": "English"},
        {"name": "SuperSport Tennis", "countryCode": "ZA", "country": "South Africa", "language": "English"},
        {"name": "beIN Sports 6", "countryCode": "QA", "country": "Middle East", "language": "Arabic"},
    ],
    "wimbledon": [
        {"name": "BBC One", "countryCode": "GB", "country": "United Kingdom", "language": "English"},
        {"name": "BBC Two", "countryCode": "GB", "country": "United Kingdom", "language": "English"},
        {"name": "ESPN", "countryCode": "US", "country": "United States", "language": "English"},
        {"name": "ESPN 2", "countryCode": "US", "country": "United States", "language": "English"},
        {"name": "Tennis Channel", "countryCode": "US", "country": "United States", "language": "English"},
        {"name": "Star Sports Select 1", "countryCode": "IN", "country": "India", "language": "English"},
        {"name": "Nine Network", "countryCode": "AU", "country": "Australia", "language": "English"},
        {"name": "Eurosport 1", "countryCode": "EU", "country": "Europe", "language": "English"},
    ],
    "us open": [
        {"name": "ESPN", "countryCode": "US", "country": "United States", "language": "English"},
        {"name": "ESPN 2", "countryCode": "US", "country": "United States", "language": "English"},
        {"name": "Sky Sports Tennis", "countryCode": "GB", "country": "United Kingdom", "language": "English"},
        {"name": "Sony Sports Ten 2", "countryCode": "IN", "country": "India", "language": "English"},
        {"name": "Stan Sport", "countryCode": "AU", "country": "Australia", "language": "English"},
        {"name": "Eurosport 1", "countryCode": "EU", "country": "Europe", "language": "English"},
    ],
    "australian open": [
        {"name": "Nine Network", "countryCode": "AU", "country": "Australia", "language": "English"},
        {"name": "Stan Sport", "countryCode": "AU", "country": "Australia", "language": "English"},
        {"name": "ESPN", "countryCode": "US", "country": "United States", "language": "English"},
        {"name": "Eurosport 1", "countryCode": "EU", "country": "Europe", "language": "English"},
        {"name": "Sony Sports Ten 5", "countryCode": "IN", "country": "India", "language": "English"},
    ],
    "french open": [
        {"name": "France 2", "countryCode": "FR", "country": "France", "language": "French"},
        {"name": "France 3", "countryCode": "FR", "country": "France", "language": "French"},
        {"name": "NBC", "countryCode": "US", "country": "United States", "language": "English"},
        {"name": "Peacock", "countryCode": "US", "country": "United States", "language": "English", "type": "ott"},
        {"name": "Tennis Channel", "countryCode": "US", "country": "United States", "language": "English"},
        {"name": "Eurosport 1", "countryCode": "EU", "country": "Europe", "language": "English"},
        {"name": "Sony Sports Ten 2", "countryCode": "IN", "country": "India", "language": "English"},
        {"name": "Nine Network", "countryCode": "AU", "country": "Australia", "language": "English"},
    ],

    # -------------------------------------------------------------
    # 8. AMERICAN FOOTBALL / NFL
    # -------------------------------------------------------------
    "nfl": [
        {"name": "CBS", "countryCode": "US", "country": "United States", "language": "English"},
        {"name": "FOX", "countryCode": "US", "country": "United States", "language": "English"},
        {"name": "NBC", "countryCode": "US", "country": "United States", "language": "English"},
        {"name": "ESPN", "countryCode": "US", "country": "United States", "language": "English"},
        {"name": "ABC", "countryCode": "US", "country": "United States", "language": "English"},
        {"name": "NFL Network", "countryCode": "US", "country": "United States", "language": "English"},
        {"name": "NFL RedZone", "countryCode": "US", "country": "United States", "language": "English"},
        {"name": "Amazon Prime Video", "countryCode": "US", "country": "United States", "language": "English", "type": "ott"},
        {"name": "Peacock", "countryCode": "US", "country": "United States", "language": "English", "type": "ott"},
        {"name": "Paramount+", "countryCode": "US", "country": "United States", "language": "English", "type": "ott"},
        {"name": "Sky Sports NFL", "countryCode": "GB", "country": "United Kingdom", "language": "English"},
        {"name": "Sky Sports Main Event", "countryCode": "GB", "country": "United Kingdom", "language": "English"},
        {"name": "Channel 5", "countryCode": "GB", "country": "United Kingdom", "language": "English"},
        {"name": "Star Sports Select 2", "countryCode": "IN", "country": "India", "language": "English"},
        {"name": "JioCinema", "countryCode": "IN", "country": "India", "language": "English", "type": "ott"},
        {"name": "TSN 1", "countryCode": "CA", "country": "Canada", "language": "English"},
        {"name": "CTV", "countryCode": "CA", "country": "Canada", "language": "English"},
        {"name": "ESPN Australia", "countryCode": "AU", "country": "Australia", "language": "English"},
        {"name": "7mate", "countryCode": "AU", "country": "Australia", "language": "English"},
        {"name": "SuperSport Action", "countryCode": "ZA", "country": "South Africa", "language": "English"},
        {"name": "RTL", "countryCode": "DE", "country": "Germany", "language": "German"},
        {"name": "DAZN 1", "countryCode": "DE", "country": "Germany", "language": "German"},
    ],

    # -------------------------------------------------------------
    # 9. FORMULA 1 / MOTORSPORT
    # -------------------------------------------------------------
    "formula 1": [
        {"name": "Sky Sports F1", "countryCode": "GB", "country": "United Kingdom", "language": "English"},
        {"name": "Sky Sports Main Event", "countryCode": "GB", "country": "United Kingdom", "language": "English"},
        {"name": "Channel 4", "countryCode": "GB", "country": "United Kingdom", "language": "English"},
        {"name": "ESPN", "countryCode": "US", "country": "United States", "language": "English"},
        {"name": "ESPN 2", "countryCode": "US", "country": "United States", "language": "English"},
        {"name": "ABC", "countryCode": "US", "country": "United States", "language": "English"},
        {"name": "FanCode", "countryCode": "IN", "country": "India", "language": "English", "type": "ott"},
        {"name": "Fox Sports 506", "countryCode": "AU", "country": "Australia", "language": "English"},
        {"name": "TSN 5", "countryCode": "CA", "country": "Canada", "language": "English"},
        {"name": "SuperSport Motorsport", "countryCode": "ZA", "country": "South Africa", "language": "English"},
        {"name": "Sky Sport F1 HD", "countryCode": "DE", "country": "Germany", "language": "German"},
        {"name": "Sky Sport F1", "countryCode": "IT", "country": "Italy", "language": "Italian"},
        {"name": "DAZN F1", "countryCode": "ES", "country": "Spain", "language": "Spanish"},
        {"name": "Canal+", "countryCode": "FR", "country": "France", "language": "French"},
        {"name": "Viaplay 1", "countryCode": "NL", "country": "Netherlands", "language": "Dutch"},
        {"name": "beIN Sports 1", "countryCode": "QA", "country": "Middle East", "language": "Arabic"},
    ],
    "f1": [
        {"name": "Sky Sports F1", "countryCode": "GB", "country": "United Kingdom", "language": "English"},
        {"name": "ESPN", "countryCode": "US", "country": "United States", "language": "English"},
        {"name": "FanCode", "countryCode": "IN", "country": "India", "language": "English", "type": "ott"},
        {"name": "Fox Sports 506", "countryCode": "AU", "country": "Australia", "language": "English"},
        {"name": "SuperSport Motorsport", "countryCode": "ZA", "country": "South Africa", "language": "English"},
        {"name": "Sky Sport F1 HD", "countryCode": "DE", "country": "Germany", "language": "German"},
        {"name": "Canal+", "countryCode": "FR", "country": "France", "language": "French"},
    ],
}


def get_curated_broadcasters_for_event(
    sport: str,
    league_name: Optional[str] = None,
    home_name: Optional[str] = None,
    away_name: Optional[str] = None,
) -> List[BroadcasterInfo]:
    """
    Returns curated, verified TV broadcast channels matching the given league/sport/tournament.
    """
    matched_entries: List[Dict[str, Any]] = []
    league_clean = (league_name or "").lower()
    sport_clean = (sport or "").lower()

    # Check for specific league/cup matches first
    for key, broadcasters in LEAGUE_BROADCASTER_MAPPINGS.items():
        # Match either exact substring or punctuation-stripped substring (e.g. "u.s. open cup" -> "us open cup")
        key_stripped = key.replace(".", "").replace("-", " ")
        league_stripped = league_clean.replace(".", "").replace("-", " ")
        if key in league_clean or key_stripped in league_stripped:
            matched_entries.extend(broadcasters)
            break

    # If no specific league match, fallback to sport generic list
    if not matched_entries:
        if "cricket" in sport_clean or "cricket" in league_clean:
            matched_entries.extend(LEAGUE_BROADCASTER_MAPPINGS["cricket"])
        elif "basket" in sport_clean or "nba" in league_clean:
            matched_entries.extend(LEAGUE_BROADCASTER_MAPPINGS["nba"])
        elif "tennis" in sport_clean or "tennis" in league_clean:
            matched_entries.extend(LEAGUE_BROADCASTER_MAPPINGS["tennis"])
        elif "soccer" in sport_clean or "football" in sport_clean:
            # Default to top general football broadcasters
            matched_entries.extend(LEAGUE_BROADCASTER_MAPPINGS["premier league"][:6])
            matched_entries.extend(LEAGUE_BROADCASTER_MAPPINGS["champions league"][:4])

    # Convert to BroadcasterInfo objects and deduplicate by normalized name + country
    results: List[BroadcasterInfo] = []
    seen: set = set()

    for item in matched_entries:
        name = item["name"]
        norm = normalize_channel_name(name)
        country_code = item.get("countryCode", "US")
        key = (norm, country_code)

        if key in seen:
            continue
        seen.add(key)

        results.append(
            BroadcasterInfo(
                name=name,
                normalizedName=norm,
                countryCode=country_code,
                country=item.get("country", "International"),
                type=item.get("type", "tv"),
                language=item.get("language", "English"),
                source="curated_catalog",
            )
        )

    return results
