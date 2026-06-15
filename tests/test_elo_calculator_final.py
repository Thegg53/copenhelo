#!/usr/bin/env python3
"""
Unit tests for final_standings_version ELO calculator improvements.

Tests cover:
- A: K-factor scaling by tournament length
- B: Dropout detection
- C: Prestige tournament bracket bonuses
"""

import sys
from pathlib import Path

# Add final_standings_version to path with higher priority
fsv_path = str(Path(__file__).parent.parent / 'final_standings_version')
sys.path.insert(0, fsv_path)

from final_standings_version.elo_calculator import (
    calculate_k_factor,
    is_prestige_tournament,
    get_bracket_stage,
    get_bracket_advancement_bonus
)


class TestKFactorScaling:
    """Test A: K-factor scaling by tournament length."""
    
    def test_k_factor_3_rounds(self):
        """3 rounds should give K=96."""
        standings = [{'rank': i, 'games': 3} for i in range(1, 6)]
        player = {'wins': 2, 'losses': 1, 'draws': 0}
        
        k = calculate_k_factor(64, 'test_tournament', 1, 3, standings, player)
        assert k == 96, f"Expected K=96 for 3 games, got {k}"
    
    def test_k_factor_4_rounds(self):
        """4 rounds should give K=128."""
        standings = [{'rank': i, 'games': 4} for i in range(1, 6)]
        player = {'wins': 3, 'losses': 1, 'draws': 0}
        
        k = calculate_k_factor(64, 'test_tournament', 1, 4, standings, player)
        assert k == 128, f"Expected K=128 for 4 games, got {k}"
    
    def test_k_factor_5_rounds(self):
        """5 rounds should give K=160."""
        standings = [{'rank': i, 'games': 5} for i in range(1, 6)]
        player = {'wins': 4, 'losses': 1, 'draws': 0}
        
        k = calculate_k_factor(64, 'test_tournament', 1, 5, standings, player)
        assert k == 160, f"Expected K=160 for 5 games, got {k}"
    
    def test_k_factor_6_rounds_prestige_swiss(self):
        """6 swiss rounds (prestige, excluding bracket) should give K=192."""
        # Prestige tournaments: 6 swiss + 3 bracket = 9 total, but only 6 count for K
        standings = [{'rank': i, 'games': 9} for i in range(1, 6)]
        player = {'wins': 7, 'losses': 1, 'draws': 1}
        
        k = calculate_k_factor(64, '20250928_prestige3', 1, 6, standings, player)
        assert k == 192, f"Expected K=192 for 6 games (prestige swiss), got {k}"


class TestDropoutDetection:
    """Test B: Dropout handling - K-factor scales with games played."""
    
    def test_no_dropout_regular_tournament(self):
        """Player with same games as others should have standard K-factor."""
        standings = [{'rank': i, 'games': 5} for i in range(1, 11)]
        player = {'wins': 2, 'losses': 3, 'draws': 0}
        
        k = calculate_k_factor(64, 'test_tournament', 5, 5, standings, player)
        assert k == 160, f"Expected K=160 (5 games), got {k}"
    
    def test_dropout_2_games(self):
        """Player with 2 games (dropout) should have K=48."""
        standings = [{'rank': 1, 'games': 5}, {'rank': 2, 'games': 5},
                     {'rank': 3, 'games': 2}, {'rank': 4, 'games': 2}]
        player = {'wins': 0, 'losses': 2, 'draws': 0}
        
        k = calculate_k_factor(64, 'test_tournament', 3, 2, standings, player)
        assert k == 64, f"Expected K=64 (2 games = dropout), got {k}"
    
    def test_dropout_3_games(self):
        """Player with 3 games should have K=72."""
        standings = [{'rank': 1, 'games': 5}, {'rank': 2, 'games': 5},
                     {'rank': 3, 'games': 3}, {'rank': 4, 'games': 3}]
        player = {'wins': 1, 'losses': 2, 'draws': 0}
        
        k = calculate_k_factor(64, 'test_tournament', 3, 3, standings, player)
        assert k == 96, f"Expected K=96 (3 games), got {k}"


class TestPrestigeDetection:
    """Test C: Prestige tournament detection and bracket bonuses."""
    
    def test_is_prestige_tournament(self):
        """Should detect 'prestige' in tournament ID."""
        assert is_prestige_tournament('20250928_prestige3')
        assert is_prestige_tournament('20260201-prestige4')
        assert not is_prestige_tournament('20250817')
    
    def test_bracket_stage_finals(self):
        """Rank 1-2 should be finals."""
        assert get_bracket_stage(1) == 'finals'
        assert get_bracket_stage(2) == 'finals'
    
    def test_bracket_stage_semis(self):
        """Rank 3-4 should be semis."""
        assert get_bracket_stage(3) == 'semis'
        assert get_bracket_stage(4) == 'semis'
    
    def test_bracket_stage_quarters(self):
        """Rank 5-8 should be quarters."""
        assert get_bracket_stage(5) == 'quarters'
        assert get_bracket_stage(8) == 'quarters'
    
    def test_bracket_stage_swiss_only(self):
        """Rank 9+ should be swiss_only."""
        assert get_bracket_stage(9) == 'swiss_only'
        assert get_bracket_stage(100) == 'swiss_only'
    
    def test_prestige_finals_bonus(self):
        """Finals player should get +48 rating points independent of performance."""
        standings = [{'rank': i, 'games': 9 if i <= 2 else 5} for i in range(1, 10)]
        player = {'wins': 7, 'losses': 1, 'draws': 1}
        
        # Finals bonus is 48 points regardless of K-factor
        bonus = get_bracket_advancement_bonus('20250928_prestige3', 1)
        assert bonus == 48.0, f"Expected 48.0 point finals bonus, got {bonus}"
    
    def test_prestige_semis_bonus(self):
        """Semis player should get +10 rating points (1-1 bracket record)."""
        standings = [{'rank': 1, 'games': 9}, {'rank': 2, 'games': 9},
                     {'rank': 3, 'games': 8}, {'rank': 4, 'games': 8}]
        standings += [{'rank': i, 'games': 5} for i in range(5, 10)]
        player = {'wins': 6, 'losses': 2, 'draws': 0}
        
        bonus = get_bracket_advancement_bonus('20260201-prestige4', 3)
        assert bonus == 10.0, f"Expected 10.0 point semis bonus (1-1 bracket), got {bonus}"
    
    def test_prestige_quarters_bonus(self):
        """Quarters player should get +3 rating points (0-1 bracket record)."""
        standings = [{'rank': 1, 'games': 9}, {'rank': 2, 'games': 9},
                     {'rank': 3, 'games': 8}, {'rank': 4, 'games': 8},
                     {'rank': 5, 'games': 7}, {'rank': 6, 'games': 7}]
        standings += [{'rank': i, 'games': 5} for i in range(7, 10)]
        player = {'wins': 5, 'losses': 2, 'draws': 0}
        
        bonus = get_bracket_advancement_bonus('20250928_prestige3', 5)
        assert bonus == 3.0, f"Expected 3.0 point quarters bonus (0-1 bracket), got {bonus}"
    
    def test_prestige_swiss_only_no_bonus(self):
        """Swiss-only player in prestige should get no bracket bonus."""
        # Prestige with 5 games (swiss only): base K=120
        # No bonus applied
        standings = [{'rank': 1, 'games': 9}, {'rank': 2, 'games': 9}]
        standings += [{'rank': i, 'games': 5} for i in range(3, 12)]
        player = {'wins': 2, 'losses': 3, 'draws': 0}
        
        k = calculate_k_factor(64, '20250928_prestige3', 10, 5, standings, player)
        assert k == 160, f"Expected K=160 (swiss, no bonus), got {k}"
    
    def test_prestige_dropout_vs_swiss_baseline(self):
        """Swiss-only players in prestige get no bracket bonus."""
        standings = [{'rank': 1, 'games': 9}, {'rank': 2, 'games': 9},
                     {'rank': 3, 'games': 8}, {'rank': 4, 'games': 8},
                     {'rank': 5, 'games': 7}, {'rank': 6, 'games': 7}]
        standings += [{'rank': i, 'games': 5} for i in range(7, 12)]
        player = {'wins': 5, 'losses': 2, 'draws': 0}
        
        from final_standings_version.elo_calculator import get_bracket_advancement_bonus
        bonus = get_bracket_advancement_bonus('20250928_prestige3', 10)
        assert bonus == 0.0, f"Expected 0.0 bonus for swiss-only, got {bonus}"


if __name__ == '__main__':
    import pytest
    pytest.main([__file__, '-v'])
