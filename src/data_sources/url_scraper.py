"""URL scraping for match stats (gracefully handles failures)."""

import json
import re
from typing import Optional, Dict, Any
import requests
from bs4 import BeautifulSoup


def fetch_match_stats_from_url(url: str, timeout: int = 5) -> Optional[Dict[str, Any]]:
    """
    Fetch match stats from a public tennis match URL.
    Returns dict of extracted stats, or None if not available.
    Gracefully handles failures.
    """
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()

        # Try to extract JSON from page
        soup = BeautifulSoup(response.text, "html.parser")

        # Look for script tags with JSON data
        for script in soup.find_all("script"):
            if script.string:
                try:
                    # Try to parse JSON from script content
                    data = json.loads(script.string)
                    stats = _extract_stats_from_json(data)
                    if stats:
                        return stats
                except json.JSONDecodeError:
                    continue

        # Fallback: look for common HTML patterns (varies by site)
        stats = _extract_stats_from_html(soup)
        if stats:
            return stats

        return None

    except requests.RequestException as e:
        print(f"Error fetching URL: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error parsing URL: {e}")
        return None


def _extract_stats_from_json(data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Extract tennis stats from JSON structure."""
    stats = {}

    # Look for nested stat objects (AO uses various structures)
    def search_stats(obj, depth=0):
        if depth > 5:  # Prevent infinite recursion
            return
        if isinstance(obj, dict):
            # Look for serve/return stats
            for key, value in obj.items():
                if "serve" in key.lower() or "return" in key.lower():
                    stats[key] = value
            for value in obj.values():
                search_stats(value, depth + 1)
        elif isinstance(obj, list):
            for item in obj:
                search_stats(item, depth + 1)

    search_stats(data)
    return stats if stats else None


def _extract_stats_from_html(soup: BeautifulSoup) -> Optional[Dict[str, Any]]:
    """Extract tennis stats from HTML structure."""
    stats = {}

    # Look for tables with stats
    tables = soup.find_all("table")
    for table in tables:
        # Very basic extraction; site-specific
        rows = table.find_all("tr")
        for row in rows:
            cells = row.find_all("td")
            if len(cells) >= 2:
                label = cells[0].get_text(strip=True)
                value = cells[1].get_text(strip=True)
                stats[label] = value

    return stats if stats else None
