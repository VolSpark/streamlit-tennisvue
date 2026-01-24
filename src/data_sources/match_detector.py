"""
Match data detection and extraction utilities.
Helps identify and extract player info, scores, and stats from various tennis sites.
"""

import re
from typing import Optional, Tuple, Dict, Any, List


class MatchDetector:
    """Detect and extract match information from URLs and page content."""
    
    # Pattern definitions for different tournaments
    TOURNAMENT_PATTERNS = {
        "ausopen": {
            "name": "Australian Open",
            "domain": "ausopen.com",
            "url_pattern": r"/match/(\d+)-([^-]+)-vs-([^-]+)-([a-z0-9]+)",
            "player_separator": "vs",
        },
        "wimbledon": {
            "name": "Wimbledon",
            "domain": "wimbledon.com",
            "url_pattern": r"/match/([^/]+)/([^/]+)/(.+)",
            "player_separator": "vs",
        },
        "usopen": {
            "name": "US Open",
            "domain": "usopen.com",
            "url_pattern": r"/match/(.+)-(.+)",
            "player_separator": "vs",
        },
        "rolandgarros": {
            "name": "Roland Garros",
            "domain": "rolandgarros.com",
            "url_pattern": r"/match/(.+)/(.+)/(.+)",
            "player_separator": "vs",
        },
        "atptour": {
            "name": "ATP Tour",
            "domain": "atptour.com",
            "url_pattern": r"/match/(.+)",
            "player_separator": "vs",
        },
        "wtatour": {
            "name": "WTA Tour",
            "domain": "wtatour.com",
            "url_pattern": r"/match/(.+)",
            "player_separator": "vs",
        },
    }
    
    # Serve statistic patterns
    STAT_PATTERNS = {
        "first_serve_in": [
            r'(?:first\s+)?serve\s+in[:\s]+(\d+(?:\.\d+)?)\s*%',
            r'(\d+(?:\.\d+)?)\s*%[:\s]+(?:first\s+)?serve\s+in',
            r'1st\s+serve\s+in[:\s]+(\d+(?:\.\d+)?)\s*%',
            r'first\s+in[:\s]+(\d+(?:\.\d+)?)\s*%',
        ],
        "first_serve_points_won": [
            r'first\s+serve\s+points?\s+won[:\s]+(\d+(?:\.\d+)?)\s*%',
            r'(\d+(?:\.\d+)?)\s*%[:\s]+first\s+serve\s+points?\s+won',
            r'1st\s+serve\s+pts?\s+won[:\s]+(\d+(?:\.\d+)?)\s*%',
            r'first\s+serve\s+(?:winning|win)[:\s]+(\d+(?:\.\d+)?)\s*%',
        ],
        "second_serve_points_won": [
            r'second\s+serve\s+points?\s+won[:\s]+(\d+(?:\.\d+)?)\s*%',
            r'(\d+(?:\.\d+)?)\s*%[:\s]+second\s+serve\s+points?\s+won',
            r'2nd\s+serve\s+pts?\s+won[:\s]+(\d+(?:\.\d+)?)\s*%',
            r'second\s+serve\s+(?:winning|win)[:\s]+(\d+(?:\.\d+)?)\s*%',
        ],
        "aces": [
            r'(\d+)\s+aces?',
            r'aces?[:\s]+(\d+)',
        ],
        "double_faults": [
            r'(\d+)\s+double\s+faults?',
            r'double\s+faults?[:\s]+(\d+)',
        ],
        "break_points": [
            r'(\d+)/(\d+)\s+break\s+points?',
            r'break\s+points?[:\s]+(\d+)/(\d+)',
        ],
    }
    
    @staticmethod
    def identify_tournament(url: str) -> Optional[Dict[str, str]]:
        """Identify which tournament the URL belongs to."""
        url_lower = url.lower()
        for key, pattern in MatchDetector.TOURNAMENT_PATTERNS.items():
            if pattern["domain"] in url_lower:
                return {
                    "tournament_id": key,
                    "tournament_name": pattern["name"],
                    "domain": pattern["domain"],
                }
        return None
    
    @staticmethod
    def extract_player_names(url: str) -> Tuple[Optional[str], Optional[str]]:
        """Extract player names from URL."""
        # Try Australian Open pattern first (most common format)
        match = re.search(r'/match/\d+-([^-]+)-vs-([^-]+)-[a-z0-9]+', url)
        if match:
            p1 = _clean_player_name(match.group(1))
            p2 = _clean_player_name(match.group(2))
            return p1, p2
        
        # Try other patterns
        match = re.search(r'/match/([^/]+)-vs-([^/]+)', url)
        if match:
            p1 = _clean_player_name(match.group(1))
            p2 = _clean_player_name(match.group(2))
            return p1, p2
        
        # Try generic pattern
        match = re.search(r'/match/([^/]+)/([^/]+)', url)
        if match:
            p1 = _clean_player_name(match.group(1))
            p2 = _clean_player_name(match.group(2))
            return p1, p2
        
        return None, None
    
    @staticmethod
    def extract_stats_from_text(text: str) -> Dict[str, Any]:
        """Extract tennis statistics using pattern matching."""
        stats = {}
        
        # Search for each stat type
        for stat_key, patterns in MatchDetector.STAT_PATTERNS.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    try:
                        if len(match.groups()) == 1:
                            value = float(match.group(1))
                            if value <= 100:  # It's a percentage
                                stats[stat_key] = value / 100
                            else:
                                stats[stat_key] = value
                        elif len(match.groups()) == 2 and stat_key == "break_points":
                            # Handle break points as fraction
                            stats[stat_key] = f"{match.group(1)}/{match.group(2)}"
                        break  # Found this stat, move to next
                    except (ValueError, IndexError):
                        continue
        
        return stats
    
    @staticmethod
    def detect_live_pages(html_content: str) -> List[Dict[str, str]]:
        """
        Detect available match pages/tabs (e.g., Live, Statistics, Head-to-Head).
        Returns list of available page options.
        """
        pages = []
        
        # Look for common page tabs/links
        patterns = {
            "live": [r'live(?:\s+)?(?:score|match)?', r'(?:watch|view)\s+live'],
            "statistics": [r'statistics', r'stats'],
            "head_to_head": [r'head\s+to\s+head', r'h2h'],
            "set_by_set": [r'set\s+by\s+set', r'game\s+by\s+game'],
            "timeline": [r'timeline', r'play\s+by\s+play'],
        }
        
        for page_type, patterns_list in patterns.items():
            for pattern in patterns_list:
                if re.search(pattern, html_content, re.IGNORECASE):
                    pages.append({
                        "type": page_type,
                        "label": page_type.replace("_", " ").title(),
                    })
                    break  # Found this page type, move to next
        
        return pages
    
    @staticmethod
    def normalize_stat_value(key: str, value: Any) -> Any:
        """Normalize statistic values to expected format."""
        if not isinstance(value, (int, float)):
            try:
                value = float(value)
            except (ValueError, TypeError):
                return None
        
        # Map key names to standard format
        key_lower = key.lower()
        
        # Percentage stats should be 0-1
        if "pct" in key_lower or "percent" in key_lower or "%" in str(value):
            if value > 1:
                value = value / 100
            return max(0, min(1, value))
        
        # Integer stats
        if "count" in key_lower or any(x in key_lower for x in ["aces", "fault", "break", "winner"]):
            return int(value)
        
        return value


def _clean_player_name(name: str) -> str:
    """Clean player name extracted from URL."""
    # Replace hyphens with spaces and title case
    name = name.replace("-", " ").replace("_", " ")
    # Handle special cases (like McDonald-Kenin)
    words = name.split()
    cleaned = []
    for word in words:
        if len(word) > 1:
            cleaned.append(word.capitalize())
        else:
            cleaned.append(word.upper())
    return " ".join(cleaned)


def extract_score_from_page(html_content: str) -> Optional[Dict[str, Any]]:
    """
    Extract current match score from page content.
    Returns sets, games, and points if available.
    """
    score_info = {}
    
    # Pattern for set scores (e.g., "6-4 3-2")
    set_pattern = r'(\d)-(\d)\s+(\d)-(\d)'
    match = re.search(set_pattern, html_content)
    if match:
        score_info["set1_a"] = int(match.group(1))
        score_info["set1_b"] = int(match.group(2))
        score_info["games_a"] = int(match.group(3))
        score_info["games_b"] = int(match.group(4))
    
    # Pattern for point scores
    point_pattern = r'(?:Point[:\s]+)?(\d+|0|15|30|40|AD)[:\s]+(\d+|0|15|30|40|AD)'
    match = re.search(point_pattern, html_content, re.IGNORECASE)
    if match:
        score_info["point_a"] = match.group(1)
        score_info["point_b"] = match.group(2)
    
    return score_info if score_info else None
