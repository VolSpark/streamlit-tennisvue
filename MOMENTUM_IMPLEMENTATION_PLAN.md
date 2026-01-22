# 🎾 Momentum-Based Prediction Implementation Plan

## Paper Summary: Wang, Chen & Sabir (2024)

**Title**: Tennis Game Dynamic Prediction Model Based on Players' Momentum  
**Journal**: Applied Mathematics (MDPI 2673-9909, Vol 5, Issue 3)  
**Key Achievement**: ~84% accuracy game prediction using momentum features

---

## 📊 Core Methodology

### Three-Layer Calculation Pipeline

```
┌─────────────────────────────────────────────────────────────┐
│ Layer 1: Rolling Point-Win Probability (20-point window)   │
│  P₁ = (n_A_SrvWin + 1) / 20  (when A serves)               │
│  P₂ = (n_B_RcvWin + 1) / 20  (when B receives)             │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ Layer 2: Leverage (Counterfactual Impact of Point)         │
│  L_t = P_win(t) - P_lose(t)  [if player wins point]         │
│  L_t = 0                     [if player loses point]        │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ Layer 3: Momentum (EWMA-smoothed Leverage)                 │
│  M_X(t) = [L_t + (1-α)L_{t-1} + (1-α)²L_{t-2} + ...] /     │
│           [1 + (1-α) + (1-α)² + ...]                       │
│  α = 3.4 (tunable parameter)                               │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ Layer 4: Game Winner Prediction                            │
│  Input: Momentum difference, serve, score deltas           │
│  Model: XGBoost classifier                                 │
│  Output: P(game_winner)  [accuracy ~84%]                   │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔧 Implementation Details

### 1. Rolling Point-Win Probability (Layer 1)

**Purpose**: Track real-time point-win probabilities using recent history

**Implementation**:

```python
def calculate_rolling_point_win_probability(
    is_serving: bool,
    previous_wins: int,
    window_size: int = 20,
    smoothing: int = 1
) -> float:
    """
    Calculate rolling point-win probability conditioned on serve.
    
    Args:
        is_serving: Whether current player is serving
        previous_wins: Count of wins in last `window_size` points
        window_size: Number of points to consider (default: 20)
        smoothing: Laplace smoothing (+1 by default)
    
    Returns:
        Probability float between 0 and 1
    
    Formula:
        P = (n_wins + smoothing) / window_size
    
    Example:
        Player A serving, won 12 of last 20 points:
        P_A_serve = (12 + 1) / 20 = 0.65
        P_A_receive = (remaining + 1) / 20 = 0.35
    """
    probability = (previous_wins + smoothing) / window_size
    return min(max(probability, 0.0), 1.0)  # Clamp to [0, 1]
```

**Integration into Current System**:
- Maintain a 20-point sliding window in session state
- Separate tracking for "serve wins" and "receive wins"
- Update after each point in live data

---

### 2. Leverage Calculation (Layer 2)

**Purpose**: Quantify the counterfactual impact of winning/losing a point

**Implementation**:

```python
def calculate_leverage(
    player_won_point: bool,
    p_win_match: float,
    p_lose_match: float
) -> float:
    """
    Calculate leverage: the swing in match-win probability if point won.
    
    Args:
        player_won_point: True if player won this point
        p_win_match: Match-win prob if player wins this point
        p_lose_match: Match-win prob if player loses this point
    
    Returns:
        Leverage value (0 or positive difference)
    
    Formula (Eq. 3-4 in paper):
        L_t = P_win(t) - P_lose(t)  [if won]
        L_t = 0                      [if lost]
    
    Key insight: Only credit momentum when player wins.
    This captures "clutch" moments (high leverage on break points).
    """
    if not player_won_point:
        return 0.0
    
    leverage = p_win_match - p_lose_match
    return max(leverage, 0.0)  # Clip at 0 (only positive leverage credited)
```

**Integration into Current System**:
- Compute `p_win_match` and `p_lose_match` from current score using existing Markov chain
- Only credit leverage on winning points
- This naturally highlights break points (high leverage swings)

---

### 3. Momentum Calculation (Layer 3)

**Purpose**: Convert discrete leverage points into continuous momentum signal

**Implementation**:

```python
def calculate_momentum_ewma(
    leverage_history: list[float],
    alpha: float = 3.4
) -> float:
    """
    Calculate momentum as EWMA of leverage stream.
    
    Args:
        leverage_history: List of leverage values [L_1, L_2, ..., L_t]
        alpha: Smoothing parameter (default: 3.4, paper's value)
    
    Returns:
        Momentum value (continuous signal)
    
    Formula (Eq. 5 in paper):
        M_X(t) = [Σ (1-α)^i * L_{t-i}] / [Σ (1-α)^i]
        
    ⚠️ CAUTION: Paper uses α=3.4, so (1-α) = -2.4
        This creates negative weights, causing oscillating behavior.
        Treat α as TUNABLE - test empirically!
    
    Recommended tuning:
        - Try α ∈ [0.3, 0.7] for stable decay
        - Paper's α=3.4 may be notation difference or special case
    """
    if not leverage_history:
        return 0.0
    
    t = len(leverage_history)
    numerator = 0.0
    denominator = 0.0
    decay_factor = (1 - alpha)
    
    for i in range(t):
        weight = decay_factor ** i
        numerator += weight * leverage_history[t - 1 - i]
        denominator += weight
    
    momentum = numerator / denominator if denominator > 0 else 0.0
    return momentum
```

**Tuning Strategy**:
```python
# Test different α values to find optimal behavior
for alpha in [0.3, 0.5, 0.7, 1.0, 1.5, 2.0, 3.4]:
    momentum = calculate_momentum_ewma(leverage_history, alpha)
    # Validate: momentum should be bounded, smooth, decay over time
```

---

### 4. Feature Engineering (Layer 4)

**Purpose**: Create feature set for game prediction

**Features Used** (from Table 1, selected subset):

```python
@dataclass
class GamePredictionFeatures:
    """Feature set for XGBoost game-winner prediction."""
    
    # Momentum features
    momentum_difference: float  # M_player1(t) - M_player2(t)
    
    # Serve features  
    serve_indicator: bool  # Who is serving
    
    # Score features
    served_score_diff: float  # Points won when p1 served - points won when p2 served
    received_score_diff: float  # Points won when p1 received - points won when p2 received
    score_diff: float  # p1_score - p2_score
    game_diff: float  # p1_games - p2_games
    
    # Point-by-point features
    point_victor: int  # Last point winner (0 or 1)
    
    # Optional (less reliable data)
    distance_run_diff: float = None  # p1_distance - p2_distance (optional)
    rally_count: int = None  # Rally length (optional)
    
    # Context
    set_number: int = None
    game_number: int = None
    point_number: int = None
```

**Time-Series Feature Extraction**:
```python
def extract_time_series_features(feature_values: list[float], window: int = 5):
    """
    Extract rolling statistics from features (window=5 points).
    
    Outputs:
    - mean: Average over window
    - kurtosis: Tail weight (extreme events)
    - skewness: Asymmetry
    - derivative_mean: Rate of change
    - integral: Cumulative sum (area under curve)
    
    Paper achieved 85.2% accuracy using this approach.
    """
    if len(feature_values) < window:
        return None
    
    recent = feature_values[-window:]
    return {
        'mean': np.mean(recent),
        'kurtosis': stats.kurtosis(recent),
        'skewness': stats.skew(recent),
        'derivative_mean': np.mean(np.diff(recent)),
        'integral': np.sum(recent)
    }
```

---

## 📁 File Modifications Required

### 1. `src/models/probabilities.py` - Add Momentum Engine

**New Functions**:
- `calculate_rolling_point_win_probability()` - Layer 1
- `calculate_leverage()` - Layer 2
- `calculate_momentum_ewma()` - Layer 3
- `extract_game_prediction_features()` - Layer 4
- `MomentumTracker` class - Maintains state across points

**Changes to Existing Functions**:
- Modify `next_point_probability()` to optionally return win/lose counterfactuals
- Add momentum cache to `next_game_probability()` (optional, for XGBoost integration)

---

### 2. `src/pages/tennis.py` - UI Integration

**New Session State**:
```python
st.session_state.setdefault('momentum_history', [])
st.session_state.setdefault('leverage_history', [])
st.session_state.setdefault('rolling_point_wins', {'p1_serve': [], 'p2_serve': []})
```

**New Display Sections**:
1. **🚀 Momentum Tracker** - Real-time momentum visualization
2. **⚡ Leverage Analysis** - High-impact points visualization
3. **🎯 Game Winner Prediction** - XGBoost prediction (if implementing)

---

### 3. `tests/test_momentum_features.py` - NEW

**Test Cases**:
```
✓ test_rolling_point_win_probability()
✓ test_leverage_on_serve_wins()
✓ test_leverage_clipping()
✓ test_momentum_ewma_decay()
✓ test_momentum_alpha_sensitivity()
✓ test_feature_extraction_window()
✓ test_psychological_reversal_detection()
✓ test_break_point_momentum_spike()
```

---

## 🎯 Implementation Phases

### Phase 1: Core Momentum Calculation (Days 1-2)
- Implement Layers 1-3 (point-win prob, leverage, momentum EWMA)
- Add unit tests
- Validate against paper's match example

### Phase 2: Feature Engineering (Day 3)
- Implement Layer 4 feature set
- Add time-series extraction
- Integrate with existing game predictions

### Phase 3: UI & Visualization (Day 4)
- Add momentum charts to tennis.py
- Show leverage breakdown by point
- Display psychological reversal warnings

### Phase 4: XGBoost Integration (Optional, Days 5-6)
- Train classifier on Wimbledon 2023 data (if available)
- Compare to current Markov chain approach
- Report accuracy improvements

### Phase 5: Testing & Documentation (Days 6-7)
- Comprehensive test suite
- Accuracy comparison to v1.0
- Update all documentation
- Deploy to production

---

## ⚠️ Known Ambiguities & Mitigations

### Ambiguity #1: P_win(t) and P_lose(t) Definition
**Paper's Issue**: Not fully specified  
**Our Solution**: Use match-win probability from current score via Markov chain
```python
p_win_match = match_win_probability(score_after_win, point_win_prob)
p_lose_match = match_win_probability(score_after_loss, point_win_prob)
```

### Ambiguity #2: α Parameter in EWMA (Eq. 5)
**Paper's Issue**: α=3.4 creates negative weights (1-3.4=-2.4), unusual for EWMA  
**Our Solution**: Treat as tunable; test α ∈ [0.3, 0.7, 1.0, 1.5, 3.4]
```python
# Unit test ensures momentum stays bounded and smooth
assert 0 <= momentum <= 1.0, "Momentum outside valid range"
assert not any(np.isnan(momentum_history)), "NaN values detected"
```

### Ambiguity #3: Missing XGBoost Hyperparameters
**Paper's Issue**: Bayesian optimization results not reported  
**Our Solution**: Two approaches:
1. Keep Markov chain (interpretable, paper-validated)
2. Train lightweight XGBoost on our data (if we have labeled games)

---

## 🚀 Quick Start Implementation Checklist

- [ ] Copy Layer 1 implementation to probabilities.py
- [ ] Copy Layer 2 implementation to probabilities.py
- [ ] Copy Layer 3 implementation to probabilities.py
- [ ] Add MomentumTracker class to probabilities.py
- [ ] Add session state initialization to tennis.py
- [ ] Create test suite (test_momentum_features.py)
- [ ] Run tests: `pytest tests/test_momentum_features.py -v`
- [ ] Add momentum visualization to tennis.py
- [ ] Compare v1.0 vs v2.0 accuracy on test matches
- [ ] Update documentation

---

## 📈 Expected Improvements

**Current System (v1.0)**:
- Simple Markov chains
- Fixed 70/30 blending weights
- No context awareness
- No momentum signal
- Accuracy: Baseline (unknown)

**Paper's Approach**:
- Momentum-aware features
- Dynamic win probability adjustment
- Time-series feature extraction
- Psychological reversal detection
- Accuracy: ~84% game prediction

**Our Implementation (v2.0)**:
- Hybrid: Markov chains + momentum signals
- Dynamic blending weights based on match state
- Early uncertainty handling (psychological reversal)
- Explicit leverage visualization
- Target: 85%+ accuracy (if comparable dataset)

---

## 🔗 Paper References for Implementation

| Component | Paper Equation | Window | Notes |
|-----------|----------------|--------|-------|
| Point-win prob | (1), (2) | 20 pts | +1 smoothing |
| Leverage | (3), (4) | Per point | Clipped at 0 |
| Momentum | (5) | Variable | α=3.4 (tunable) |
| Time-series | N/A | 5 pts | Mean, kurtosis, skewness, derivative, integral |
| Train/test | Table 2-3 | 28/3 | 5-fold CV on train |
| Features | Table 1 | N/A | Momentum diff, serve, score deltas |

---

## ✅ Success Criteria

1. ✓ All momentum calculations match paper's formulas
2. ✓ Unit tests pass (8/8 test cases)
3. ✓ Momentum values bounded and stable
4. ✓ Break points show momentum spikes
5. ✓ Visual alignment with paper's match visualization
6. ✓ Game prediction accuracy ≥ paper baseline
7. ✓ Zero breaking changes to existing functionality
8. ✓ Comprehensive documentation

---

## 🎓 References

- Wang, L., Chen, P., & Sabir, Q.U.A. (2024). Tennis Game Dynamic Prediction Model Based on Players' Momentum. *Applied Mathematics*, 5(3), 77.
- Markov chain methodology: From v1.0 Restoration Point
- Current implementation: v1.0 backed up in RESTORATION_POINT_v1.0.md
