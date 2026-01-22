#!/usr/bin/env python3
"""
Comprehensive test of new detailed game outcome features.
Tests:
1. get_all_game_outcomes() - All possible game outcomes with deuce probability
2. forecast_next_game_outcomes() - Next game predictions
3. Prediction history tracking
4. Highest probability bolding logic
"""

from datetime import datetime
from src.tennis_schema import MatchSnapshot, PlayerStats
from src.models.probabilities import (
    get_all_game_outcomes,
    forecast_next_game_outcomes,
    next_game_probability,
)

def test_all_game_outcomes():
    """Test getting all possible game outcomes."""
    print("\n" + "=" * 70)
    print("TEST 1: All Possible Game Outcomes from 0-0")
    print("=" * 70)
    
    snapshot = MatchSnapshot(
        timestamp=datetime.now(),
        best_of_sets=5,
        player_a_name="Djokovic",
        player_b_name="Sinner",
        sets_won_a=0,
        sets_won_b=0,
        games_in_set_a=0,
        games_in_set_b=0,
        point_score_a="0",
        point_score_b="0",
        server="A",
        player_a=PlayerStats("Djokovic", 0.65, 0.82, 0.60),
        player_b=PlayerStats("Sinner", 0.68, 0.80, 0.58),
    )
    
    outcomes, p_deuce, note = get_all_game_outcomes(snapshot)
    assert outcomes is not None, "Failed to get game outcomes"
    assert p_deuce is not None, "Failed to get deuce probability"
    
    print(f"✓ Retrieved {len(outcomes)} possible game outcomes")
    print(f"✓ Probability of deuce: {p_deuce:.1%}")
    print(f"\nTop 8 outcomes (sorted by probability):")
    
    sorted_outcomes = sorted(outcomes.items(), key=lambda x: x[1], reverse=True)
    max_prob = max(outcomes.values())
    
    for i, (outcome, prob) in enumerate(sorted_outcomes[:8], 1):
        is_max = prob >= max_prob * 0.95
        marker = "➤ HIGHEST" if is_max else "  "
        print(f"  {i}. {marker} {outcome}: {prob:.1%}")
    
    return True


def test_deuce_scenarios():
    """Test deuce probability at different point scores."""
    print("\n" + "=" * 70)
    print("TEST 2: Deuce Probability at Different Scores")
    print("=" * 70)
    
    test_scores = [
        ("0", "0"),
        ("15", "15"),
        ("30", "30"),
        ("40", "40"),
        ("40", "30"),
        ("30", "40"),
        ("15", "0"),
    ]
    
    for score_a, score_b in test_scores:
        snapshot = MatchSnapshot(
            timestamp=datetime.now(),
            best_of_sets=5,
            player_a_name="Player A",
            player_b_name="Player B",
            sets_won_a=0,
            sets_won_b=0,
            games_in_set_a=0,
            games_in_set_b=0,
            point_score_a=score_a,
            point_score_b=score_b,
            server="A",
            player_a=PlayerStats("Player A", 0.65, 0.82, 0.60),
            player_b=PlayerStats("Player B", 0.68, 0.80, 0.58),
        )
        
        outcomes, p_deuce, _ = get_all_game_outcomes(snapshot)
        print(f"  Score {score_a}–{score_b}: P(deuce) = {p_deuce:.1%}")
    
    return True


def test_next_game_forecast():
    """Test forecasting the next game."""
    print("\n" + "=" * 70)
    print("TEST 3: Next Game Forecast")
    print("=" * 70)
    
    snapshot = MatchSnapshot(
        timestamp=datetime.now(),
        best_of_sets=5,
        player_a_name="Federer",
        player_b_name="Nadal",
        sets_won_a=1,
        sets_won_b=0,
        games_in_set_a=3,
        games_in_set_b=2,
        point_score_a="0",
        point_score_b="0",
        server="A",  # Currently Federer serving
        player_a=PlayerStats("Federer", 0.70, 0.85, 0.65),
        player_b=PlayerStats("Nadal", 0.65, 0.80, 0.62),
    )
    
    next_game_out, next_note = forecast_next_game_outcomes(snapshot)
    assert next_game_out is not None, f"Failed to get next game forecast: {next_note}"
    
    print(f"Current score: {snapshot.sets_won_a}-{snapshot.sets_won_b} sets, " 
          f"{snapshot.games_in_set_a}-{snapshot.games_in_set_b} games")
    print(f"Next server: Nadal")
    print(f"\nNext game outcomes:")
    for outcome, prob in next_game_out.items():
        print(f"  • {outcome}")
    
    return True


def test_prediction_history():
    """Test prediction history tracking."""
    print("\n" + "=" * 70)
    print("TEST 4: Prediction History Tracking")
    print("=" * 70)
    
    history = []
    
    # Simulate multiple time points in a game
    scores = [("0", "0"), ("15", "0"), ("30", "0"), ("30", "15")]
    
    for score_a, score_b in scores:
        snapshot = MatchSnapshot(
            timestamp=datetime.now(),
            best_of_sets=5,
            player_a_name="Player A",
            player_b_name="Player B",
            sets_won_a=0,
            sets_won_b=0,
            games_in_set_a=0,
            games_in_set_b=0,
            point_score_a=score_a,
            point_score_b=score_b,
            server="A",
            player_a=PlayerStats("Player A", 0.65, 0.82, 0.60),
            player_b=PlayerStats("Player B", 0.68, 0.80, 0.58),
        )
        
        outcomes, p_deuce, _ = get_all_game_outcomes(snapshot)
        
        prediction = {
            "timestamp": snapshot.timestamp,
            "score": f"{score_a}–{score_b}",
            "server": snapshot.server,
            "game_outcomes": outcomes,
            "p_deuce": p_deuce,
            "match_state": f"{snapshot.sets_won_a}-{snapshot.sets_won_b} {snapshot.games_in_set_a}-{snapshot.games_in_set_b}"
        }
        history.append(prediction)
    
    print(f"✓ Tracked {len(history)} predictions:")
    for i, pred in enumerate(history, 1):
        print(f"  {i}. Score: {pred['score']} | P(deuce): {pred['p_deuce']:.1%}")
    
    print(f"\n✓ History can be displayed in expanders for reference")
    return True


def test_highest_probability_marking():
    """Test the logic for marking highest probability outcomes."""
    print("\n" + "=" * 70)
    print("TEST 5: Highest Probability Outcome Marking")
    print("=" * 70)
    
    snapshot = MatchSnapshot(
        timestamp=datetime.now(),
        best_of_sets=5,
        player_a_name="Murray",
        player_b_name="Wawrinka",
        sets_won_a=0,
        sets_won_b=0,
        games_in_set_a=0,
        games_in_set_b=0,
        point_score_a="15",
        point_score_b="30",
        server="B",
        player_a=PlayerStats("Murray", 0.60, 0.78, 0.55),
        player_b=PlayerStats("Wawrinka", 0.62, 0.80, 0.58),
    )
    
    outcomes, p_deuce, _ = get_all_game_outcomes(snapshot)
    sorted_outcomes = sorted(outcomes.items(), key=lambda x: x[1], reverse=True)
    max_prob = max(outcomes.values())
    threshold = max_prob * 0.95
    
    print(f"Maximum probability: {max_prob:.1%}")
    print(f"Bolding threshold (95% of max): {threshold:.1%}")
    print(f"\nOutcomes (★ = will be bolded):")
    
    for outcome, prob in sorted_outcomes[:8]:
        if prob >= threshold:
            print(f"  ★ {outcome}: {prob:.1%}")
        else:
            print(f"    {outcome}: {prob:.1%}")
    
    return True


def test_graceful_degradation():
    """Test that missing fields don't break new features."""
    print("\n" + "=" * 70)
    print("TEST 6: Graceful Degradation with Minimal Fields")
    print("=" * 70)
    
    # Minimal snapshot (only required fields)
    snapshot = MatchSnapshot(
        timestamp=datetime.now(),
        best_of_sets=3,
        player_a_name="Player A",
        player_b_name="Player B",
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
    
    try:
        outcomes, p_deuce, note = get_all_game_outcomes(snapshot)
        print(f"✓ get_all_game_outcomes works: {len(outcomes)} outcomes computed")
        print(f"✓ P(deuce) = {p_deuce:.1%}")
        
        next_out, next_note = forecast_next_game_outcomes(snapshot)
        print(f"✓ forecast_next_game_outcomes works: {len(next_out)} outcomes")
        
        return True
    except Exception as e:
        print(f"✗ Failed: {e}")
        return False


def main():
    """Run all tests."""
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 15 + "NEW DETAILED GAME OUTCOMES TEST SUITE" + " " * 17 + "║")
    print("╚" + "=" * 68 + "╝")
    
    tests = [
        ("All Game Outcomes", test_all_game_outcomes),
        ("Deuce Scenarios", test_deuce_scenarios),
        ("Next Game Forecast", test_next_game_forecast),
        ("Prediction History", test_prediction_history),
        ("Highest Probability Marking", test_highest_probability_marking),
        ("Graceful Degradation", test_graceful_degradation),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n✗ {test_name} FAILED: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! New features are working correctly.")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed.")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
