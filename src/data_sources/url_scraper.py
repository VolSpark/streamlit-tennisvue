"""URL scraping for match stats (gracefully handles failures)."""

import json
import re
from typing import Optional, Dict, Any, Tuple, List
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from .match_detector import MatchDetector, extract_score_from_page


def fetch_match_stats_from_url(url: str, timeout: int = 10) -> Optional[Dict[str, Any]]:
    """
    Fetch match stats from a public tennis match URL.
    Intelligently detects site and uses appropriate parser.
    Returns dict of extracted stats, or None if not available.
    Gracefully handles failures.
    """
    try:
        if not url or not url.strip():
            return None

        # Determine site type
        domain = _get_domain(url)
        
        # Route to appropriate parser
        if "ausopen" in domain or "australianopen" in domain:
            return _parse_ausopen(url, timeout)
        elif "wimbledon" in domain:
            return _parse_wimbledon(url, timeout)
        elif "usta.com" in domain or "usopen" in domain:
            return _parse_us_open(url, timeout)
        elif "rolandgarros" in domain:
            return _parse_roland_garros(url, timeout)
        elif "atptour" in domain or "wtatour" in domain:
            return _parse_atp_wta(url, timeout)
        else:
            # Generic fallback parser
            return _parse_generic(url, timeout)

    except Exception as e:
        print(f"Error in fetch_match_stats_from_url: {e}")
        return None


def get_available_match_pages(url: str, timeout: int = 10) -> Optional[List[Dict[str, str]]]:
    """
    Detect available match pages/tabs (Live, Statistics, Head-to-Head, etc.)
    Returns list of available pages with their information.
    """
    try:
        html = _get_page_content(url, timeout)
        if html:
            pages = MatchDetector.detect_live_pages(html)
            return pages if pages else []
        return None
    except Exception as e:
        print(f"Error detecting match pages: {e}")
        return None


def _get_domain(url: str) -> str:
    """Extract domain from URL."""
    try:
        parsed = urlparse(url)
        return parsed.netloc.lower()
    except:
        return ""


def _get_page_content(url: str, timeout: int = 10) -> Optional[str]:
    """Fetch page content with appropriate headers."""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Referer": "https://www.google.com/",
        }
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"Error fetching page: {e}")
        return None


def _extract_player_names_from_url(url: str) -> Tuple[Optional[str], Optional[str]]:
    """Extract player names from URL pattern using MatchDetector."""
    return MatchDetector.extract_player_names(url)


def _parse_ausopen(url: str, timeout: int = 10) -> Optional[Dict[str, Any]]:
    """Parse Australian Open match URL."""
    html = _get_page_content(url, timeout)
    if not html:
        return None

    soup = BeautifulSoup(html, "html.parser")
    stats = {}

    # Extract player names from URL
    p1_name, p2_name = _extract_player_names_from_url(url)
    if p1_name:
        stats["player_a_name"] = p1_name
    if p2_name:
        stats["player_b_name"] = p2_name

    # Look for JSON in script tags (AO uses React/data embeds)
    for script in soup.find_all("script", {"type": "application/json"}):
        if script.string:
            try:
                data = json.loads(script.string)
                extracted = _extract_ausopen_stats(data)
                if extracted:
                    stats.update(extracted)
            except json.JSONDecodeError:
                continue

    # Look for common stat patterns in text content
    page_text = soup.get_text()
    
    # Pattern matching for serve stats
    stats.update(_extract_patterns_from_text(page_text))
    
    # Look for stat tables
    table_stats = _extract_stats_from_tables(soup)
    stats.update(table_stats)

    return stats if stats else None


def _parse_wimbledon(url: str, timeout: int = 10) -> Optional[Dict[str, Any]]:
    """Parse Wimbledon match URL."""
    html = _get_page_content(url, timeout)
    if not html:
        return None

    soup = BeautifulSoup(html, "html.parser")
    stats = {}

    # Extract player names from URL
    p1_name, p2_name = _extract_player_names_from_url(url)
    if p1_name:
        stats["player_a_name"] = p1_name
    if p2_name:
        stats["player_b_name"] = p2_name

    # Wimbledon specific selectors
    for script in soup.find_all("script"):
        if script.string and "stats" in script.string.lower():
            try:
                data = json.loads(script.string)
                extracted = _extract_wimbledon_stats(data)
                if extracted:
                    stats.update(extracted)
            except json.JSONDecodeError:
                continue

    table_stats = _extract_stats_from_tables(soup)
    stats.update(table_stats)

    return stats if stats else None


def _parse_us_open(url: str, timeout: int = 10) -> Optional[Dict[str, Any]]:
    """Parse US Open match URL."""
    html = _get_page_content(url, timeout)
    if not html:
        return None

    soup = BeautifulSoup(html, "html.parser")
    stats = {}

    # Extract player names
    p1_name, p2_name = _extract_player_names_from_url(url)
    if p1_name:
        stats["player_a_name"] = p1_name
    if p2_name:
        stats["player_b_name"] = p2_name

    # Look for data in various formats
    for script in soup.find_all("script"):
        if script.string:
            try:
                if script.string.strip().startswith('{') or script.string.strip().startswith('['):
                    data = json.loads(script.string)
                    extracted = _extract_generic_stats(data)
                    if extracted:
                        stats.update(extracted)
            except json.JSONDecodeError:
                continue

    table_stats = _extract_stats_from_tables(soup)
    stats.update(table_stats)

    return stats if stats else None


def _parse_roland_garros(url: str, timeout: int = 10) -> Optional[Dict[str, Any]]:
    """Parse Roland Garros match URL."""
    html = _get_page_content(url, timeout)
    if not html:
        return None

    soup = BeautifulSoup(html, "html.parser")
    stats = {}

    # Extract player names
    p1_name, p2_name = _extract_player_names_from_url(url)
    if p1_name:
        stats["player_a_name"] = p1_name
    if p2_name:
        stats["player_b_name"] = p2_name

    # Look for JSON data
    for script in soup.find_all("script"):
        if script.string:
            try:
                data = json.loads(script.string)
                extracted = _extract_generic_stats(data)
                if extracted:
                    stats.update(extracted)
            except json.JSONDecodeError:
                continue

    table_stats = _extract_stats_from_tables(soup)
    stats.update(table_stats)

    return stats if stats else None


def _parse_atp_wta(url: str, timeout: int = 10) -> Optional[Dict[str, Any]]:
    """Parse ATP/WTA tour match URL."""
    html = _get_page_content(url, timeout)
    if not html:
        return None

    soup = BeautifulSoup(html, "html.parser")
    stats = {}

    # Extract player names
    p1_name, p2_name = _extract_player_names_from_url(url)
    if p1_name:
        stats["player_a_name"] = p1_name
    if p2_name:
        stats["player_b_name"] = p2_name

    # ATP/WTA specific parsing
    for script in soup.find_all("script"):
        if script.string:
            try:
                data = json.loads(script.string)
                extracted = _extract_generic_stats(data)
                if extracted:
                    stats.update(extracted)
            except json.JSONDecodeError:
                continue

    table_stats = _extract_stats_from_tables(soup)
    stats.update(table_stats)

    return stats if stats else None


def _parse_generic(url: str, timeout: int = 10) -> Optional[Dict[str, Any]]:
    """Generic fallback parser for unknown sites."""
    html = _get_page_content(url, timeout)
    if not html:
        return None

    soup = BeautifulSoup(html, "html.parser")
    stats = {}

    # Try to extract player names
    p1_name, p2_name = _extract_player_names_from_url(url)
    if p1_name:
        stats["player_a_name"] = p1_name
    if p2_name:
        stats["player_b_name"] = p2_name

    # Look for any JSON data
    for script in soup.find_all("script"):
        if script.string:
            try:
                # Check if it looks like JSON
                cleaned = script.string.strip()
                if cleaned.startswith('{') or cleaned.startswith('['):
                    data = json.loads(cleaned)
                    extracted = _extract_generic_stats(data)
                    if extracted:
                        stats.update(extracted)
            except json.JSONDecodeError:
                continue

    # Extract from HTML tables
    table_stats = _extract_stats_from_tables(soup)
    stats.update(table_stats)

    # Extract patterns from text
    page_text = soup.get_text()
    pattern_stats = _extract_patterns_from_text(page_text)
    stats.update(pattern_stats)

    return stats if stats else None


def _extract_ausopen_stats(data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Extract stats from Australian Open JSON structure."""
    stats = {}
    
    def search_match_data(obj, depth=0):
        if depth > 8:
            return
        if isinstance(obj, dict):
            # Look for player/stats related keys
            for key, value in obj.items():
                key_lower = key.lower()
                if any(term in key_lower for term in ["serve", "return", "ace", "winner", "error", "break"]):
                    stats[key] = value
                if key_lower in ["player", "opponent", "match", "statistics", "stats"]:
                    search_match_data(value, depth + 1)
            for value in obj.values():
                search_match_data(value, depth + 1)
        elif isinstance(obj, list):
            for item in obj:
                search_match_data(item, depth + 1)
    
    search_match_data(data)
    return stats if stats else None


def _extract_wimbledon_stats(data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Extract stats from Wimbledon JSON structure."""
    stats = {}
    
    def search_stats(obj, depth=0):
        if depth > 8:
            return
        if isinstance(obj, dict):
            for key, value in obj.items():
                key_lower = key.lower()
                if any(term in key_lower for term in ["serve", "return", "ace", "winner", "double fault"]):
                    stats[key] = value
            for value in obj.values():
                search_stats(value, depth + 1)
        elif isinstance(obj, list):
            for item in obj:
                search_stats(item, depth + 1)
    
    search_stats(data)
    return stats if stats else None


def _extract_generic_stats(data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Extract stats from any JSON structure."""
    stats = {}

    def search_stats(obj, depth=0):
        if depth > 6:
            return
        if isinstance(obj, dict):
            for key, value in obj.items():
                if any(term in key.lower() for term in ["serve", "return", "ace", "winner", "error", "break", "point", "game", "set", "match"]):
                    stats[key] = value
            for value in obj.values():
                search_stats(value, depth + 1)
        elif isinstance(obj, list):
            for item in obj:
                search_stats(item, depth + 1)

    search_stats(data)
    return stats if stats else None


def _extract_stats_from_tables(soup: BeautifulSoup) -> Dict[str, Any]:
    """Extract tennis stats from HTML tables."""
    stats = {}

    tables = soup.find_all("table")
    for table in tables:
        rows = table.find_all("tr")
        for row in rows:
            cells = row.find_all(["td", "th"])
            if len(cells) >= 2:
                label = cells[0].get_text(strip=True)
                value = cells[1].get_text(strip=True)
                
                # Clean up label and value
                label_clean = label.lower().strip()
                if any(term in label_clean for term in ["serve", "return", "ace", "winner", "fault", "break", "point", "game"]):
                    stats[label.strip()] = value.strip()

    return stats


def _extract_patterns_from_text(text: str) -> Dict[str, Any]:
    """Extract stats using pattern matching from page text."""
    return MatchDetector.extract_stats_from_text(text)
