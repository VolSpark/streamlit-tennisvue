# My Streamlit App

A minimal, production-ready Streamlit application with a **Live Tennis Win Probability Engine** and best practices for deployment, testing, and secrets management.

## 🎾 Feature: Live Tennis Win Probability Engine

**Ingests live tennis match stats and computes:**
- Next point win probability
- Next game win probability (with likely final scores)
- Next 3 games forecast
- Set & match win probabilities

**Data sources (graceful degradation):**
1. **From URL** - Scrape public match pages (e.g., ausopen.com)
2. **Paste Snapshot** - JSON, CSV, or plain-text stats
3. **Manual Entry** - Enter stats directly in the UI

**Models:**
- Markov chain for game/set/match probabilities
- Bayesian blending of live data with priors
- Full support for deuce, advantage, and tiebreaks

[See Tennis Engine Details](#tennis-engine-details) below.

---

## 📁 Repository Structure

```
streamlit-tennisvue/
├── app.py                       # Main entrypoint
├── requirements.txt             # Dependencies (pinned)
├── pyproject.toml               # Project config
├── run.ps1, run.sh              # Setup scripts
├── .gitignore, README.md        # Docs
│
├── .streamlit/
│   └── config.toml              # Streamlit theme & settings
│
├── src/
│   ├── __init__.py
│   ├── config.py                # Configuration
│   ├── utils.py                 # Utility functions
│   ├── styles.css               # Custom CSS
│   ├── tennis_schema.py          # MatchSnapshot dataclass
│   ├── pages/
│   │   ├── __init__.py
│   │   ├── home.py              # Home page
│   │   └── tennis.py            # Tennis engine page
│   ├── data_sources/
│   │   ├── __init__.py
│   │   ├── url_scraper.py       # Fetch from match URLs
│   │   └── paste_parser.py      # Parse pasted stats
│   └── models/
│       ├── __init__.py
│       ├── probabilities.py     # Markov chain models
│       └── blending.py          # Bayesian blending
│
└── tests/
    ├── __init__.py
    └── test_utils.py            # Tests (15+ tests for tennis logic)
```

---

## 🚀 Quick Start

### Windows (PowerShell 7+)

```powershell
.\run.ps1
```

### Mac / Linux

```bash
bash run.sh
```

Open your browser to `http://localhost:8501`

---

## 📋 Detailed Setup Instructions

### Prerequisites

- **Python 3.9+** installed ([Download](https://www.python.org/downloads/))
- **Git** installed
- A **GitHub account** (for deployment)

### Local Development

#### 1. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/streamlit-app.git
cd streamlit-app
```

#### 2. Create a Virtual Environment

**Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**Mac/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

#### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

#### 4. Run Locally

```bash
streamlit run app.py
```

Your app will open at `http://localhost:8501`

#### 5. Run Tests

```bash
pytest
```

#### 6. Format & Lint Code

```bash
black src tests app.py
ruff check src tests app.py --fix
```

---

## 🔐 Secrets Management

### Local Development

Create a `.streamlit/secrets.toml` file in your workspace (**do NOT commit**):

```toml
api_key = "your-secret-key"
database_url = "your-database-url"
```

Access secrets in code:
```python
import streamlit as st
api_key = st.secrets["api_key"]
```

### Production Deployment (Streamlit Community Cloud)

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Select your app
3. Click **App settings → Secrets**
4. Paste your secrets (same format as `.streamlit/secrets.toml`):
   ```toml
   api_key = "prod-secret-key"
   database_url = "prod-database-url"
   ```

**⚠️ Never commit `.streamlit/secrets.toml` to GitHub!**

---

## 🌐 Deploy to Streamlit Community Cloud

### Step-by-Step

1. **Push code to GitHub**
   ```bash
   git add .
   git commit -m "Deploy app"
   git push origin main
   ```

2. **Go to [share.streamlit.io](https://share.streamlit.io)**

3. **Click "New app"** → Sign in with GitHub

4. **Configure deployment:**
   - **Repository:** `YOUR_USERNAME/streamlit-app`
   - **Branch:** `main`
   - **Main file path:** `app.py`

5. **Click "Deploy"** and wait 2-3 minutes

6. **(Optional) Add secrets:**
   - App settings → Secrets
   - Paste your production secrets

Your app is now live! Share the URL with anyone.

---

## 🔧 Troubleshooting

### 1. "ModuleNotFoundError: No module named 'streamlit'"

**Solution:**
```bash
pip install -r requirements.txt
```

### 2. "Python is not installed or not in PATH" (Windows)

**Solution:**
- Download Python from [python.org](https://www.python.org/downloads/)
- **During installation, check "Add Python to PATH"**
- Restart your terminal and try again

### 3. "Permission denied: ./run.sh" (Mac/Linux)

**Solution:**
```bash
chmod +x run.sh
bash run.sh
```

### 4. Port 8501 is already in use

**Solution:**
```bash
streamlit run app.py --server.port 8502
```

### 5. App crashes after deploying to Streamlit Cloud

**Check:**
1. All imports in `requirements.txt`? → Run `pip freeze` locally
2. Secrets configured correctly? → Check Streamlit Cloud app settings
3. File paths correct? → Use `os.path.join()` or relative paths
4. Python version compatible? → Cloud uses Python 3.10+

---

## 📝 Development Workflow

### Adding a New Dependency

1. Install locally:
   ```bash
   pip install my-package
   ```

2. Add to `requirements.txt` with pinned version:
   ```bash
   pip freeze | grep my-package >> requirements.txt
   ```

3. Commit:
   ```bash
   git add requirements.txt
   git commit -m "Add my-package"
   git push
   ```

### Adding a New Page

1. Create `src/pages/my_page.py`:
   ```python
   import streamlit as st

   def render():
       st.title("My Page")
       st.write("Content here")
   ```

2. Import and route in `app.py`:
   ```python
   from src.pages import my_page
   
   if page == "My Page":
       my_page.render()
   ```

---

## 🎾 Tennis Engine Details

### Feature Overview

The **Live Tennis Win Probability Engine** computes real-time win probabilities for tennis matches using live match statistics.

**Supported outputs:**
- **Next point probability**: P(server holds point)
- **Next game probability**: P(server holds game) + likely final game scores
- **Next 3 games**: Probabilistic forecasts for upcoming games
- **Set win probability**: P(player A wins current set)
- **Match win probability**: P(player A wins match)

### Data Ingestion

The engine supports three gracefully-degrading data sources:

#### 1. From URL (Primary)
```
Paste public match URL (e.g., https://ausopen.com/match/2026-...)
→ App scrapes HTML/JSON for stats
→ Falls back to paste/manual if incomplete
```

#### 2. Paste Snapshot (Secondary)
```
Copy-paste match stats in JSON, CSV, or plain-text format
→ App parses extracted fields
→ Requests missing required fields via UI
```

#### 3. Manual Entry (Fallback)
```
Enter all stats directly in web form
→ Works even with zero external data
```

### Required Inputs (Minimum)

For any meaningful output, the app needs:

**Match structure:**
- Best-of sets (3 or 5)
- Current sets won (A and B)
- Current games in set (A and B)
- Current point score (e.g., 0, 15, 30, 40, AD)
- Current server (A or B)

**Serve statistics (per player):**
- First serve in % (0–1)
- First serve points won % (0–1)
- Second serve points won % (0–1)

**Example:**
```
Djokovic: 65% 1st in, 82% 1st win, 60% 2nd win
Alcaraz: 68% 1st in, 80% 1st win, 58% 2nd win
```

### Optional Enhancements

If available, the engine also uses:
- Detailed point counts (allows Bayesian credible intervals)
- Return stats (P(break), P(return game win))
- Break point conversion rates
- Aces, double faults, winners, unforced errors

### Probability Models

**Point level:**
Serve-point-win probability blends live data with tour-average priors.

```
p_serve_point = w × p_live + (1-w) × p_prior
where w = blending weight (default 0.70)
```

**Game level:**
Exact game-win probability using Markov chain from current point score.
Correctly handles deuce, advantage, and tiebreaks.

**Set level:**
Markov chain over game scores; first to 6 with 2-game lead (or tiebreak at 6-6).

**Match level:**
Markov chain over set scores; first to (best_of / 2 + 1) sets.

### Bayesian Blending

By default, the engine blends live observed stats with tour-average priors:
- **Prior**: Men's average serve-point-win ≈ 62% (configurable)
- **Live data**: Current match stats
- **Blend weight**: Default 0.70 (adjustable via slider)

If detailed counts are available (e.g., 82/100 points won on 1st serve), the engine can compute Bayesian credible intervals showing uncertainty.

### Graceful Degradation

The app handles missing data gracefully:

| Missing field | Behavior |
|---|---|
| Serve stats (A or B) | Request via UI form |
| Current point score | Request via UI form |
| Optional stats (aces, breaks, etc.) | Skip; use only base stats |
| URL scraping fails | Fall back to paste/manual |
| Partial stats in paste | Request remaining fields |

### Export & Sharing

- **CSV export**: Download all snapshots as timestamped CSV
- **Shareable summary**: One-paragraph plain-text summary with all stats and probabilities

### Example Walkthrough

**Scenario:** Australian Open mens final, live stats available

1. Paste URL or stats
2. Verify extracted fields (sets, games, points, serve stats)
3. Adjust blending weight if desired (default 0.70 is good)
4. Click "Calculate Win Probabilities"
5. View results:
   - Next point: Server 75%, Receiver 25%
   - Next game: Server 65%, Receiver 35%
   - Set win: Player A 58%, Player B 42%
   - Match win: Player A 65%, Player B 35%
6. Export to CSV or copy shareable summary

### Assumptions & Limitations

**Assumptions:**
- Players maintain consistent serve stats throughout match
- No momentum or fatigue modeling
- Independent points (no streaks)
- Break point conversion = 1 - (serve hold %)

**Limitations:**
- Does not account for player fatigue, injuries, or psychological factors
- Requires accurate live stats (garbage in → garbage out)
- Tiebreak model is simplified (does not use per-player serve advantage)

---

## ✅ Definition of Done (Pre-Deployment Checklist)

Before deploying to Streamlit Community Cloud, verify:

- [ ] All files created (`app.py`, `requirements.txt`, `src/`, `tests/`)
- [ ] `requirements.txt` has pinned Streamlit version (`streamlit==1.53.0`)
- [ ] Tests pass: `pytest` (all green)
- [ ] Code is formatted: `black src tests app.py` (no changes)
- [ ] No linting errors: `ruff check src tests app.py`
- [ ] No secrets in `.gitignore`: Git will ignore `.streamlit/secrets.toml`
- [ ] `.streamlit/secrets.toml` exists locally but NOT committed
- [ ] `app.py` imports work: `python app.py` (runs without errors, even if Streamlit complains)
- [ ] All changes committed: `git status` shows clean working directory
- [ ] Latest push to GitHub: `git log` shows recent commits
- [ ] Streamlit Community Cloud deployment works
- [ ] App loads at provided URL without errors
- [ ] Sidebar navigation works
- [ ] Form inputs respond correctly
- [ ] Secrets are accessible (if configured)

---

## 📚 Learn More

- [Streamlit Docs](https://docs.streamlit.io)
- [Python Virtual Environments](https://docs.python.org/3/tutorial/venv.html)
- [GitHub Deployment](https://docs.streamlit.io/deploy/streamlit-community-cloud)

---

## 📄 License

MIT License - See LICENSE file.

---

**Questions?** Check the troubleshooting section or [Streamlit Community Forums](https://discuss.streamlit.io)
