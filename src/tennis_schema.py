"""MatchSnapshot schema and tennis data structures."""

from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime


@dataclass
class PlayerStats:
    """Live match stats for one player."""

    player_name: str
    first_serve_in_pct: Optional[float] = None  # 0-1
    first_serve_points_won_pct: Optional[float] = None  # 0-1
    second_serve_points_won_pct: Optional[float] = None  # 0-1

    # Optional detailed counts
    first_serves_in_count: Optional[int] = None
    first_serves_total_count: Optional[int] = None
    first_serve_points_won_count: Optional[int] = None
    first_serve_points_played_count: Optional[int] = None
    second_serve_points_won_count: Optional[int] = None
    second_serve_points_played_count: Optional[int] = None
    total_service_points_played: Optional[int] = None

    # Optional advanced stats
    return_points_won_pct: Optional[float] = None
    aces: Optional[int] = None
    double_faults: Optional[int] = None
    break_points_faced: Optional[int] = None
    break_points_saved: Optional[int] = None
    break_points_converted: Optional[int] = None
    winners: Optional[int] = None
    unforced_errors: Optional[int] = None

    def get_serve_point_win_pct(self) -> Optional[float]:
        """Compute blended serve-point-win % from components."""
        if (
            self.first_serve_in_pct is None
            or self.first_serve_points_won_pct is None
            or self.second_serve_points_won_pct is None
        ):
            return None
        return (
            self.first_serve_in_pct * self.first_serve_points_won_pct
            + (1 - self.first_serve_in_pct) * self.second_serve_points_won_pct
        )


@dataclass
class MatchSnapshot:
    """Complete immutable snapshot of a match state."""

    # Match metadata
    timestamp: datetime
    match_url: Optional[str] = None
    data_source: str = "manual"  # "url", "paste", "manual"

    # Match structure
    best_of_sets: int = 3
    player_a_name: str = "Player A"
    player_b_name: str = "Player B"

    # Current match state (REQUIRED for meaningful output)
    sets_won_a: Optional[int] = None
    sets_won_b: Optional[int] = None
    current_set_number: Optional[int] = None

    # Current game state (REQUIRED)
    games_in_set_a: Optional[int] = None
    games_in_set_b: Optional[int] = None
    is_tiebreak: bool = False
    tiebreak_points_a: Optional[int] = None
    tiebreak_points_b: Optional[int] = None

    # Current point state (REQUIRED)
    # Standard: 0, 15, 30, 40, "AD"
    point_score_a: Optional[str] = None  # "0", "15", "30", "40", "AD"
    point_score_b: Optional[str] = None

    # Server/Receiver
    server: Optional[str] = None  # "A" or "B"

    # Player stats
    player_a: PlayerStats = field(default_factory=lambda: PlayerStats("Player A"))
    player_b: PlayerStats = field(default_factory=lambda: PlayerStats("Player B"))

    # Priors and blending config
    blending_weight_live: float = 0.70  # 0-1
    generic_prior_serve_point_win: float = 0.62  # men's baseline
    use_bayesian: bool = False

    # Ingestion notes
    ingestion_notes: List[str] = field(default_factory=list)

    def is_complete_for_match_probability(self) -> bool:
        """Check if snapshot has minimum data for match probability."""
        required_fields = [
            self.sets_won_a,
            self.sets_won_b,
            self.games_in_set_a,
            self.games_in_set_b,
            self.point_score_a,
            self.point_score_b,
            self.server,
            self.player_a.get_serve_point_win_pct(),
            self.player_b.get_serve_point_win_pct(),
        ]
        return all(f is not None for f in required_fields)

    def is_complete_for_next_point(self) -> bool:
        """Check if snapshot has minimum data for next point probability."""
        required_fields = [
            self.server,
            self.player_a.get_serve_point_win_pct(),
            self.player_b.get_serve_point_win_pct(),
        ]
        return all(f is not None for f in required_fields)

    def missing_required_fields(self) -> List[str]:
        """Return list of missing required fields."""
        missing = []
        if self.sets_won_a is None:
            missing.append("Sets won by Player A")
        if self.sets_won_b is None:
            missing.append("Sets won by Player B")
        if self.games_in_set_a is None:
            missing.append("Games in current set (Player A)")
        if self.games_in_set_b is None:
            missing.append("Games in current set (Player B)")
        if self.point_score_a is None:
            missing.append("Point score (Player A)")
        if self.point_score_b is None:
            missing.append("Point score (Player B)")
        if self.server is None:
            missing.append("Current server")
        if self.player_a.get_serve_point_win_pct() is None:
            missing.append(f"Serve stats for {self.player_a_name}")
        if self.player_b.get_serve_point_win_pct() is None:
            missing.append(f"Serve stats for {self.player_b_name}")
        return missing
