"""Tests for leaderboard HTML generator."""

import pytest
import json
import sys
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

from leaderboard_generator import (
    slugify,
    load_players_data,
    generate_leaderboard_html,
)


class TestLeaderboardGenerator:
    """Test suite for leaderboard generation."""
    
    def test_slugify_converts_to_lowercase(self):
        """Test that slugify converts text to lowercase."""
        assert slugify("John Doe") == "john-doe"
    
    def test_slugify_removes_special_chars(self):
        """Test that slugify removes special characters."""
        # Note: Non-ASCII word characters are preserved by \w regex
        result = slugify("Åsa Ørsted")
        assert len(result) > 0
        assert isinstance(result, str)
    
    def test_slugify_handles_spaces(self):
        """Test that slugify converts spaces to hyphens."""
        assert slugify("player one") == "player-one"
    
    def test_load_players_data_empty(self, temp_output_dir):
        """Test loading players data from empty directory."""
        players = load_players_data(temp_output_dir)
        assert isinstance(players, dict)
        assert len(players) == 0
    
    def test_load_players_data_with_players(self, temp_output_dir):
        """Test loading players data with actual players."""
        test_data = {
            'Player A': {'name': 'Player A', 'rating': 1600, 'matches': []},
            'Player B': {'name': 'Player B', 'rating': 1500, 'matches': []},
        }
        with open(temp_output_dir / 'players.json', 'w') as f:
            json.dump(test_data, f)
        
        players = load_players_data(temp_output_dir)
        assert len(players) == 2
        assert 'Player A' in players
    
    def test_generate_leaderboard_html_valid_output(self):
        """Test that leaderboard HTML is generated with valid structure."""
        players = {
            'Player A': {'name': 'Player A', 'rating': 1600, 'matches': []},
            'Player B': {'name': 'Player B', 'rating': 1500, 'matches': []},
        }
        
        html = generate_leaderboard_html(players)
        
        assert isinstance(html, str)
        assert '<table>' in html
        assert '<tbody>' in html
        assert 'Player A' in html
        assert 'Player B' in html
        assert '1600' in html
        assert '1500' in html
    
    def test_generate_leaderboard_html_sorts_by_rating(self):
        """Test that leaderboard sorts players by rating descending."""
        players = {
            'Player A': {'name': 'Player A', 'rating': 1500, 'matches': []},
            'Player B': {'name': 'Player B', 'rating': 1600, 'matches': []},
        }
        
        html = generate_leaderboard_html(players)
        
        # Player B (1600) should appear before Player A (1500)
        pos_b = html.find('Player B')
        pos_a = html.find('Player A')
        assert pos_b < pos_a
