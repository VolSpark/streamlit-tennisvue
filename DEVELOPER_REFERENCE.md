# Developer Quick Reference

## New Features At a Glance

### Functions Added to `src/models/probabilities.py`

#### 1. `get_all_game_outcomes(snapshot)`
```python
def get_all_game_outcomes(snapshot: MatchSnapshot) 
    -> Tuple[Optional[Dict[str, float]], Optional[float], Optional[str]]:
```

**What it does**:
- Enumerates ALL possible game outcomes from current point score
- Calculates probability of reaching deuce
- Returns outcomes as readable strings with probabilities

**Returns**:
- `outcomes`: Dict like `{"Djokovic 30–15: 0.706, "Djokovic 40–15": 0.499, ...}`
- `p_deuce`: Float like `0.258` (25.8% probability of deuce)
- `note`: String with explanation

**Usage**:
```python
outcomes, p_deuce, note = get_all_game_outcomes(snapshot)
if outcomes:
    for outcome, prob in sorted(outcomes.items(), key=lambda x: -x[1])[:5]:
        print(f"  {outcome}: {prob:.1%}")
else:
    print(f"Error: {note}")
```

---

#### 2. `forecast_next_game_outcomes(snapshot)`
```python
def forecast_next_game_outcomes(snapshot: MatchSnapshot) 
    -> Tuple[Optional[Dict[str, float]], Optional[str]]:
```

**What it does**:
- Predicts outcomes of the NEXT game (after current game completes)
- Calculates hold/break probabilities for next server
- Integrates Bayesian blending with live data

**Returns**:
- `outcomes`: Dict like `{"Sinner holds serve: 0.94, "Federer breaks": 0.06}`
- `note`: String with explanation

**Usage**:
```python
next_out, note = forecast_next_game_outcomes(snapshot)
if next_out:
    for outcome, prob in next_out.items():
        print(f"  • {outcome}")
```

---

## Changes to `src/pages/tennis.py`

### Session State Initialization
```python
# NEW: Initialize prediction history
if "prediction_history" not in st.session_state:
    st.session_state.prediction_history = []
```

### Imports Added
```python
import time  # For auto-refresh timing
from src.models.probabilities import (
    # ... existing imports ...
    get_all_game_outcomes,  # NEW
    forecast_next_game_outcomes,  # NEW
)
```

### Auto-Refresh Logic
```python
# NEW: Auto-refresh for URL mode (5 seconds)
auto_refresh = refresh_mode == "Auto (5s)" and data_mode == "From URL"
if auto_refresh:
    if "last_refresh" not in st.session_state:
        st.session_state.last_refresh = time.time()
    
    time_since_refresh = time.time() - st.session_state.last_refresh
    if time_since_refresh < 5:
        st.info(f"⏳ Next refresh in {5 - int(time_since_refresh)} seconds...")
        time.sleep(0.5)
        st.rerun()
```

### Enhanced Results Display
```python
# NEW: Detailed Current Game Analysis Section
game_outcomes, p_deuce, note = get_all_game_outcomes(snapshot)
if game_outcomes:
    sorted_outcomes = sorted(game_outcomes.items(), key=lambda x: x[1], reverse=True)
    max_prob = max(game_outcomes.values())
    
    for outcome, prob in sorted_outcomes[:10]:
        if prob >= max_prob * 0.95:  # BOLD highest (95% of max)
            st.markdown(f"**{outcome}: {prob:.1%}**")
        else:
            st.write(f"  {outcome}: {prob:.1%}")
```

### Prediction History Storage
```python
# NEW: Store each prediction with metadata
st.session_state.prediction_history.append({
    "timestamp": datetime.now(),
    "score": f"{point_score_a}–{point_score_b}",
    "server": server,
    "game_outcomes": game_outcomes,
    "p_deuce": p_deuce,
    "match_state": f"{sets_won_a}-{sets_won_b} {games_in_set_a}-{games_in_set_b}"
})
```

### History Display
```python
# NEW: Optional history display
if show_history and st.session_state.prediction_history:
    for idx, pred in enumerate(reversed(st.session_state.prediction_history)):
        with st.expander(f"Prediction #{idx} - {pred['timestamp'].strftime('%H:%M:%S')}"):
            st.write(f"Score: {pred['score']}")
            st.write(f"P(Deuce): {pred['p_deuce']:.1%}")
            st.write("Game outcomes:")
            for outcome, prob in sorted(pred['game_outcomes'].items(), 
                                       key=lambda x: -x[1])[:5]:
                st.write(f"  • {outcome}: {prob:.1%}")
```

---

## Key Implementation Details

### Markov Chain Algorithm
```
For all possible game outcomes:
1. Start at current (points_server, points_receiver)
2. Recursively compute paths to terminal states (game win/loss)
3. Weight each path by probability of that sequence
4. Sum probabilities of all paths to same outcome
5. Use memoization to avoid redundant calculations

Terminal conditions:
  - Server wins: points_s >= 4 AND points_s - points_r >= 2
  - Receiver wins: points_r >= 4 AND points_r - points_s >= 2

Recursion depth cap:
  - If points_s > 10 OR points_r > 10: Use asymptotic approximation
  - Prevents stack overflow while maintaining accuracy
```

### Bolding Logic
```python
# Find max probability
max_prob = max(outcomes.values())  # e.g., 100.0%

# Calculate 95% threshold
threshold = max_prob * 0.95  # e.g., 95.0%

# For each outcome
for outcome, prob in outcomes.items():
    if prob >= threshold:
        st.markdown(f"**{outcome}: {prob:.1%}**")  # BOLD
    else:
        st.write(f"  {outcome}: {prob:.1%}")  # normal text
```

### Auto-Refresh Cycle
```python
# Every page load/rerun
current_time = time.time()
last_refresh = st.session_state.last_refresh
elapsed = current_time - last_refresh

if elapsed >= 5:  # 5 seconds have passed
    fetch_latest_data()  # Get new match stats
    update_all_predictions()  # Recalculate probabilities
    st.session_state.last_refresh = current_time  # Reset timer
else:  # Less than 5 seconds
    remaining = 5 - int(elapsed)
    st.info(f"⏳ Next refresh in {remaining} seconds...")
    time.sleep(0.5)
    st.rerun()  # Trigger page refresh
```

---

## Testing Your Changes

### Quick Test Script
```python
from datetime import datetime
from src.tennis_schema import MatchSnapshot, PlayerStats
from src.models.probabilities import get_all_game_outcomes

# Create test snapshot
snapshot = MatchSnapshot(
    timestamp=datetime.now(),
    best_of_sets=5,
    player_a_name="Player A",
    player_b_name="Player B",
    sets_won_a=0, sets_won_b=0,
    games_in_set_a=0, games_in_set_b=0,
    point_score_a="15", point_score_b="15",
    server="A",
    player_a=PlayerStats("A", 0.65, 0.82, 0.60),
    player_b=PlayerStats("B", 0.68, 0.80, 0.58),
)

# Test new function
outcomes, p_deuce, note = get_all_game_outcomes(snapshot)
print(f"Outcomes: {len(outcomes)}")
print(f"P(Deuce): {p_deuce:.1%}")
```

### Running Full Test Suite
```bash
cd /workspaces/streamlit-tennisvue
python3 test_new_features.py
```

Expected output:
```
╔════════════════════════════════════════════════════════╗
║        NEW DETAILED GAME OUTCOMES TEST SUITE           ║
╚════════════════════════════════════════════════════════╝

✓ PASS: All Game Outcomes
✓ PASS: Deuce Scenarios
✓ PASS: Next Game Forecast
✓ PASS: Prediction History
✓ PASS: Highest Probability Marking
✓ PASS: Graceful Degradation

Total: 6/6 tests passed
```

---

## Common Integration Patterns

### Pattern 1: Display All Outcomes with Bolding
```python
outcomes, p_deuce, note = get_all_game_outcomes(snapshot)
if outcomes:
    sorted_outcomes = sorted(outcomes.items(), key=lambda x: x[1], reverse=True)
    max_prob = max(outcomes.values())
    
    st.markdown("**Possible outcomes:**")
    for outcome, prob in sorted_outcomes:
        if prob >= max_prob * 0.95:
            st.markdown(f"**{outcome}: {prob:.1%}**")
        else:
            st.write(f"  {outcome}: {prob:.1%}")
    
    st.metric("P(Deuce)", f"{p_deuce:.1%}")
```

### Pattern 2: Track Prediction History
```python
# When calculating probabilities
outcomes, p_deuce, _ = get_all_game_outcomes(snapshot)

# Store in session state
st.session_state.prediction_history.append({
    "timestamp": datetime.now(),
    "score": f"{snapshot.point_score_a}–{snapshot.point_score_b}",
    "outcomes": outcomes,
    "p_deuce": p_deuce,
})

# Display history
if show_history:
    for pred in st.session_state.prediction_history:
        with st.expander(f"{pred['score']} @ {pred['timestamp'].strftime('%H:%M')}"):
            st.write(f"P(Deuce): {pred['p_deuce']:.1%}")
```

### Pattern 3: Auto-Refresh Loop
```python
if auto_refresh and data_source == "URL":
    if "last_refresh" not in st.session_state:
        st.session_state.last_refresh = time.time()
    
    elapsed = time.time() - st.session_state.last_refresh
    if elapsed < 5:
        st.info(f"⏳ Next refresh in {5 - int(elapsed)}s")
        time.sleep(0.5)
        st.rerun()
    else:
        # Fetch and update
        stats = fetch_match_stats_from_url(url)
        # ... create snapshot and calculate ...
        st.session_state.last_refresh = time.time()
```

---

## Debugging Tips

### Check if New Functions Are Available
```python
from src.models.probabilities import get_all_game_outcomes
print(get_all_game_outcomes.__doc__)
```

### Verify Outcomes Calculation
```python
outcomes, p_deuce, note = get_all_game_outcomes(snapshot)
print(f"Number of outcomes: {len(outcomes)}")
print(f"Sum of probabilities: {sum(outcomes.values()):.2%}")
print(f"Deuce probability: {p_deuce:.1%}")
```

### Check Auto-Refresh Timer
```python
print(f"Last refresh: {st.session_state.get('last_refresh', 'N/A')}")
print(f"Time now: {time.time()}")
print(f"Elapsed: {time.time() - st.session_state.get('last_refresh', 0)} seconds")
```

### Verify Prediction History
```python
if st.session_state.prediction_history:
    print(f"Predictions stored: {len(st.session_state.prediction_history)}")
    for i, pred in enumerate(st.session_state.prediction_history):
        print(f"  {i+1}. {pred['score']} @ {pred['timestamp'].strftime('%H:%M:%S')}")
```

---

## Performance Optimization Tips

1. **Memoization**: Already implemented - caches game probability calculations
2. **Limit displayed outcomes**: Show top 10 instead of all 22+
3. **Batch predictions**: Process multiple refreshes without recalculating old ones
4. **Cache player stats**: Store calculated serve point percentages in session

---

## File Locations

| File | Purpose | Status |
|------|---------|--------|
| `src/models/probabilities.py` | Core probability functions | Modified (+150 lines) |
| `src/pages/tennis.py` | UI and display logic | Modified (+200 lines) |
| `test_new_features.py` | Test suite | Created |
| `FEATURE_SUMMARY.md` | Technical documentation | Created |
| `USAGE_GUIDE.md` | User guide | Created |
| `ARCHITECTURE.md` | System architecture | Created |
| `TEST_REPORT.md` | Test results | Created |
| `IMPLEMENTATION_COMPLETE.md` | Summary | Created |

---

## Version History

| Date | Version | Changes |
|------|---------|---------|
| 2026-01-22 | 1.1.0 | Initial release of detailed game outcomes feature |
| (TBD) | 1.2.0 | Planned: Prediction export, confidence intervals |

---

## Support & Questions

For questions about implementation:
1. Check `FEATURE_SUMMARY.md` for technical details
2. Check `USAGE_GUIDE.md` for user-facing explanations
3. Check `ARCHITECTURE.md` for system design
4. Review test cases in `test_new_features.py`
5. Run debugging commands above

For issues:
1. Run test suite: `python3 test_new_features.py`
2. Check syntax: Use Pylance syntax checker
3. Verify imports are working
4. Check session state is initialized

---

## Backward Compatibility Checklist

- ✅ Existing functions unchanged
- ✅ New functions are additions only
- ✅ No modification to MatchSnapshot schema
- ✅ No changes to existing UI sections
- ✅ All existing features work as before
- ✅ Can migrate existing code without changes

---

**Last Updated**: 2026-01-22
**Maintained By**: Streamlit Tennis Engine Team
**Status**: Production Ready ✅
