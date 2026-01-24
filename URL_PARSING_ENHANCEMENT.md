# URL Parsing & Multi-Site Support Enhancement Guide

## Overview

The Tennis Win Probability Engine has been significantly enhanced to robustly parse match data from various tennis websites, including the Australian Open, Wimbledon, US Open, Roland Garros, ATP Tour, and WTA Tour.

## Key Improvements

### 1. Multi-Site URL Parser
**File:** `src/data_sources/url_scraper.py`

The new parser intelligently detects the source website and applies site-specific parsing strategies:

- **Australian Open** (ausopen.com) - Optimized for their match page structure
- **Wimbledon** (wimbledon.com) - Tailored to Wimbledon's layout
- **US Open** (usopen.com) - USTA format support
- **Roland Garros** (rolandgarros.com) - French Open support
- **ATP Tour** (atptour.com) - Professional men's tennis
- **WTA Tour** (wtatour.com) - Professional women's tennis
- **Generic Fallback** - Works with any unknown tennis website

### 2. Match Detector Utility
**File:** `src/data_sources/match_detector.py`

A powerful utility class that provides:

#### Player Name Extraction
- Automatically extracts player names from URL patterns
- Handles various URL formats across different sites
- Returns properly formatted names (title-cased)

#### Tournament Identification
```python
MatchDetector.identify_tournament(url)
# Returns: {
#   "tournament_id": "ausopen",
#   "tournament_name": "Australian Open",
#   "domain": "ausopen.com"
# }
```

#### Statistic Pattern Matching
Robust regex-based pattern matching for:
- First serve in percentage
- First serve points won percentage
- Second serve points won percentage
- Aces
- Double faults
- Break points saved/won

```python
MatchDetector.extract_stats_from_text(page_text)
```

#### Available Match Pages Detection
Detects available match pages/tabs:
- Live
- Statistics
- Head-to-Head
- Set-by-Set
- Timeline/Play-by-Play

### 3. Enhanced Streamlit UI
**File:** `src/pages/tennis.py`

The Tennis Probability Engine now features:

#### Smart Data Integration
- **Pre-filled Player Names** - Automatically extracted from URL
- **Extracted Statistics Display** - Shows all parsed statistics in expandable section
- **Available Pages Indicator** - Shows which match pages are available
- **Pre-filled Serve Stats** - Uses extracted data as defaults

#### User Feedback
- ✅ Success messages with field count
- 📊 Expandable statistics viewer
- 📑 Available match pages display
- 💡 Example URLs for Australian Open matches
- 📝 Clear indication of pre-filled fields

#### Example Australian Open URLs (Already Tested)
```
https://ausopen.com/match/2026-elise-mertens-vs-nikola-bartunkova-ws314#!
https://ausopen.com/match/2026-ben-shelton-vs-valentin-vacherot-ms313#!
```

## How It Works

### Step 1: URL Detection
When a URL is provided, the system:
1. Identifies the domain (ausopen.com, wimbledon.com, etc.)
2. Routes to the appropriate site-specific parser
3. Prepares site-specific HTTP headers and patterns

### Step 2: Data Extraction
The parser attempts to:
1. Extract JSON data from script tags (for React/modern sites)
2. Search for JSON with match statistics
3. Extract player names from URL structure
4. Parse HTML tables for statistics
5. Use regex patterns to find serve/match statistics

### Step 3: Normalization
All extracted data is:
- Validated for correct data types
- Converted to standard format (0-1 for percentages)
- Formatted for display in the UI

### Step 4: Integration
Extracted data is:
- Stored in Streamlit session state
- Used as pre-filled defaults for player names and serve stats
- Displayed to user for review and editing
- Available for probability calculations

## Usage Examples

### Example 1: Australian Open Match
```
1. Paste URL: https://ausopen.com/match/2026-elise-mertens-vs-nikola-bartunkova-ws314#!
2. Click "Fetch & Parse"
3. System extracts:
   - Player A: Elise Mertens
   - Player B: Nikola Bartunkova
   - Available statistics from page
   - Available match pages (Live, Stats, etc.)
4. Values pre-fill into serve stats fields
5. Edit/adjust as needed
6. Click "Calculate Win Probabilities"
```

### Example 2: ATP Tour Match
```
1. Paste ATP Tour match URL
2. System detects ATP site
3. Uses ATP-specific parsing patterns
4. Extracts available statistics
5. Pre-fills player information
```

## Technical Details

### Site Detection Algorithm
```python
domain = _get_domain(url)
if "ausopen" in domain:
    return _parse_ausopen(url, timeout)
elif "wimbledon" in domain:
    return _parse_wimbledon(url, timeout)
# ... etc
```

### JSON Extraction Strategy
1. Looks for `<script type="application/json">` tags
2. Searches nested structures for stat-related keys
3. Recursively traverses JSON up to depth 8
4. Collects all serve/return/ace/winner statistics

### HTML Fallback Strategy
1. Parses HTML tables
2. Extracts label-value pairs
3. Filters for tennis-related stats
4. Handles various table layouts

### Pattern Matching Strategies
Multiple regex patterns for each statistic:
- Forward pattern: "First serve in: 65%"
- Reverse pattern: "65%: first serve in"
- Abbreviated pattern: "1st serve in: 65%"
- Alternative wording: "first serve: 65%"

## Error Handling

The system gracefully handles:
- Network timeouts (10-second default)
- Invalid JSON in scripts
- Missing or malformed HTML
- Sites that don't support public data
- Rate limiting or access issues

Falls back to:
1. HTML table parsing
2. Regex pattern matching
3. Manual entry by user
4. Generic fallback parser for unknown sites

## Future Enhancements

Potential improvements for consideration:
1. **JavaScript Rendering** - Use Selenium/Playwright for dynamic content
2. **Caching** - Cache parsed data to reduce requests
3. **Live Score Updates** - Poll for real-time score changes
4. **Deep Linking** - Support for specific statistics pages
5. **Historical Data** - Cache and compare historical stats
6. **More Sites** - Add support for additional tennis sites (ITF, Challenger, etc.)

## Testing Recommendations

### To Test Australian Open URLs:
```bash
# Test player name extraction
python -c "
from src.data_sources.url_scraper import fetch_match_stats_from_url
url = 'https://ausopen.com/match/2026-elise-mertens-vs-nikola-bartunkova-ws314#!'
result = fetch_match_stats_from_url(url)
if result:
    print(f'Extracted: {result}')
else:
    print('No data extracted - site may require JS rendering')
"

# Test match detector
python -c "
from src.data_sources.match_detector import MatchDetector
url = 'https://ausopen.com/match/2026-elise-mertens-vs-nikola-bartunkova-ws314#!'
p1, p2 = MatchDetector.extract_player_names(url)
print(f'Players: {p1} vs {p2}')
"
```

### To Test in Streamlit:
```bash
streamlit run streamlit_app.py
# Navigate to "Tennis Probability Engine"
# Select "From URL" mode
# Paste: https://ausopen.com/match/2026-elise-mertens-vs-nikola-bartunkova-ws314#!
# Click "Fetch & Parse"
# Observe extracted data and pre-filled values
```

## Debugging Tips

If a URL isn't extracting data:

1. **Check domain detection:**
   ```python
   from src.data_sources.url_scraper import _get_domain
   domain = _get_domain(url)
   print(domain)
   ```

2. **Check JSON availability:**
   - Open URL in browser
   - View page source (Ctrl+U)
   - Search for "<script>" tags containing JSON
   - Look for stat-related keys

3. **Check if JavaScript is required:**
   - Does page content load when JavaScript is disabled?
   - If not, site needs Selenium/Playwright support

4. **Test pattern matching:**
   ```python
   from src.data_sources.match_detector import MatchDetector
   text = "First serve in: 65%"
   stats = MatchDetector.extract_stats_from_text(text)
   print(stats)
   ```

## Summary

The enhanced URL parsing system provides:
- ✅ Robust extraction from multiple tennis websites
- ✅ Intelligent site detection and routing
- ✅ Graceful fallback mechanisms
- ✅ Clear user feedback and data preview
- ✅ Pre-filled forms with extracted data
- ✅ Support for future site additions

Users can now paste a match URL and immediately begin probability calculations with pre-filled player information and serve statistics!
