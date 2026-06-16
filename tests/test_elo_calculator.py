"""Tests for ELO rating calculations."""

import pytest
import math
import sys
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

from elo_calculator import calculate_new_rating, DEFAULT_RATING, K_FACTOR, DIVISOR


class TestELOCalculator:
    """Test suite for ELO rating calculations."""
    
    def test_default_rating(self):
        """Test that default rating is 1500."""
        assert DEFAULT_RATING == 1500
    
    def test_k_factor(self):
        """Test that K-factor is 32."""
        assert K_FACTOR == 32
    
    def test_calculate_new_rating_win_equal(self):
        """Test rating increase for winning against equal opponent."""
        current_rating = 1500
        opponent_rating = 1500
        score = 1.0  # Win
        
        new_rating = calculate_new_rating(
            current_rating,
            opponent_rating,
            score
        )
        
        # Expected: expected_score = 0.5, rating_change = 32 * (1.0 - 0.5) = +16
        assert new_rating == 1516
    
    def test_calculate_new_rating_loss_equal(self):
        """Test rating decrease for losing against equal opponent."""
        current_rating = 1500
        opponent_rating = 1500
        score = 0.0  # Loss
        
        new_rating = calculate_new_rating(
            current_rating,
            opponent_rating,
            score
        )
        
        # Expected: rating_change = 32 * (0.0 - 0.5) = -16
        assert new_rating == 1484
    
    def test_calculate_new_rating_draw_equal(self):
        """Test rating change for drawing against equal opponent."""
        current_rating = 1500
        opponent_rating = 1500
        score = 0.5  # Draw
        
        new_rating = calculate_new_rating(
            current_rating,
            opponent_rating,
            score
        )
        
        # Expected: rating_change = 32 * (0.5 - 0.5) = 0
        assert new_rating == 1500
    
    def test_calculate_new_rating_win_higher_opponent(self):
        """Test rating increase for winning against stronger opponent."""
        current_rating = 1400
        opponent_rating = 1600
        score = 1.0  # Win
        
        new_rating = calculate_new_rating(
            current_rating,
            opponent_rating,
            score
        )
        
        # Should gain more points for beating stronger player
        assert new_rating > 1416  # More than typical win
    
    def test_calculate_new_rating_loss_lower_opponent(self):
        """Test rating decrease for losing against weaker opponent."""
        current_rating = 1600
        opponent_rating = 1400
        score = 0.0  # Loss
        
        new_rating = calculate_new_rating(
            current_rating,
            opponent_rating,
            score
        )
        
        # Should lose more points for losing to weaker player
        assert new_rating < 1584  # More than typical loss
    
    def test_calculate_new_rating_custom_k_factor(self):
        """Test rating calculation with custom K-factor."""
        current_rating = 1500
        opponent_rating = 1500
        score = 1.0
        k_factor = 16  # Lower K-factor
        
        new_rating = calculate_new_rating(
            current_rating,
            opponent_rating,
            score,
            k_factor=k_factor
        )
        
        # With K=16: rating_change = 16 * 0.5 = +8
        assert new_rating == 1508
    
    def test_expected_score_formula(self):
        """Test expected score calculation is symmetric."""
        rating_a = 1600
        rating_b = 1400
        
        # Using the ELO formula: expected = 1 / (1 + 10^((opponent - player) / DIVISOR))
        # DIVISOR = 1136 (MTG Elo Project standard)
        expected_a_vs_b = 1 / (1 + math.pow(10, (rating_b - rating_a) / DIVISOR))
        expected_b_vs_a = 1 / (1 + math.pow(10, (rating_a - rating_b) / DIVISOR))
        
        # They should sum to 1.0
        assert abs(expected_a_vs_b + expected_b_vs_a - 1.0) < 0.0001
    
    def test_calculate_new_rating_same_rating_both_players(self):
        """Test rating change when both players have same rating."""
        current_rating = 1600
        opponent_rating = 1600
        
        # Win against equal opponent
        new_rating_win = calculate_new_rating(current_rating, opponent_rating, 1.0)
        assert new_rating_win == 1616  # 32 * 0.5 = +16
        
        # Loss against equal opponent
        new_rating_loss = calculate_new_rating(current_rating, opponent_rating, 0.0)
        assert new_rating_loss == 1584  # 32 * -0.5 = -16
    
    def test_divisor_1136_vs_400_difference(self):
        """Test that 1136 divisor produces different results than 400."""
        current_rating = 1500
        opponent_rating = 1700  # 200 point gap
        score = 1.0  # Win
        
        # Calculate with our new divisor (1136)
        new_rating_1136 = calculate_new_rating(current_rating, opponent_rating, score)
        
        # Calculate with old chess divisor (400)
        expected_score_400 = 1 / (1 + math.pow(10, (opponent_rating - current_rating) / 400))
        new_rating_400 = current_rating + K_FACTOR * (score - expected_score_400)
        
        # With 1136 divisor, a 200-point gap is less extreme (~60% vs ~40%)
        # With 400 divisor, a 200-point gap is more extreme (~76% vs ~24%)
        # So the upset win gains less with 1136 than with 400
        assert new_rating_1136 < new_rating_400, \
            f"Expected 1136 divisor ({new_rating_1136}) to give lower gain than 400 divisor ({new_rating_400}) for upset win"
    
    def test_expected_score_200_point_gap(self):
        """Test expected score for 200-point rating gap."""
        higher_rated = 1700
        lower_rated = 1500
        
        # Lower-rated player's expected score against higher-rated
        expected_score = 1 / (1 + math.pow(10, (higher_rated - lower_rated) / DIVISOR))
        
        # With MTG's 1136 divisor: 200-point gap ≈ 60% win rate for higher player
        # So lower player should have ~40% expected win rate
        assert 0.38 < expected_score < 0.42, \
            f"Expected ~40% win rate for 200-point lower player, got {expected_score:.2%}"
