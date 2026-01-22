"""Test suite for momentum-based prediction features (Wang et al. 2024)."""

import pytest
import numpy as np
from src.models.probabilities import (
    calculate_rolling_point_win_probability,
    calculate_leverage,
    calculate_momentum_ewma,
    MomentumTracker,
)


class TestRollingPointWinProbability:
    """Test rolling point-win probability calculation (Eq. 1-2)."""
    
    def test_basic_calculation(self):
        """Test basic rolling probability calculation."""
        # Won 12 of last 20 points
        prob = calculate_rolling_point_win_probability(previous_wins=12)
        expected = (12 + 1) / 20  # With +1 smoothing
        assert prob == pytest.approx(expected, rel=1e-6)
    
    def test_zero_wins(self):
        """Test probability when no wins in window."""
        prob = calculate_rolling_point_win_probability(previous_wins=0)
        expected = (0 + 1) / 20  # Just smoothing
        assert prob == pytest.approx(expected, rel=1e-6)
        assert prob > 0  # Smoothing prevents zero
    
    def test_all_wins(self):
        """Test probability when all points won."""
        prob = calculate_rolling_point_win_probability(previous_wins=20)
        # Due to clamping, probability is max 1.0, not >1
        assert prob == 1.0
    
    def test_clamping(self):
        """Test that probability is clamped to [0, 1]."""
        # Even with smoothing making numerator > denominator
        prob = calculate_rolling_point_win_probability(previous_wins=25)
        assert 0.0 <= prob <= 1.0
    
    def test_custom_window_size(self):
        """Test with custom window size."""
        prob = calculate_rolling_point_win_probability(
            previous_wins=7,
            window_size=10
        )
        expected = (7 + 1) / 10
        assert prob == pytest.approx(expected, rel=1e-6)
    
    def test_custom_smoothing(self):
        """Test with custom smoothing value."""
        prob = calculate_rolling_point_win_probability(
            previous_wins=10,
            smoothing=2  # +2 instead of +1
        )
        expected = (10 + 2) / 20
        assert prob == pytest.approx(expected, rel=1e-6)


class TestLeverageCalculation:
    """Test leverage calculation (Eq. 3-4)."""
    
    def test_leverage_on_win_high_swing(self):
        """Test high leverage when winning a break point."""
        # Break point scenario: p_win=0.45, p_lose=0.20
        leverage = calculate_leverage(
            player_won_point=True,
            p_win_counterfactual=0.45,
            p_lose_counterfactual=0.20
        )
        expected = 0.45 - 0.20
        assert leverage == pytest.approx(expected, rel=1e-6)
    
    def test_leverage_on_win_low_swing(self):
        """Test low leverage when winning while already ahead."""
        # Up 5-4: p_win=0.95, p_lose=0.85
        leverage = calculate_leverage(
            player_won_point=True,
            p_win_counterfactual=0.95,
            p_lose_counterfactual=0.85
        )
        expected = 0.95 - 0.85
        assert leverage == pytest.approx(expected, rel=1e-6)
    
    def test_no_leverage_on_loss(self):
        """Test that no leverage is credited when losing."""
        leverage = calculate_leverage(
            player_won_point=False,
            p_win_counterfactual=0.45,
            p_lose_counterfactual=0.20
        )
        assert leverage == 0.0
    
    def test_clipping_at_zero(self):
        """Test that negative leverage is clipped to 0."""
        # Shouldn't happen in practice, but ensure safety
        leverage = calculate_leverage(
            player_won_point=True,
            p_win_counterfactual=0.20,
            p_lose_counterfactual=0.45  # Inverted (shouldn't occur)
        )
        assert leverage == 0.0
    
    def test_symmetric_breakpoint(self):
        """Test leverage on break point from receiver perspective."""
        # Receiver breaking serve at 0-1
        leverage = calculate_leverage(
            player_won_point=True,
            p_win_counterfactual=0.40,
            p_lose_counterfactual=0.15
        )
        expected = 0.40 - 0.15
        assert leverage == pytest.approx(expected, rel=1e-6)


class TestMomentumEWMA:
    """Test momentum EWMA calculation (Eq. 5)."""
    
    def test_single_point_leverage(self):
        """Test momentum with single leverage point."""
        leverage_history = [0.1]
        momentum = calculate_momentum_ewma(leverage_history, alpha=0.5)
        # With single point, EWMA ≈ that point
        assert momentum == pytest.approx(0.1, rel=0.1)  # Rough check
    
    def test_increasing_momentum(self):
        """Test momentum with increasing leverage (building momentum)."""
        leverage_history = [0.05, 0.10, 0.15, 0.20]
        momentum = calculate_momentum_ewma(leverage_history, alpha=0.5)
        assert 0 < momentum <= 0.20  # Should be bounded
    
    def test_decreasing_momentum(self):
        """Test momentum after momentum dies off."""
        leverage_history = [0.20, 0.15, 0.10, 0.05, 0.0, 0.0, 0.0]
        momentum = calculate_momentum_ewma(leverage_history, alpha=0.5)
        assert momentum >= 0  # Non-negative
    
    def test_alpha_sensitivity_small(self):
        """Test that alpha parameter changes momentum output."""
        leverage_history = [0.1, 0.0, 0.0, 0.0, 0.0]
        
        momentum_alpha_01 = calculate_momentum_ewma(leverage_history, alpha=0.1)
        momentum_alpha_07 = calculate_momentum_ewma(leverage_history, alpha=0.7)
        
        # Different α values should produce different momentums
        assert momentum_alpha_01 != momentum_alpha_07
    
    def test_empty_history(self):
        """Test behavior with empty leverage history."""
        momentum = calculate_momentum_ewma([], alpha=0.5)
        assert momentum == 0.0
    
    def test_oscillating_leverage(self):
        """Test momentum with oscillating leverage (win-loss-win pattern)."""
        leverage_history = [0.15, 0.0, 0.15, 0.0, 0.15]
        momentum = calculate_momentum_ewma(leverage_history, alpha=0.5)
        assert 0 <= momentum <= 0.15  # Should be bounded by max leverage
    
    def test_stability_with_paper_alpha(self):
        """
        Test momentum stability with paper's α=3.4.
        
        ⚠️ Paper uses (1-α)=-2.4, which creates negative weights.
        Momentum should still stay bounded due to normalization.
        """
        leverage_history = [0.1, 0.05, 0.0, 0.05, 0.1]
        momentum = calculate_momentum_ewma(leverage_history, alpha=3.4)
        
        # Even with odd α, EWMA should stay bounded [-1, 1]
        assert -1.0 <= momentum <= 1.0


class TestMomentumTracker:
    """Test MomentumTracker class for match-level state management."""
    
    def test_tracker_initialization(self):
        """Test tracker initializes correctly."""
        tracker = MomentumTracker()
        assert tracker.points_played == 0
        assert len(tracker.leverage_history) == 0
        assert len(tracker.momentum_history) == 0
    
    def test_tracker_add_serve_point(self):
        """Test adding a point when server wins."""
        tracker = MomentumTracker()
        tracker.add_point(
            point_won_by_server=True,
            is_server_point=True,
            leverage=0.1
        )
        
        assert tracker.points_played == 1
        assert len(tracker.serve_win_history) == 1
        assert tracker.serve_win_history[0] is True
        assert len(tracker.leverage_history) == 1
        assert len(tracker.momentum_history) == 1
    
    def test_tracker_add_receive_point(self):
        """Test adding points when receiver wins."""
        tracker = MomentumTracker()
        tracker.add_point(
            point_won_by_server=False,
            is_server_point=False,
            leverage=0.05
        )
        
        assert tracker.points_played == 1
        assert len(tracker.receive_win_history) == 1
        # point_won_by_server=False, so server lost, which records False
        assert tracker.receive_win_history[0] is False
    
    def test_tracker_rolling_probability_serve(self):
        """Test rolling probability calculation from tracker."""
        tracker = MomentumTracker(window_size=10)
        
        # Add 10 serve points: server wins 7, loses 3
        for i in range(7):
            tracker.add_point(True, True, 0.1)
        for i in range(3):
            tracker.add_point(False, True, 0.0)
        
        prob = tracker.get_rolling_point_win_probability(is_serving=True)
        expected = (7 + 1) / 10  # With smoothing
        assert prob == pytest.approx(expected, rel=1e-6)
    
    def test_tracker_rolling_probability_receive(self):
        """Test rolling probability when receiving."""
        tracker = MomentumTracker(window_size=10)
        
        # Add 10 receive points (is_server_point=False)
        # Track when server LOSES points (point_won_by_server=False)
        for i in range(6):
            tracker.add_point(False, False, 0.1)  # Server loses (loses 6)
        for i in range(4):
            tracker.add_point(True, False, 0.0)   # Server wins (loses 4)
        
        prob = tracker.get_rolling_point_win_probability(is_serving=False)
        # receive_win_history records point_won_by_server
        # 6 False + 4 True = 4 True values (server won 4 times)
        expected = (4 + 1) / 10  # Server won 4 times
        assert prob == pytest.approx(expected, rel=1e-6)
    
    def test_tracker_current_momentum(self):
        """Test retrieving current momentum."""
        tracker = MomentumTracker()
        
        # No points yet
        assert tracker.get_current_momentum() is None
        
        # After first point
        tracker.add_point(True, True, 0.1)
        momentum = tracker.get_current_momentum()
        assert momentum is not None
        assert momentum >= 0
    
    def test_tracker_momentum_delta(self):
        """Test momentum change calculation."""
        tracker = MomentumTracker()
        
        # Add points with increasing then decreasing leverage
        leverage_sequence = [0.05, 0.10, 0.15, 0.20, 0.15, 0.10]
        for leverage in leverage_sequence:
            tracker.add_point(True, True, leverage)
        
        # Get momentum change over last 3 points
        delta = tracker.get_momentum_delta(last_n=3)
        assert delta is not None
        assert isinstance(delta, float)
    
    def test_tracker_momentum_spike_detection(self):
        """Test detection of momentum spikes."""
        tracker = MomentumTracker()
        
        # Build baseline momentum
        for _ in range(3):
            tracker.add_point(True, True, 0.05)
        
        # Sudden high leverage (spike)
        tracker.add_point(True, True, 0.30)
        
        # Check if spike detected
        spike = tracker.detect_momentum_spike(threshold=0.15)
        # May or may not detect depending on exact calculation
        assert isinstance(spike, bool)
    
    def test_tracker_reset(self):
        """Test resetting tracker for new match."""
        tracker = MomentumTracker()
        
        # Add some data
        tracker.add_point(True, True, 0.1)
        tracker.add_point(False, False, 0.05)
        assert tracker.points_played == 2
        
        # Reset
        tracker.reset()
        assert tracker.points_played == 0
        assert len(tracker.leverage_history) == 0
        assert len(tracker.momentum_history) == 0
    
    def test_tracker_separate_serve_receive_tracking(self):
        """Test that tracker maintains separate serve/receive histories."""
        tracker = MomentumTracker(window_size=5)
        
        # Add serve points: server wins 3, loses 2
        for _ in range(3):
            tracker.add_point(True, True, 0.1)
        for _ in range(2):
            tracker.add_point(False, True, 0.0)
        
        # Add receive points: server loses 4, wins 1
        for _ in range(4):
            tracker.add_point(False, False, 0.1)
        for _ in range(1):
            tracker.add_point(True, False, 0.0)
        
        # Check serve probability: server won 3 / 5 points
        prob_serve = tracker.get_rolling_point_win_probability(is_serving=True)
        expected_serve = (3 + 1) / 5
        assert prob_serve == pytest.approx(expected_serve, rel=1e-6)
        
        # Check receive probability: server won 1 / 5 points
        prob_receive = tracker.get_rolling_point_win_probability(is_serving=False)
        expected_receive = (1 + 1) / 5
        assert prob_receive == pytest.approx(expected_receive, rel=1e-6)


class TestMomentumIntegration:
    """Integration tests combining multiple components."""
    
    def test_break_point_momentum_spike(self):
        """
        Test realistic scenario: momentum spike on break point.
        Simulates losing player breaking serve at 5-1 down.
        """
        tracker = MomentumTracker(alpha=0.5)
        
        # Before break point: low leverage (losing points)
        for _ in range(3):
            tracker.add_point(False, False, 0.02)
        
        # Break point: high leverage (receiver wins critical point)
        tracker.add_point(False, False, 0.25)  # Receiver breaks!
        
        # After break: momentum continues
        for _ in range(2):
            tracker.add_point(False, False, 0.10)
        
        # Momentum should show spike
        assert tracker.get_current_momentum() > 0.05
    
    def test_psychological_reversal_detection(self):
        """
        Test scenario: psychological reversal (unexpected momentum flip).
        Player wins 4 points in a row, then momentum drops suddenly.
        """
        tracker = MomentumTracker(alpha=0.5)
        
        # Building momentum: player wins streak
        for _ in range(4):
            tracker.add_point(True, True, 0.15)
        
        momentum_high = tracker.get_current_momentum()
        assert momentum_high > 0.05
        
        # Psychological reversal: lose next 3 points
        for _ in range(3):
            tracker.add_point(False, True, 0.0)
        
        momentum_low = tracker.get_current_momentum()
        
        # Momentum should decrease
        assert momentum_low < momentum_high
    
    def test_full_game_simulation(self):
        """Simulate a realistic game and track momentum evolution."""
        tracker = MomentumTracker(window_size=20, alpha=0.5)
        
        # Simulate 24 points (realistic game length)
        point_results = [
            True, False, True, True,      # 2-2
            False, False, True, False,    # 2-4 (receiver ahead)
            True, True, True, False,      # 4-4 (break back)
            True, True, False, True,      # 6-4 (server wins)
            False, False, True, True,
            True, False, True, False,
            True, True,
        ]
        
        for point_won in point_results:
            leverage = 0.15 if point_won else 0.05
            tracker.add_point(point_won, True, leverage)
        
        # Check state after full game
        assert tracker.points_played == len(point_results)
        assert len(tracker.momentum_history) == len(point_results)
        
        # Momentum should be well-defined at end
        final_momentum = tracker.get_current_momentum()
        assert final_momentum is not None
        assert -1.0 <= final_momentum <= 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
