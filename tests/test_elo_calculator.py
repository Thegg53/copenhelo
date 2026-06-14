"""Tests for ELO rating calculations."""

import pytest
import math
import sys
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

from elo_calculator import ELOCalculator


class TestELOCalculator:
    """Test suite for ELO rating calculations."""
    
    def test_default_rating(self):
        """Test that default rating is 1500."""
        assert ELOCalculator.DEFAULT_RATING == 1500
    
    def test_k_factor(self):
        """Test that K-factor is 32."""
        assert ELOCalculator.K_FACTOR == 32
    
    def test_calculate_new_rating_win_equal(self):
        """Test rating increase for winning against equal opponent."""
        current_rating = 1500
        opponent_rating = 1500
        score = 1.0  # Win
        
        new_rating = ELOCalculator.calculate_new_rating(
            current_rating,
            opponent_rating,
            score
        )
        
        # Expected: expected_score = 0.5, rating_change = 32 * (1.0 - 0.5) = +16
        assert new_rating == 1516.0
    
    def test_calculate_new_rating_loss_equal(self):
        """Test rating decrease for losing against equal opponent."""
        current_rating = 1500
        opponent_rating = 1500
        score = 0.0  # Loss
        
        new_rating = ELOCalculator.calculate_new_rating(
            current_rating,
            opponent_rating,
            score
        )
        
        # Expected: rating_change = 32 * (0.0 - 0.5) = -16
        assert new_rating == 1484.0
    
    def test_calculate_new_rating_draw_equal(self):
        """Test rating change for drawing against equal opponent."""
        current_rating = 1500
        opponent_rating = 1500
        score = 0.5  # Draw
        
        new_rating = ELOCalculator.calculate_new_rating(
            current_rating,
            opponent_rating,
            score
        )
        
        # Expected: rating_change = 32 * (0.5 - 0.5) = 0
        assert new_rating == 1500.0
    
    def test_calculate_new_rating_win_higher_opponent(self):
        """Test rating increase for winning against stronger opponent."""
        current_rating = 1400
        opponent_rating = 1600
        score = 1.0  # Win
        
        new_rating = ELOCalculator.calculate_new_rating(
            current_rating,
            opponent_rating,
            score
        )
        
        # Should gain more points for beating stronger player
        assert new_rating > 1416.0  # More than typical win
    
    def test_calculate_new_rating_loss_lower_opponent(self):
        """Test rating decrease for losing against weaker opponent."""
        current_rating = 1600
        opponent_rating = 1400
        score = 0.0  # Loss
        
        new_rating = ELOCalculator.calculate_new_rating(
            current_rating,
            opponent_rating,
            score
        )
        
        # Should lose more points for losing to weaker player
        assert new_rating < 1584.0  # More than typical loss
    
    def test_calculate_new_rating_custom_k_factor(self):
        """Test rating calculation with custom K-factor."""
        current_rating = 1500
        opponent_rating = 1500
        score = 1.0
        k_factor = 16  # Lower K-factor
        
        new_rating = ELOCalculator.calculate_new_rating(
            current_rating,
            opponent_rating,
            score,
            k_factor=k_factor
        )
        
        # With K=16: rating_change = 16 * 0.5 = +8
        assert new_rating == 1508.0
    
    def test_expected_score_formula(self):
        """Test expected score calculation is symmetric."""
        rating_a = 1600
        rating_b = 1400
        
        # Using the ELO formula: expected = 1 / (1 + 10^((opponent - player) / 400))
        expected_a_vs_b = 1 / (1 + math.pow(10, (rating_b - rating_a) / 400))
        expected_b_vs_a = 1 / (1 + math.pow(10, (rating_a - rating_b) / 400))
        
        # They should sum to 1.0
        assert abs(expected_a_vs_b + expected_b_vs_a - 1.0) < 0.0001
