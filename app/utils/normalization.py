import re
from difflib import SequenceMatcher
from typing import Set

# Common tags, codecs, resolutions and IPTV artifacts to strip from channel names
COUNTRY_PREFIX_PATTERNS = [
    r"^\[[A-Z0-9\s\-]+\]\s*",
    r"^\([A-Z0-9\s\-]+\)\s*",
    r"^\|[A-Z0-9\s\-]+\|\s*",
    r"^[A-Z]{2,3}\s*[\:\|\-\/]\s*",
    r"^(uk|us|usa|ca|can|aus|nz|in|ind|za|pk|bd|fr|es|de|it|pt|ar|latam)\s*[\:\|\-\/]\s*",
    r"^(sport|sports|tv|live|stream)\s*[\:\|\-\/]\s*",
]

QUALITY_AND_CODEC_PATTERNS = [
    r"\b(4k|8k|uhd|fhd|hd|sd|1080p|1080i|720p|576p|480p|360p)\b",
    r"\b(50fps|60fps|25fps|30fps|hdr|hdr10|dolby\s*vision)\b",
    r"\b(hevc|h\.?265|h\.?264|avc|x264|x265)\b",
    r"\b(raw|vip|premium|direct|backup|feed|multi|multisub|alt|backup\d*|live)\b",
    r"\b(5\.1|7\.1|stereo|mono|audio\s*\d*)\b",
]

# Aliases and synonyms for common sports broadcasters
CHANNEL_SYNONYMS = {
    "tnt sports 1": ["bt sport 1", "tnt 1"],
    "tnt sports 2": ["bt sport 2", "tnt 2"],
    "tnt sports 3": ["bt sport 3", "tnt 3"],
    "tnt sports 4": ["bt sport 4", "tnt 4"],
    "tnt sports ultimate": ["bt sport ultimate", "tnt ultimate"],
    "sky sports main event": ["sky main event", "sky sports me"],
    "sky sports premier league": ["sky premier league", "sky sports pl"],
    "sky sports football": ["sky football"],
    "sky sports cricket": ["sky cricket"],
    "sky sports f1": ["sky formula 1"],
    "sky sports action": ["sky action"],
    "sky sports arena": ["sky arena"],
    "sky sports golf": ["sky golf"],
    "sky sports tennis": ["sky tennis"],
    "usa network": ["usa net", "usa"],
    "nbc sports": ["nbcsn", "nbc"],
    "cbs sports network": ["cbssn"],
    "espn": ["espn 1", "espn usa"],
    "espn 2": ["espn2"],
    "fox sports 1": ["fs1"],
    "fox sports 2": ["fs2"],
    "willow cricket": ["willow", "willow hd", "willow tv", "willow xtra"],
    "star sports 1": ["star sports 1 hd", "star sports 1 english"],
    "star sports 2": ["star sports 2 hd"],
    "star sports select 1": ["star select 1"],
    "star sports select 2": ["star select 2"],
    "sony sports ten 1": ["sony ten 1", "ten 1"],
    "sony sports ten 2": ["sony ten 2", "ten 2"],
    "sony sports ten 3": ["sony ten 3", "ten 3"],
    "sony sports ten 5": ["sony ten 5", "ten 5", "sony six"],
    "supersport grandstand": ["supersport grandstand hd", "ss grandstand"],
    "supersport premier league": ["ss premier league", "ss pl", "supersport pl"],
    "supersport football": ["ss football"],
    "supersport cricket": ["ss cricket"],
    "bein sports 1": ["bein 1", "bein sports 1 hd"],
    "bein sports 2": ["bein 2", "bein sports 2 hd"],
    "bein sports 3": ["bein 3", "bein sports 3 hd"],
    "optus sport 1": ["optus 1", "optus sport"],
    "stan sport": ["stan"],
    "astro superSport": ["astro supersport 1"],
}


def normalize_channel_name(name: str) -> str:
    """
    Normalizes a channel name by removing resolution tags, codecs, country prefixes,
    punctuation, and duplicate whitespace while preserving distinctive numbers and words.
    
    Examples:
        "UK | SKY SPORTS MAIN EVENT FHD" -> "sky sports main event"
        "[UK] TNT Sports 1 4K UHD" -> "tnt sports 1"
        "USA NETWORK HD" -> "usa network"
        "IN - Star Sports 1 HD (Hindi)" -> "star sports 1 hindi"
        "US: NBC Sports 1080P 60FPS HEVC" -> "nbc sports"
    """
    if not name:
        return ""

    text = name.strip()

    # Step 1: Strip leading country brackets/separators BEFORE punctuation stripping
    for pattern in COUNTRY_PREFIX_PATTERNS:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE).strip()

    # Step 2: Replace separators/punctuation like |, :, -, _, /, +, • with spaces
    text = re.sub(r"[\|\:\-\_\/\+\•\*\~\#\(\)\[\]\{\}]", " ", text)

    # Step 3: Remove resolution, codec, and IPTV noise words
    for pattern in QUALITY_AND_CODEC_PATTERNS:
        text = re.sub(pattern, " ", text, flags=re.IGNORECASE)

    # Step 4: Convert to lowercase and normalize spaces
    text = text.lower()
    text = re.sub(r"\s+", " ", text).strip()

    return text


def get_token_set(text: str) -> Set[str]:
    """Get clean token set from normalized text."""
    return set(text.split())


def channel_similarity(broadcaster_name: str, playlist_channel_name: str) -> float:
    """
    Calculates a similarity score between a canonical broadcaster name and
    a playlist channel name.
    
    Returns:
        float between 0.0 and 1.0.
    """
    norm_b = normalize_channel_name(broadcaster_name)
    norm_p = normalize_channel_name(playlist_channel_name)

    if not norm_b or not norm_p:
        return 0.0

    # 1. Exact match after normalization
    if norm_b == norm_p:
        return 1.0

    # 2. Check alias dictionary
    if norm_b in CHANNEL_SYNONYMS:
        if norm_p in CHANNEL_SYNONYMS[norm_b]:
            return 0.98
        for alias in CHANNEL_SYNONYMS[norm_b]:
            if alias == norm_p:
                return 0.98

    # 3. Token-based analysis
    tokens_b = get_token_set(norm_b)
    tokens_p = get_token_set(norm_p)

    if not tokens_b or not tokens_p:
        return 0.0

    # Check for crucial numeric/channel differentiation
    # (e.g. "Sky Sports 1" vs "Sky Sports 2" MUST NOT match)
    digits_b = {t for t in tokens_b if t.isdigit()}
    digits_p = {t for t in tokens_p if t.isdigit()}
    if digits_b and digits_p and digits_b != digits_p:
        return 0.0

    # If broadcaster has a digit that channel doesn't have, penalize heavily
    if digits_b and not digits_p:
        return 0.3

    # Intersect tokens
    intersection = tokens_b.intersection(tokens_p)
    union = tokens_b.union(tokens_p)

    # Jaccard index
    jaccard = len(intersection) / len(union) if union else 0.0

    # Broadcaster coverage: fraction of broadcaster words found in playlist channel
    broadcaster_coverage = len(intersection) / len(tokens_b) if tokens_b else 0.0

    # Sequence Matcher on raw normalized strings
    seq_ratio = SequenceMatcher(None, norm_b, norm_p).ratio()

    # Substring bonus: if the entire broadcaster string is inside the channel name
    if norm_b in norm_p:
        extra_len = len(norm_p) - len(norm_b)
        penalty = min(0.15, extra_len * 0.01)
        score = max(0.95 - penalty, 0.80)
        return min(1.0, max(score, seq_ratio))

    if norm_p in norm_b:
        coverage = len(norm_p) / len(norm_b)
        return round(0.75 * coverage + 0.25 * seq_ratio, 3)

    # If all tokens of broadcaster are present in channel
    if broadcaster_coverage == 1.0:
        return max(0.92, (0.5 * broadcaster_coverage) + (0.5 * seq_ratio))

    # Weighted combination
    composite_score = (broadcaster_coverage * 0.5) + (jaccard * 0.2) + (seq_ratio * 0.3)
    return round(min(1.0, max(0.0, composite_score)), 3)
