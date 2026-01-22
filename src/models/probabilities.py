"""Core probability calculations for tennis matches."""

from typing import Optional, Tuple, Dict
from src.tennis_schema import MatchSnapshot


def get_server_serve_point_win_pct(snapshot: MatchSnapshot) -> Optional[float]:
    """Get serve-point-win % for the current server (blended with priors)."""
    if snapshot.server is None:
        return None

    if snapshot.server == "A":
        live_pct = snapshot.player_a.get_serve_point_win_pct()
        prior = snapshot.generic_prior_serve_point_win
    else:
        live_pct = snapshot.player_b.get_serve_point_win_pct()
        prior = snapshot.generic_prior_serve_point_win

    if live_pct is None:
        return prior

    # Blend live data with prior using configurable weight
    w = snapshot.blending_weight_live
    return w * live_pct + (1 - w) * prior


def get_receiver_serve_point_win_pct(snapshot: MatchSnapshot) -> Optional[float]:
    """Receiver win % on this serve = 1 - server_win_pct."""
    server_pct = get_server_serve_point_win_pct(snapshot)
    if server_pct is None:
        return None
    return 1 - server_pct


def point_score_to_index(score: Optional[str]) -> Optional[int]:
    """Convert point score ('0', '15', '30', '40', 'AD') to state index."""
    if score is None:
        return None
    score_map = {"0": 0, "15": 1, "30": 2, "40": 3, "AD": 4}
    return score_map.get(score)


def next_point_probability(
    snapshot: MatchSnapshot,
) -> Tuple[Optional[float], Optional[float], Optional[str]]:
    """
    Compute P(server wins next point) and P(receiver wins next point).
    Returns (p_server, p_receiver, note).
    """
    p_server = get_server_serve_point_win_pct(snapshot)
    if p_server is None:
        return None, None, "Missing server stats"

    p_receiver = 1 - p_server
    note = "Based on current server's serve performance"
    return p_server, p_receiver, note


def next_game_probability(
    snapshot: MatchSnapshot,
) -> Tuple[Optional[float], Optional[float], Optional[Dict], Optional[str]]:
    """
    Compute P(server holds) and P(receiver breaks) for current game.
    Also compute likely final game scores.
    Returns (p_hold, p_break, score_dist, note).
    """
    p_server = get_server_serve_point_win_pct(snapshot)
    if p_server is None or snapshot.is_tiebreak:
        return None, None, None, "Missing server stats or in tiebreak"

    # Use Markov chain to compute exact game-win probability
    # State: (score_server, score_receiver)
    # Terminal states: (4, 0), (4, 1), (4, 2), (3, 3->deuce variants), etc.

    memo = {}

    def game_prob(s_pts: int, r_pts: int) -> float:
        """Recursive: probability server wins from this point score."""
        if (s_pts, r_pts) in memo:
            return memo[(s_pts, r_pts)]

        # Terminal states
        # Need 4+ points and 2+ lead to win
        if s_pts >= 4 and s_pts - r_pts >= 2:
            return 1.0  # Server won
        if r_pts >= 4 and r_pts - s_pts >= 2:
            return 0.0  # Receiver won
        
        # Deuce or early: both < 4 or at 3-3, 4-4, etc.
        # Handle bounded recursion: cap recursion depth
        if s_pts > 10 or r_pts > 10:
            # At very high point scores, use asymptotic approximation
            # Higher server point %, they'll eventually win
            return p_server if p_server > 0.5 else (1 - p_server)

        # Recursive case
        result = (
            p_server * game_prob(s_pts + 1, r_pts) 
            + (1 - p_server) * game_prob(s_pts, r_pts + 1)
        )
        memo[(s_pts, r_pts)] = result
        return result

    # Compute from current state
    s_idx = point_score_to_index(snapshot.point_score_a) or 0
    r_idx = point_score_to_index(snapshot.point_score_b) or 0
    p_hold = game_prob(s_idx, r_idx)
    p_break = 1 - p_hold

    # Compute likely final scores (brute-force simulation)
    score_dist = _simulate_game_final_scores(p_server, s_idx, r_idx, n_sims=5000)

    note = "Using Markov chain for exact game probability"
    return p_hold, p_break, score_dist, note


def _simulate_game_final_scores(
    p_server: float, s_pts: int, r_pts: int, n_sims: int = 1000
) -> Dict[str, float]:
    """Simulate game outcomes to get likely final scores."""
    import random

    score_map = {0: "0", 1: "15", 2: "30", 3: "40"}
    outcomes = {}

    for _ in range(n_sims):
        s, r = s_pts, r_pts
        while True:
            if s >= 4 and s - r >= 2:
                outcome = f"Server wins ({score_map.get(s, str(s))}–{score_map.get(r, str(r))})"
                break
            elif r >= 4 and r - s >= 2:
                outcome = f"Receiver wins ({score_map.get(s, str(s))}–{score_map.get(r, str(r))})"
                break
            else:
                if random.random() < p_server:
                    s += 1
                else:
                    r += 1

        outcomes[outcome] = outcomes.get(outcome, 0) + 1

    # Convert to probabilities, keep top 5
    total = n_sims
    probs = {k: v / total for k, v in outcomes.items()}
    top_5 = dict(sorted(probs.items(), key=lambda x: -x[1])[:5])
    return top_5


def next_three_games_forecast(
    snapshot: MatchSnapshot,
) -> Tuple[Optional[Dict], Optional[str]]:
    """
    Forecast outcomes of the next 3 games in the current set.
    Returns (forecast_dict, note).
    forecast_dict contains:
    - "p_a_game1", "p_b_game1", ..., "p_a_game3", "p_b_game3"
    - "set_score_dist": likely set scores after 3 games
    """
    if snapshot.server is None:
        return None, "Missing server info"

    p_hold_a = _hold_probability_for_player(snapshot, "A")
    p_hold_b = _hold_probability_for_player(snapshot, "B")

    if p_hold_a is None or p_hold_b is None:
        return None, "Missing serve stats"

    # Simple forecast: alternate serves, compute hold prob for each
    forecast = {}
    server = snapshot.server
    current_games = {"A": snapshot.games_in_set_a or 0, "B": snapshot.games_in_set_b or 0}

    for game_num in range(1, 4):
        if server == "A":
            forecast[f"p_a_game{game_num}"] = p_hold_a
            forecast[f"p_b_game{game_num}"] = 1 - p_hold_a
            server = "B"
        else:
            forecast[f"p_a_game{game_num}"] = 1 - p_hold_b
            forecast[f"p_b_game{game_num}"] = p_hold_b
            server = "A"

    # Simplified set score distribution (enumerate top outcomes)
    set_dist = _simulate_set_scores(p_hold_a, p_hold_b, current_games, n_sims=1000)
    forecast["set_score_dist"] = set_dist

    note = "Next 3 games based on hold/break probabilities"
    return forecast, note


def _hold_probability_for_player(snapshot: MatchSnapshot, player: str) -> Optional[float]:
    """Get hold probability when this player serves."""
    if player == "A":
        p_serve = snapshot.player_a.get_serve_point_win_pct()
    else:
        p_serve = snapshot.player_b.get_serve_point_win_pct()

    if p_serve is None:
        return None

    # Hold prob ≈ server_win_pct ^ 4 (simplification; exact is Markov)
    # For now, use Markov from initial (0, 0)
    memo = {}

    def game_prob(s_pts: int, r_pts: int) -> float:
        if (s_pts, r_pts) in memo:
            return memo[(s_pts, r_pts)]
        
        # Terminal states
        if s_pts >= 4 and s_pts - r_pts >= 2:
            return 1.0
        if r_pts >= 4 and r_pts - s_pts >= 2:
            return 0.0
        
        # Recursion depth cap: if points are too high, use asymptotic approximation
        if s_pts > 10 or r_pts > 10:
            # Simple approximation: higher serve point % → higher hold probability
            return p_serve
        
        result = (
            p_serve * game_prob(s_pts + 1, r_pts)
            + (1 - p_serve) * game_prob(s_pts, r_pts + 1)
        )
        memo[(s_pts, r_pts)] = result
        return result

    return game_prob(0, 0)


def _simulate_set_scores(
    p_hold_a: float, p_hold_b: float, current_games: Dict, n_sims: int = 1000
) -> Dict[str, float]:
    """Simulate set outcomes from current position."""
    import random

    outcomes = {}
    games_a, games_b = current_games["A"], current_games["B"]

    for _ in range(n_sims):
        g_a, g_b = games_a, games_b
        server = "A" if (games_a + games_b) % 2 == 0 else "B"

        for _ in range(3):
            if server == "A":
                if random.random() < p_hold_a:
                    g_a += 1
                else:
                    g_b += 1
                server = "B"
            else:
                if random.random() < p_hold_b:
                    g_b += 1
                else:
                    g_a += 1
                server = "A"

        outcome = f"{g_a}–{g_b}"
        outcomes[outcome] = outcomes.get(outcome, 0) + 1

    probs = {k: v / n_sims for k, v in outcomes.items()}
    top = dict(sorted(probs.items(), key=lambda x: -x[1])[:5])
    return top


def set_win_probability(snapshot: MatchSnapshot) -> Tuple[Optional[float], Optional[str]]:
    """Compute P(player A wins current set) from current state."""
    if snapshot.games_in_set_a is None or snapshot.games_in_set_b is None:
        return None, "Missing games in set"

    p_hold_a = _hold_probability_for_player(snapshot, "A")
    p_hold_b = _hold_probability_for_player(snapshot, "B")

    if p_hold_a is None or p_hold_b is None:
        return None, "Missing serve stats"

    # Markov chain for set
    memo = {}

    def set_prob(g_a: int, g_b: int, serving: str) -> float:
        """Prob player A wins set from (g_a, g_b) with serving."""
        if (g_a, g_b, serving) in memo:
            return memo[(g_a, g_b, serving)]

        # Terminal: first to 6 with 2+ lead
        if g_a >= 6 and g_a - g_b >= 2:
            return 1.0
        if g_b >= 6 and g_b - g_a >= 2:
            return 0.0
        # Tiebreak at 6-6
        if g_a == 6 and g_b == 6:
            p_a_tb = _tiebreak_win_prob(p_hold_a, p_hold_b)
            return p_a_tb

        # Prevent infinite recursion with game count cap
        if g_a > 12 or g_b > 12:
            # At very high game scores, approximation
            return p_hold_a if p_hold_a > 0.5 else (1 - p_hold_a)

        # Recursive
        if serving == "A":
            result = (
                p_hold_a * set_prob(g_a + 1, g_b, "B")
                + (1 - p_hold_a) * set_prob(g_a, g_b + 1, "B")
            )
        else:
            result = (
                p_hold_b * set_prob(g_a, g_b + 1, "A")
                + (1 - p_hold_b) * set_prob(g_a + 1, g_b, "A")
            )

        memo[(g_a, g_b, serving)] = result
        return result

    # Determine who serves next
    games_played = snapshot.games_in_set_a + snapshot.games_in_set_b
    next_server = "A" if games_played % 2 == 0 else "B"

    p_a_set = set_prob(snapshot.games_in_set_a, snapshot.games_in_set_b, next_server)
    return p_a_set, "Using set-level Markov chain"


def match_win_probability(snapshot: MatchSnapshot) -> Tuple[Optional[float], Optional[str]]:
    """Compute P(player A wins match) from current state."""
    if snapshot.sets_won_a is None or snapshot.sets_won_b is None:
        return None, "Missing sets won"

    p_a_set, _ = set_win_probability(snapshot)
    if p_a_set is None:
        return None, "Cannot compute set win probability"

    sets_to_win = (snapshot.best_of_sets // 2) + 1
    memo = {}

    def match_prob(sets_a: int, sets_b: int) -> float:
        """Prob A wins match from this set count."""
        if (sets_a, sets_b) in memo:
            return memo[(sets_a, sets_b)]

        # Terminal
        if sets_a >= sets_to_win:
            return 1.0
        if sets_b >= sets_to_win:
            return 0.0

        # Recursive
        result = p_a_set * match_prob(sets_a + 1, sets_b) + (
            1 - p_a_set
        ) * match_prob(sets_a, sets_b + 1)
        memo[(sets_a, sets_b)] = result
        return result

    p_a_match = match_prob(snapshot.sets_won_a, snapshot.sets_won_b)
    return p_a_match, "Using match-level Markov chain"


def _tiebreak_win_prob(p_hold_a: float, p_hold_b: float) -> float:
    """Approximate tiebreak win prob (first to 7, 2+ lead)."""
    # Simplification: use weighted serve point win probs
    p_a_point = p_hold_a
    memo = {}

    def tb_prob(pts_a: int, pts_b: int) -> float:
        if (pts_a, pts_b) in memo:
            return memo[(pts_a, pts_b)]
        if pts_a >= 7 and pts_a - pts_b >= 2:
            return 1.0
        if pts_b >= 7 and pts_b - pts_a >= 2:
            return 0.0
        # Recursion depth cap at high points
        if pts_a > 20 or pts_b > 20:
            return p_a_point  # Simple approximation
        result = p_a_point * tb_prob(pts_a + 1, pts_b) + (1 - p_a_point) * tb_prob(
            pts_a, pts_b + 1
        )
        memo[(pts_a, pts_b)] = result
        return result

    return tb_prob(0, 0)


def get_all_game_outcomes(snapshot: MatchSnapshot) -> Tuple[Optional[Dict[str, float]], Optional[float], Optional[str]]:
    """
    Compute probabilities for all possible current game outcomes.
    Returns (outcomes_dict, p_deuce, note).
    
    outcomes_dict: {
        "Server 40–Receiver 0": 0.015,
        "Server 40–Receiver 15": 0.045,
        ... (all possible scores from current position)
    }
    p_deuce: Probability of reaching deuce from current score
    """
    p_server = get_server_serve_point_win_pct(snapshot)
    if p_server is None or snapshot.is_tiebreak:
        return None, None, "Missing server stats or in tiebreak"

    server_name = snapshot.player_a_name if snapshot.server == "A" else snapshot.player_b_name
    receiver_name = snapshot.player_b_name if snapshot.server == "A" else snapshot.player_a_name

    s_idx = point_score_to_index(snapshot.point_score_a) or 0
    r_idx = point_score_to_index(snapshot.point_score_b) or 0

    memo = {}
    deuce_paths = {"count": 0, "total": 0}

    def score_index_to_label(s: int, r: int) -> str:
        """Convert (s, r) indices to tennis score string."""
        score_map = {0: "0", 1: "15", 2: "30", 3: "40"}
        if s < 3 or r < 3:
            return f"{score_map.get(s, str(s))}–{score_map.get(r, str(r))}"
        # Deuce variants
        if s == r:
            return "Deuce"
        elif s > r:
            return "Advantage Server"
        else:
            return "Advantage Receiver"

    def game_outcomes(s_pts: int, r_pts: int) -> Dict[str, float]:
        """Recursive: compute all final score outcomes from this point."""
        if (s_pts, r_pts) in memo:
            return memo[(s_pts, r_pts)]

        # Terminal states
        if s_pts >= 4 and s_pts - r_pts >= 2:
            return {"Server wins": 1.0}
        if r_pts >= 4 and r_pts - s_pts >= 2:
            return {"Receiver wins": 1.0}
        
        # Recursion depth cap
        if s_pts > 10 or r_pts > 10:
            if p_server > 0.5:
                return {"Server wins": 1.0}
            else:
                return {"Receiver wins": 1.0}

        # Recursive case
        left_outcomes = game_outcomes(s_pts + 1, r_pts)
        right_outcomes = game_outcomes(s_pts, r_pts + 1)

        result = {}
        for outcome, prob in left_outcomes.items():
            result[outcome] = result.get(outcome, 0) + p_server * prob
        for outcome, prob in right_outcomes.items():
            result[outcome] = result.get(outcome, 0) + (1 - p_server) * prob

        memo[(s_pts, r_pts)] = result
        return result

    # Compute all outcomes from current position
    all_outcomes = game_outcomes(s_idx, r_idx)

    # Compute probability of reaching deuce
    def reaches_deuce(s_pts: int, r_pts: int) -> float:
        """Probability of reaching deuce from current position."""
        if s_pts >= 4 or r_pts >= 4:
            return 0.0 if not (s_pts >= 3 and r_pts >= 3) else 0.0
        if s_pts == 3 and r_pts == 3:
            return 1.0
        
        if s_pts > 10 or r_pts > 10:
            return 0.0

        left = reaches_deuce(s_pts + 1, r_pts)
        right = reaches_deuce(s_pts, r_pts + 1)
        return p_server * left + (1 - p_server) * right

    p_deuce = reaches_deuce(s_idx, r_idx)

    # Format outcomes nicely
    outcomes_display = {}
    score_index_outcomes = {}
    
    # Simulate paths to build intermediate score probabilities
    def prob_to_score(s_pts: int, r_pts: int, target_s: int, target_r: int) -> float:
        """Probability of reaching target score from current (s_pts, r_pts)."""
        if s_pts == target_s and r_pts == target_r:
            return 1.0
        if s_pts > target_s or r_pts > target_r:
            return 0.0
        if (s_pts >= 4 and s_pts - r_pts >= 2) or (r_pts >= 4 and r_pts - s_pts >= 2):
            return 0.0
        
        if s_pts > 10 or r_pts > 10:
            return 0.0
        
        left = prob_to_score(s_pts + 1, r_pts, target_s, target_r)
        right = prob_to_score(s_pts, r_pts + 1, target_s, target_r)
        return p_server * left + (1 - p_server) * right

    # Enumerate all possible intermediate scores
    for target_s in range(5):
        for target_r in range(5):
            if target_s >= 4 and target_s - target_r < 2:
                continue
            if target_r >= 4 and target_r - target_s < 2:
                continue
            
            prob = prob_to_score(s_idx, r_idx, target_s, target_r)
            if prob > 0.001:  # Only show significant probabilities
                score_label = score_index_to_label(target_s, target_r)
                outcomes_display[f"{server_name} {score_label} {receiver_name}"] = prob

    note = "All possible game outcomes from current score"
    return outcomes_display, p_deuce, note


def forecast_next_game_outcomes(snapshot: MatchSnapshot) -> Tuple[Optional[Dict[str, float]], Optional[str]]:
    """
    Forecast outcomes for the next game (after current game completes).
    Updated point scores based on whether server holds/breaks.
    Returns (outcomes_dict, note).
    """
    # Get current game hold probability
    p_hold, p_break, _, _ = next_game_probability(snapshot)
    if p_hold is None:
        return None, "Cannot compute next game probabilities"

    # Determine who serves next game
    server_name = snapshot.player_a_name if snapshot.server == "A" else snapshot.player_b_name
    receiver_name = snapshot.player_b_name if snapshot.server == "A" else snapshot.player_a_name

    # In next game, we start at 0-0
    # Server is whoever didn't serve current game
    next_server = "B" if snapshot.server == "A" else "A"
    next_server_name = snapshot.player_a_name if next_server == "A" else snapshot.player_b_name

    # Get next server's serve point win %
    if next_server == "A":
        p_next_serve = snapshot.player_a.get_serve_point_win_pct()
    else:
        p_next_serve = snapshot.player_b.get_serve_point_win_pct()

    if p_next_serve is None:
        return None, "Missing next server stats"

    # Blend with prior
    w = snapshot.blending_weight_live
    p_next_serve = w * p_next_serve + (1 - w) * snapshot.generic_prior_serve_point_win

    outcomes = {}
    outcomes[f"{next_server_name} holds serve: {p_hold:.1%}"] = p_hold
    outcomes[f"{receiver_name} breaks: {p_break:.1%}"] = p_break

    note = "Next game after current game completes"
    return outcomes, note


# ============================================================================
# MOMENTUM-BASED PREDICTION (Wang, Chen & Sabir 2024)
# ============================================================================


def calculate_rolling_point_win_probability(
    previous_wins: int,
    window_size: int = 20,
    smoothing: int = 1
) -> float:
    """
    Calculate rolling point-win probability using recent history.
    
    Wang et al. (2024) formulas (Eq. 1-2):
        P₁ = (n_A_PreviousSrvWin + 1) / 20
        P₂ = (n_B_PreviousRcvWin + 1) / 20
    
    Uses Laplace smoothing (+1 in numerator) to handle initial periods.
    Window size = 20 points by default (current + previous 19 points).
    
    Args:
        previous_wins: Count of wins in last `window_size` points
        window_size: Points to consider (default: 20 per paper)
        smoothing: Laplace smoothing value (default: 1)
    
    Returns:
        Probability float ∈ [0, 1]
    
    Example:
        Player A serving, won 12 of last 20 points:
        P_A_serve = (12 + 1) / 20 = 0.65
    """
    probability = (previous_wins + smoothing) / window_size
    return min(max(probability, 0.0), 1.0)  # Clamp to [0, 1]


def calculate_leverage(
    player_won_point: bool,
    p_win_counterfactual: float,
    p_lose_counterfactual: float
) -> float:
    """
    Calculate leverage: counterfactual impact of winning/losing a point.
    
    Wang et al. (2024) formulas (Eq. 3-4):
        L_t = P_win(t) - P_lose(t)  [if player won point]
        L_t = 0                     [if player lost point]
    
    Leverage captures the swing in match-win probability from a single point.
    Only credited when player wins (asymmetric crediting).
    Naturally highlights "clutch" moments (high leverage on break points).
    
    Args:
        player_won_point: True if player won this point
        p_win_counterfactual: Match-win prob if point won
        p_lose_counterfactual: Match-win prob if point lost
    
    Returns:
        Leverage value (≥ 0)
    
    Example:
        Player wins a break point at 4-5 down:
        p_win = 0.45, p_lose = 0.20 → leverage = 0.25 (high!)
        
        Same point won while up 5-4:
        p_win = 0.95, p_lose = 0.85 → leverage = 0.10 (lower)
    """
    if not player_won_point:
        return 0.0
    
    leverage = p_win_counterfactual - p_lose_counterfactual
    return max(leverage, 0.0)  # Clip at 0 (only positive leverage credited)


def calculate_momentum_ewma(
    leverage_history: list,
    alpha: float = 3.4
) -> float:
    """
    Calculate momentum as exponentially-weighted moving average of leverage.
    
    Wang et al. (2024) formula (Eq. 5):
        M_X(t) = [Σ(1-α)^i * L_{t-i}] / [Σ(1-α)^i]  (for i=0 to t-1)
    
    Converts discrete leverage points into continuous momentum signal.
    
    ⚠️  CAUTION: Paper uses α=3.4, so (1-α)=-2.4, creating negative weights.
    This causes oscillating behavior in standard EWMA.
    TREAT α AS TUNABLE - validate empirically with unit tests.
    
    Recommended tuning:
        - Standard EWMA: α ∈ [0.3, 0.7]
        - Paper's value: α = 3.4 (may indicate special definition)
        - Test range: [0.3, 0.5, 0.7, 1.0, 1.5, 3.4]
    
    Args:
        leverage_history: List of leverage values [L_1, L_2, ..., L_t]
        alpha: Smoothing/decay parameter (default: 3.4)
    
    Returns:
        Momentum value (continuous signal)
    
    Example:
        leverage_history = [0.0, 0.05, 0.25, 0.15, 0.0]
        With α=0.5: M_X(5) ≈ 0.12 (weighted recent leverage)
    """
    if not leverage_history or len(leverage_history) == 0:
        return 0.0
    
    t = len(leverage_history)
    numerator = 0.0
    denominator = 0.0
    decay_factor = (1 - alpha)
    
    # Sum from i=0 to t-1, where leverage is indexed backward in time
    for i in range(t):
        weight = decay_factor ** i
        numerator += weight * leverage_history[t - 1 - i]
        denominator += weight
    
    if denominator <= 0:
        return 0.0
    
    momentum = numerator / denominator
    
    # Safety check: momentum should stay bounded
    # (if not, α may be incorrectly tuned or notation differs from standard EWMA)
    momentum = min(max(momentum, -1.0), 1.0)  # Clamp to [-1, 1] for safety
    
    return momentum


def calculate_match_win_probability_counterfactual(
    snapshot: MatchSnapshot,
    point_won_by_server: bool
) -> Optional[float]:
    """
    Calculate match-win probability in a counterfactual scenario.
    
    Used for leverage calculation (Eq. 4 in Wang et al.).
    Computes match-win prob after a hypothetical point outcome.
    
    Args:
        snapshot: Current match state
        point_won_by_server: True if server wins this point
    
    Returns:
        Match-win probability from the new state, or None if cannot compute
    
    Implementation:
        1. Create hypothetical new score after point
        2. Compute match-win probability from that state
        3. Return the probability
    
    Note: This requires updating game/set scores, which may differ
    depending on current point score and game/set context.
    """
    # This is a complex operation; for now return None
    # Full implementation would create new snapshot with updated score
    # and recursively call match_win_probability()
    return None


class MomentumTracker:
    """
    Maintains momentum state across points in a match.
    
    Tracks:
    - Rolling point-win probability (20-point window, separate serve/receive)
    - Leverage history
    - Momentum (EWMA of leverage)
    - Match-level statistics
    
    Integrates with session state for persistence across Streamlit reruns.
    """
    
    def __init__(
        self,
        window_size: int = 20,
        alpha: float = 3.4,
        smoothing: int = 1
    ):
        """Initialize momentum tracker with configurable parameters."""
        self.window_size = window_size
        self.alpha = alpha
        self.smoothing = smoothing
        
        # Rolling windows (separate for serve and receive)
        self.serve_win_history: list[bool] = []  # Did player win when serving?
        self.receive_win_history: list[bool] = []  # Did player win when receiving?
        
        # Leverage and momentum streams
        self.leverage_history: list[float] = []
        self.momentum_history: list[float] = []
        
        # Match metadata
        self.last_point_server: Optional[str] = None
        self.points_played: int = 0
    
    def reset(self):
        """Reset all tracking for a new match."""
        self.serve_win_history.clear()
        self.receive_win_history.clear()
        self.leverage_history.clear()
        self.momentum_history.clear()
        self.last_point_server = None
        self.points_played = 0
    
    def add_point(
        self,
        point_won_by_server: bool,
        is_server_point: bool,
        leverage: float
    ):
        """
        Record a point's outcome and compute momentum update.
        
        Args:
            point_won_by_server: True if server won this point
            is_server_point: True if server was serving
            leverage: Leverage value for this point
        """
        # Track win/loss in appropriate history
        if is_server_point:
            self.serve_win_history.append(point_won_by_server)
        else:
            self.receive_win_history.append(point_won_by_server)
        
        # Record leverage
        self.leverage_history.append(leverage)
        
        # Update momentum (EWMA of leverage)
        new_momentum = calculate_momentum_ewma(self.leverage_history, self.alpha)
        self.momentum_history.append(new_momentum)
        
        self.points_played += 1
    
    def get_rolling_point_win_probability(self, is_serving: bool) -> Optional[float]:
        """
        Get rolling point-win probability for current serving status.
        
        Returns:
            Probability ∈ [0, 1] based on last 20 points, or None if insufficient data
        """
        if is_serving:
            if not self.serve_win_history:
                return None
            recent_serves = self.serve_win_history[-self.window_size:]
            wins = sum(recent_serves)
        else:
            if not self.receive_win_history:
                return None
            recent_receives = self.receive_win_history[-self.window_size:]
            wins = sum(recent_receives)
        
        return calculate_rolling_point_win_probability(
            wins,
            self.window_size,
            self.smoothing
        )
    
    def get_current_momentum(self) -> Optional[float]:
        """Get most recent momentum value."""
        return self.momentum_history[-1] if self.momentum_history else None
    
    def get_momentum_delta(self, last_n: int = 5) -> Optional[float]:
        """
        Get momentum change over last n points.
        
        Returns: momentum[-n] - momentum[-1] if enough data, else None
        """
        if len(self.momentum_history) < last_n + 1:
            return None
        return self.momentum_history[-1] - self.momentum_history[-(last_n + 1)]
    
    def detect_momentum_spike(self, threshold: float = 0.15) -> bool:
        """
        Detect if recent points show momentum spike (clutch moment).
        
        A spike is: recent momentum > threshold above baseline.
        Used to highlight break points and high-leverage moments.
        """
        if len(self.momentum_history) < 5:
            return False
        
        recent_momentum = self.momentum_history[-1]
        baseline_momentum = self.momentum_history[-5]
        
        return (recent_momentum - baseline_momentum) > threshold
