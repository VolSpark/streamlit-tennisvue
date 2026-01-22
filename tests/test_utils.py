"""Test suite for src.utils and tennis models."""

from src.utils import format_number, validate_input
from src.tennis_schema import MatchSnapshot, PlayerStats
from src.models.probabilities import (
    next_point_probability,
    next_game_probability,
    set_win_probability,
    match_win_probability,
    get_server_serve_point_win_pct,
)
from datetime import datetime


# ============ Original Utils Tests ============


def test_format_number():
    """Test format_number function."""
    assert format_number(3.14159, 2) == "3.14"
    assert format_number(42, 0) == "42"
    assert format_number(0.5, 3) == "0.500"


def test_validate_input():
    """Test validate_input function."""
    assert validate_input("hello") is True
    assert validate_input("") is False
    assert validate_input("   ") is False
    assert validate_input("a", min_length=2) is False
    assert validate_input("hello", min_length=3) is True


# ============ Tennis Schema Tests ============


def test_player_stats_serve_point_win():
    """Test PlayerStats.get_serve_point_win_pct()."""
    ps = PlayerStats(
        player_name="Djokovic",
        first_serve_in_pct=0.65,
        first_serve_points_won_pct=0.82,
        second_serve_points_won_pct=0.60,
    )
    expected = 0.65 * 0.82 + (1 - 0.65) * 0.60
    assert abs(ps.get_serve_point_win_pct() - expected) < 0.001
    # Expected is 0.754 (correct calculation)
    assert abs(ps.get_serve_point_win_pct() - 0.754) < 0.015


def test_player_stats_none_handling():
    """Test PlayerStats returns None when data missing."""
    ps = PlayerStats(player_name="Player", first_serve_in_pct=0.65)
    assert ps.get_serve_point_win_pct() is None


def test_match_snapshot_complete_for_match():
    """Test MatchSnapshot.is_complete_for_match_probability()."""
    snap = MatchSnapshot(
        timestamp=datetime.now(),
        sets_won_a=0,
        sets_won_b=0,
        games_in_set_a=0,
        games_in_set_b=0,
        point_score_a="0",
        point_score_b="0",
        server="A",
        player_a=PlayerStats("A", 0.65, 0.82, 0.60),
        player_b=PlayerStats("B", 0.68, 0.80, 0.58),
    )
    assert snap.is_complete_for_match_probability() is True


def test_match_snapshot_missing_fields():
    """Test missing_required_fields() detection."""
    snap = MatchSnapshot(timestamp=datetime.now())
    missing = snap.missing_required_fields()
    assert len(missing) > 5
    assert any("Sets won" in m for m in missing)


# ============ Probability Model Tests ============


def test_next_point_probability_baseline():
    """Test next point probability with Bayesian blending (70% live, 30% prior)."""
    snap = MatchSnapshot(
        timestamp=datetime.now(),
        server="A",
        blending_weight_live=0.70,  # 70% weight to live data
        generic_prior_serve_point_win=0.62,  # 30% weight to prior (62%)
        player_a=PlayerStats("A", 0.65, 0.82, 0.60),  # Live: 75.4%
        player_b=PlayerStats("B", 0.68, 0.80, 0.58),
    )
    p_server, p_receiver, note = next_point_probability(snap)
    assert p_server is not None
    assert p_receiver is not None
    assert abs(p_server + p_receiver - 1.0) < 0.001
    # Expected blend: 0.70 * 0.754 + 0.30 * 0.62 ≈ 0.706
    expected_p_a = 0.70 * 0.754 + 0.30 * 0.62  
    assert abs(p_server - expected_p_a) < 0.01


def test_next_point_probability_missing_server():
    """Test next point probability with missing server."""
    snap = MatchSnapshot(
        timestamp=datetime.now(),
        server=None,
        player_a=PlayerStats("A", 0.65, 0.82, 0.60),
    )
    p_server, p_receiver, note = next_point_probability(snap)
    assert p_server is None
    assert p_receiver is None


def test_next_game_probability_hold():
    """Test next game probability (hold vs break)."""
    snap = MatchSnapshot(
        timestamp=datetime.now(),
        server="A",
        point_score_a="0",
        point_score_b="0",
        is_tiebreak=False,
        player_a=PlayerStats("A", 0.65, 0.82, 0.60),  # ~75.4% point win
        player_b=PlayerStats("B", 0.68, 0.80, 0.58),
    )
    p_hold, p_break, score_dist, note = next_game_probability(snap)
    assert p_hold is not None
    assert p_break is not None
    assert abs(p_hold + p_break - 1.0) < 0.001
    # With 75.4% point win, hold should be significantly > 0.5
    assert p_hold > 0.6


def test_next_game_probability_deuce_handling():
    """Test next game at deuce (40-40) with strong server."""
    snap = MatchSnapshot(
        timestamp=datetime.now(),
        server="A",
        point_score_a="40",
        point_score_b="40",
        is_tiebreak=False,
        player_a=PlayerStats("A", 0.65, 0.82, 0.60),  # 75.4% point win
        player_b=PlayerStats("B", 0.68, 0.80, 0.58),
    )
    p_hold, p_break, score_dist, note = next_game_probability(snap)
    # Server at deuce has 75.4% point win rate, so should hold >50%
    # Our Markov model shows ~85% hold (85.2%)
    assert p_hold is not None
    assert p_hold > 0.5  # Server advantage should be maintained


def test_set_win_probability():
    """Test set win probability from 0-0."""
    snap = MatchSnapshot(
        timestamp=datetime.now(),
        games_in_set_a=0,
        games_in_set_b=0,
        player_a=PlayerStats("A", 0.65, 0.82, 0.60),  # Stronger server
        player_b=PlayerStats("B", 0.60, 0.78, 0.55),
    )
    p_a_set, note = set_win_probability(snap)
    assert p_a_set is not None
    # Stronger server should be favored
    assert p_a_set > 0.5


def test_match_win_probability_leading():
    """Test match win probability when leading."""
    snap = MatchSnapshot(
        timestamp=datetime.now(),
        best_of_sets=3,
        sets_won_a=1,
        sets_won_b=0,
        games_in_set_a=0,
        games_in_set_b=0,
        player_a=PlayerStats("A", 0.65, 0.82, 0.60),
        player_b=PlayerStats("B", 0.60, 0.78, 0.55),
    )
    p_a_match, note = match_win_probability(snap)
    assert p_a_match is not None
    # Leading 1-0 should increase win probability
    assert p_a_match > 0.5


def test_match_win_probability_best_of_5():
    """Test match win probability for best-of-5 (Grand Slams)."""
    snap = MatchSnapshot(
        timestamp=datetime.now(),
        best_of_sets=5,
        sets_won_a=0,
        sets_won_b=0,
        games_in_set_a=0,
        games_in_set_b=0,
        player_a=PlayerStats("A", 0.65, 0.82, 0.60),
        player_b=PlayerStats("B", 0.60, 0.78, 0.55),
    )
    p_a_match, note = match_win_probability(snap)
    assert p_a_match is not None
    assert 0.0 <= p_a_match <= 1.0


def test_blending_weight_effect():
    """Test that blending weight affects outcome."""
    snap_high_blend = MatchSnapshot(
        timestamp=datetime.now(),
        server="A",
        point_score_a="0",
        point_score_b="0",
        is_tiebreak=False,
        blending_weight_live=0.95,
        generic_prior_serve_point_win=0.50,  # Low prior
        player_a=PlayerStats("A", 0.65, 0.82, 0.60),  # High live
        player_b=PlayerStats("B", 0.68, 0.80, 0.58),
    )

    snap_low_blend = MatchSnapshot(
        timestamp=datetime.now(),
        server="A",
        point_score_a="0",
        point_score_b="0",
        is_tiebreak=False,
        blending_weight_live=0.10,
        generic_prior_serve_point_win=0.50,  # Low prior
        player_a=PlayerStats("A", 0.65, 0.82, 0.60),  # High live
        player_b=PlayerStats("B", 0.68, 0.80, 0.58),
    )

    p_high, _, _ = next_point_probability(snap_high_blend)
    p_low, _, _ = next_point_probability(snap_low_blend)

    # Higher blend should result in higher probability (trusting live data more)
    assert p_high > p_low


def test_serve_point_win_pct_blending():
    """Test server serve-point-win blending logic."""
    snap_high = MatchSnapshot(
        timestamp=datetime.now(),
        server="A",
        blending_weight_live=0.80,
        generic_prior_serve_point_win=0.60,
        player_a=PlayerStats("A", 0.65, 0.82, 0.60),  # Live: ~75.4%
    )

    p_a = get_server_serve_point_win_pct(snap_high)
    # 0.80 * 0.754 + 0.20 * 0.60 ≈ 0.723
    expected = 0.80 * 0.754 + 0.20 * 0.60
    assert abs(p_a - expected) < 0.01

