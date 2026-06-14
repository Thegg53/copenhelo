"""Tests for players HTML generator."""

import pytest
import json
import sys
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

from players_generator import (
    load_opted_in_players_csv,
    generate_player_pages_html,
)


class TestPlayersGenerator:
    """Test suite for player pages generation."""
    
    def test_load_opted_in_players_csv_empty(self, temp_output_dir):
        """Test loading opted-in players from non-existent file."""
        input_dir = temp_output_dir / 'input'
        input_dir.mkdir(exist_ok=True)
        
        opted_in = load_opted_in_players_csv(input_dir)
        assert isinstance(opted_in, set)
        assert len(opted_in) == 0
    
    def test_load_opted_in_players_csv_with_players(self, temp_output_dir):
        """Test loading opted-in players from CSV."""
        input_dir = temp_output_dir / 'input'
        input_dir.mkdir(exist_ok=True)
        
        csv_path = input_dir / 'opt_in.csv'
        csv_path.write_text('Player A\nPlayer B\n')
        
        opted_in = load_opted_in_players_csv(input_dir)
        assert len(opted_in) == 2
        assert 'Player A' in opted_in
        assert 'Player B' in opted_in
    
    def test_generate_player_pages_html_valid_output(self):
        """Test that player pages HTML is generated."""
        players = {
            'Player A': {
                'name': 'Player A',
                'rating': 1600,
                'matches': [],
                'history': []
            }
        }
        
        opted_in = {'Player A'}
        html = generate_player_pages_html(players, opted_in)
        
        assert isinstance(html, str)
        assert 'Player A' in html
        assert 'DOCTYPE' in html
    
    def test_generate_player_pages_html_with_match_history(self):
        """Test that player match history is included in HTML."""
        players = {
            'Player A': {
                'name': 'Player A',
                'rating': 1600,
                'matches': [
                    {'tournament': '001', 'round': 1, 'opponent': 'Player B', 'result': [2, 0]}
                ],
                'history': [
                    {
                        'tournament': '001',
                        'round': 1,
                        'opponent': 'Player B',
                        'result_code': 'W',
                        'rating_before': 1600,
                        'rating_after': 1616.0,
                        'rating_change': 16.0
                    }
                ]
            }
        }
        
        opted_in = {'Player A', 'Player B'}
        html = generate_player_pages_html(players, opted_in)
        
        assert 'Player B' in html
        assert 'W' in html or 'Win' in html
    
    def test_generate_player_pages_html_hides_non_opted_in_opponents(self):
        """Test that non-opted-in opponent names are hidden."""
        players = {
            'Player A': {
                'name': 'Player A',
                'rating': 1600,
                'matches': [
                    {'tournament': '001', 'round': 1, 'opponent': 'Player B', 'result': [2, 0]}
                ],
                'history': [
                    {
                        'tournament': '001',
                        'round': 1,
                        'opponent': 'Player B',
                        'result_code': 'W',
                        'rating_before': 1600,
                        'rating_after': 1616.0,
                        'rating_change': 16.0
                    }
                ]
            }
        }
        
        opted_in = {'Player A'}  # Player B NOT opted in
        html = generate_player_pages_html(players, opted_in)
        
        # Player B should be hidden
        assert 'Player B' not in html
        assert 'Hidden' in html
