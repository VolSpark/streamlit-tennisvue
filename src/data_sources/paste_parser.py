"""Parse pasted match stats snapshot (JSON, CSV, or plain text)."""

import json
import csv
from io import StringIO
from typing import Optional, Dict, Any


def parse_pasted_stats(text: str) -> Optional[Dict[str, Any]]:
    """
    Parse user-pasted stats. Accepts JSON, CSV-like, or plain text.
    Returns dict of extracted stats, or None if parsing fails.
    """
    text = text.strip()
    if not text:
        return None

    # Try JSON first
    try:
        data = json.loads(text)
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError:
        pass

    # Try CSV-like format
    try:
        lines = text.split("\n")
        if len(lines) > 1:
            stats = {}
            for line in lines:
                parts = [p.strip() for p in line.split(",")]
                if len(parts) >= 2:
                    stats[parts[0]] = parts[1]
            if stats:
                return stats
    except Exception:
        pass

    # Try plain key:value format
    try:
        stats = {}
        for line in text.split("\n"):
            if ":" in line:
                key, val = line.split(":", 1)
                stats[key.strip()] = val.strip()
        if stats:
            return stats
    except Exception:
        pass

    return None
