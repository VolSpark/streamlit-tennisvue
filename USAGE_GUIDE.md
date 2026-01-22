# Quick Start Guide - Detailed Game Outcomes

## What's New? 🎾

The Tennis Win Probability Engine now provides detailed game outcome analysis with three major enhancements:

### 1. 🎯 All Possible Game Outcomes
See the probability of **every possible ending** of the current game, including:
- All intermediate scores (e.g., "15–30", "40–15", "Deuce")
- **Highest probability outcome automatically bolded** for easy identification
- Probability of reaching deuce from the current score
- Clear visual hierarchy of most likely outcomes

### 2. 📊 Prediction History
Every time you calculate probabilities, the prediction is **saved with a timestamp**:
- Click "📋 Show prediction history" to review past predictions
- See how probabilities evolved throughout the game
- Each prediction shows:
  - Exact time of calculation
  - Point score
  - Match state (sets and games)
  - Top outcomes
  - Deuce probability

### 3. ⏱️ Live Auto-Refresh
When using URL data source, enable "Auto (5s)" mode to:
- Automatically fetch latest match stats every 5 seconds
- Update all probabilities in real-time
- Maintain complete prediction history across all refreshes
- Perfect for watching live matches

---

## How to Use

### Step 1: Select Data Source
```
Choose: "Manual Entry", "Paste Snapshot", or "From URL"
```

### Step 2: Choose Refresh Mode
```
Select: "Manual" (update on demand) or "Auto (5s)" (live updates)
```

### Step 3: Enter Match Data
```
- Player names
- Current match score (sets and games)
- Point score (0, 15, 30, 40, AD)
- Server designation
- Serve stats (1st serve in %, 1st serve win %, 2nd serve win %)
```

### Step 4: Click "🚀 Calculate Win Probabilities"

### Step 5: View Results

#### 📈 Win Probabilities Section
Shows all existing outputs (point, game, set, match probabilities)

#### 🎯 Detailed Current Game Analysis
**NEW** - Shows:
```
Possible outcomes from 15–30:
  **Player A 30–30: 44.0%**  ← Bolded (highest)
  Player A 15–40: 38.2%
  Player A 30–15: 35.1%
  ... (all possible scores)

P(Deuce): 18.3%
```

#### 🎾 Next Game Prediction
**NEW** - Shows:
```
  • Player B holds serve: 85.0%
  • Player A breaks: 15.0%
```

#### 📊 Prediction History (Optional)
Click "📋 Show prediction history" to see all previous predictions with expandable details for each.

---

## Interpreting the Results

### Highest Probability Outcome
The outcome bolded in the "Detailed Current Game Analysis" section is:
- **Highest probability outcome**: The single most likely endpoint
- **Within 95% of max**: All outcomes within 95% of the maximum probability are bolded
- Use this for quick visual scanning

### Deuce Probability
The "P(Deuce)" metric tells you:
- **Low (~10-20%)**: Game will likely finish soon (one player is clearly up)
- **Medium (~40-50%)**: Score is relatively balanced, deuce is likely
- **100%**: Currently at deuce or advantage, uncertain outcome ahead

### Next Game Forecast
When both probabilities shown, the higher one is:
- **Hold probability (>50%)**: Server likely to hold
- **Break probability (>50%)**: Receiver likely to break serve

---

## Example Scenarios

### Scenario 1: Server Leading 40–15
```
Input: Score 40–15, Server A with 0.82 first serve win %

Output:
  Possible outcomes:
    **Server A wins: 87.1%**  ← Highest (bolded)
    Deuce: 10.2%
    Receiver wins: 2.7%
  
  P(Deuce): 10.2%
  
  Interpretation: Server is heavily favored but still some risk
```

### Scenario 2: Deuce Situation (40–40)
```
Input: Score 40–40 (Deuce), Both players ~65% serve win %

Output:
  Possible outcomes:
    **Server Advantage: 65.0%**  ← Highest (bolded)
    Receiver Advantage: 35.0%
  
  P(Deuce): 100.0%
  
  Interpretation: Server is slightly favored at deuce
```

### Scenario 3: Receiver Leading 15–30
```
Input: Score 15–30, Server B with 0.78 first serve win %

Output:
  Possible outcomes:
    **Receiver wins (30–15): 43.2%**  ← Highest
    Server leads (30–30): 38.5%
    Receiver wins (0–40): 12.3%
    ... (more outcomes)
  
  P(Deuce): 18.3%
  
  Interpretation: Receiver has momentum but server not out of danger
```

---

## Tips for Best Results

### For Accurate Probabilities
1. **Update serve stats regularly** - Use latest match stats for accuracy
2. **Use consistent data source** - URL > Paste > Manual (in terms of freshness)
3. **Enable Bayesian blending** - Keep the default 70% live / 30% prior weighting

### For Live Match Analysis
1. Select "From URL" + "Auto (5s)" mode
2. Provide Australian Open or other official match URL
3. Let it run - predictions update automatically
4. Review prediction history to see how probabilities evolved

### For Post-Match Analysis
1. Use "Manual Entry" to recreate scores at key moments
2. Enable "Show prediction history" to compare outcomes
3. Export history as CSV for deeper analysis

---

## Data Requirements (Minimum)

For the app to calculate probabilities, you need:

**Required:**
- ✅ Server designation (A or B)
- ✅ Current point score (0, 15, 30, 40, AD)
- ✅ Current games in set (A and B)
- ✅ For each player:
  - 1st Serve In %
  - 1st Serve Points Won %
  - 2nd Serve Points Won %

**Optional (for match context):**
- 📌 Player names
- 📌 Sets won (A and B)
- 📌 Best of (3 or 5 sets)

---

## Troubleshooting

### "No outcomes displayed"
- Check that all required fields are filled
- Verify server stats are valid (0.0–1.0 range)
- Make sure point score is valid (0, 15, 30, 40, AD)

### "Auto-refresh not working"
- Ensure "From URL" data source is selected
- Confirm "Auto (5s)" mode is enabled
- Check that URL is valid and accessible
- Look for error messages in the UI

### "Prediction history is empty"
- Click "🚀 Calculate Win Probabilities" at least once
- Check "📋 Show prediction history" checkbox
- History persists within the session (refresh browser clears it)

---

## FAQ

**Q: What does "bolded outcome" mean?**
A: The outcome is within 95% of the highest probability. Use this for quick visual scanning of most likely results.

**Q: Can I save my prediction history?**
A: Yes! Click "📊 Export to CSV" to download your snapshots with probabilities.

**Q: How often does auto-refresh update?**
A: Every 5 seconds when "Auto (5s)" mode is enabled. You'll see a countdown timer.

**Q: Do probabilities change between refreshes?**
A: Yes! As the match progresses and new data arrives, probabilities update to reflect the current match state.

**Q: Can I compare different scenarios?**
A: Yes! Use prediction history to compare outcomes from different point scores throughout the game.

---

## Technical Notes

- All calculations use **Markov chain models** - same as professional tennis analytics
- **Bayesian blending** combines live match data with historical averages (default 70% live / 30% prior)
- **Memoization** ensures calculations complete in <200ms even for complex game states
- **Session state** preserves prediction history throughout your browsing session

---

For detailed technical documentation, see [FEATURE_SUMMARY.md](FEATURE_SUMMARY.md)
