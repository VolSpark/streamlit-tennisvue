# 🎾 URL Parsing Enhancement - Quick Start

## What Was Enhanced

The Tennis Win Probability Engine now intelligently parses match data from multiple tennis websites including Australian Open, Wimbledon, US Open, Roland Garros, ATP Tour, and WTA Tour.

## Key Features Added

### 1. **Multi-Site Support**
- Automatically detects which site the URL is from
- Uses optimized parsing for each site
- Falls back to generic parser for unknown sites

### 2. **Smart Player Extraction**
- Automatically extracts player names from URL
- Pre-fills player fields
- Handles various URL formats

### 3. **Statistical Pattern Recognition**
- Detects serve statistics from page content
- Recognizes percentage patterns
- Finds aces, breaks, and other match stats

### 4. **Available Pages Detection**
- Shows which match pages are available (Live, Stats, H2H, etc.)
- Helps users select appropriate data source

### 5. **Enhanced User Interface**
- Shows extraction progress
- Displays extracted data in expandable sections
- Provides example URLs
- Clear pre-fill confirmation

## Supported Websites

✅ **Tested & Optimized:**
- Australian Open (ausopen.com)
- Wimbledon (wimbledon.com)
- US Open (usopen.com)
- Roland Garros (rolandgarros.com)
- ATP Tour (atptour.com)
- WTA Tour (wtatour.com)

✅ **Fallback Support:** Any other tennis website

## How to Use

### Step 1: Paste URL
Navigate to **Tennis Probability Engine** > **From URL** mode and paste a match URL:
```
https://ausopen.com/match/2026-elise-mertens-vs-nikola-bartunkova-ws314#!
```

### Step 2: Fetch & Parse
Click the **"🔍 Fetch & Parse"** button

### Step 3: Review Extracted Data
- Player names will appear in the Player A/B fields
- Extracted statistics shown in expandable section
- Available match pages listed
- Serve stats pre-filled where available

### Step 4: Calculate
Click **"🚀 Calculate Win Probabilities"** to get insights

## Example URLs (Australian Open)

These URLs are live and can be tested immediately:

**Women's Singles:**
```
https://ausopen.com/match/2026-elise-mertens-vs-nikola-bartunkova-ws314#!
```

**Men's Singles:**
```
https://ausopen.com/match/2026-ben-shelton-vs-valentin-vacherot-ms313#!
```

## What Gets Extracted

From a match URL, the system extracts:
- ✅ Player A name
- ✅ Player B name
- ✅ First serve in percentage
- ✅ First serve points won percentage
- ✅ Second serve points won percentage
- ✅ Aces
- ✅ Double faults
- ✅ Break points information
- ✅ Available match pages

## File Structure

```
src/data_sources/
├── url_scraper.py          # Main URL parsing engine
├── match_detector.py       # Smart detection & extraction
└── paste_parser.py         # (existing)

src/pages/
└── tennis.py               # Enhanced UI with URL support
```

## Technical Architecture

### URL Scraper Flow:
```
URL Input
    ↓
Domain Detection (ausopen? wimbledon? etc)
    ↓
Site-Specific Parser
    ↓
JSON Extraction (if available)
    ↓
HTML Table Parsing (fallback)
    ↓
Pattern Matching (final fallback)
    ↓
Data Normalization
    ↓
Display & Storage
```

### Detection Strategy:
1. **Identify Tournament** - Check domain
2. **Extract Players** - Parse URL structure
3. **Fetch Page** - HTTP GET with proper headers
4. **Parse JSON** - Look in script tags
5. **Parse HTML** - Extract tables
6. **Match Patterns** - Find percentages and stats
7. **Normalize** - Convert to 0-1 scale for percentages

## Troubleshooting

### ❌ "Could not extract stats from URL"

**Reasons:**
- Website uses heavy JavaScript rendering (not yet supported)
- Page requires authentication
- URL doesn't match expected pattern

**Solutions:**
1. Try pasting the data manually
2. Use "Paste Snapshot" mode
3. Enter data manually
4. Check if the match page is still live

### ✅ Player names extracted but no stats

**Why:** The site may not expose statistics in a parseable format yet

**What to do:**
1. Pre-filled player names are ready
2. Manually enter the serve statistics
3. Or use "Paste Snapshot" with copied stats

### ✅ Some stats extracted, some missing

**Expected behavior:** Not all sites expose all statistics

**Solution:** Manually fill in missing required fields:
- First Serve In %
- First Serve Points Won %
- Second Serve Points Won %

## API Reference

### fetch_match_stats_from_url()
```python
from src.data_sources.url_scraper import fetch_match_stats_from_url

stats = fetch_match_stats_from_url(
    "https://ausopen.com/match/2026-...",
    timeout=10  # seconds
)
# Returns: {'player_a_name': '...', 'player_b_name': '...', ...}
# Or: None if extraction failed
```

### get_available_match_pages()
```python
from src.data_sources.url_scraper import get_available_match_pages

pages = get_available_match_pages("https://ausopen.com/match/2026-...")
# Returns: [
#   {'type': 'live', 'label': 'Live'},
#   {'type': 'statistics', 'label': 'Statistics'},
#   ...
# ]
```

### MatchDetector
```python
from src.data_sources.match_detector import MatchDetector

# Extract player names
p1, p2 = MatchDetector.extract_player_names(url)

# Identify tournament
tournament = MatchDetector.identify_tournament(url)

# Extract stats from text
stats = MatchDetector.extract_stats_from_text(page_text)

# Detect available pages
pages = MatchDetector.detect_live_pages(html_content)
```

## Performance Notes

- **Timeout:** 10 seconds per URL fetch (configurable)
- **Recursion Depth:** Limited to 8 levels for JSON parsing (prevents infinite loops)
- **Regex Patterns:** Optimized for speed, comprehensive coverage

## Future Roadmap

🔄 **Planned Improvements:**
- JavaScript rendering support (Selenium/Playwright)
- Real-time score polling
- Match page caching
- Additional site support (ITF, Challenger, etc.)
- Historical stat comparison
- Deep linking to specific pages

## Questions?

Refer to **URL_PARSING_ENHANCEMENT.md** for:
- Detailed technical documentation
- Debugging strategies
- Testing procedures
- Architecture details
