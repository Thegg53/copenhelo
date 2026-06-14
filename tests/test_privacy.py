"""Tests for privacy and data sanitization."""

import pytest
import json
import sys
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

from elo_calculator import (
    filter_opted_in_players,
    sanitize_opponent_names,
    sanitize_tournament_names,
    save_results
)


class TestPrivacySanitization:
    """Test suite for privacy protection and data sanitization."""
    
    def test_filtered_players_exclude_non_opted_in(self, temp_output_dir, opted_in_players):
        """Test that non-opted-in players are excluded from output."""
        if not opted_in_players:
            pytest.skip("No opted-in players in test data")
        
        # Add some sample players
        players = {
            'Player A': {'name': 'Player A', 'rating': 1500},
            'Player B': {'name': 'Player B', 'rating': 1600},
        }
        
        # Simulate Player A being opted-in, Player B not
        opted_in = {'Player A'}
        
        # Filter players
        filtered = filter_opted_in_players(players, opted_in)
        
        assert 'Player A' in filtered
        assert 'Player B' not in filtered
    
    def test_opponent_names_sanitized_in_match_history(self, temp_output_dir):
        """Test that non-opted-in opponent names are replaced with 'Hidden Opponent'."""
        opted_in = {'Player A', 'Player B'}
        
        # Create player with matches against opted-in and non-opted-in players
        players = {
            'Player A': {
                'name': 'Player A',
                'rating': 1500,
                'matches': [
                    {'tournament': '001', 'round': 1, 'opponent': 'Player B', 'result': [2, 0]},
                    {'tournament': '001', 'round': 2, 'opponent': 'Player C', 'result': [2, 1]},
                ],
                'history': [
                    {'opponent': 'Player B', 'result_code': 'W', 'rating_before': 1500, 'rating_after': 1516.0, 'rating_change': 16.0},
                    {'opponent': 'Player C', 'result_code': 'W', 'rating_before': 1516.0, 'rating_after': 1532.0, 'rating_change': 16.0},
                ]
            }
        }
        
        # Sanitize opponent names
        sanitized = sanitize_opponent_names(players, opted_in)
        player_a = sanitized['Player A']
        
        # Check matches
        assert player_a['matches'][0]['opponent'] == 'Player B'  # Opted-in, not hidden
        assert player_a['matches'][1]['opponent'] == 'Hidden Opponent'  # Not opted-in, hidden
        
        # Check history
        assert player_a['history'][0]['opponent'] == 'Player B'  # Opted-in, not hidden
        assert player_a['history'][1]['opponent'] == 'Hidden Opponent'  # Not opted-in, hidden
    
    def test_tournament_player_names_sanitized(self, temp_output_dir):
        """Test that non-opted-in player names are replaced in tournament data."""
        opted_in = {'Player A', 'Player B'}
        
        tournaments = {
            '001': {
                'id': '001',
                'rounds': {
                    '1': {
                        'matches': [
                            {'table': '1', 'player1': 'Player A', 'player2': 'Player B', 'result': [2, 0], 'has_bye': False},
                            {'table': '2', 'player1': 'Player C', 'player2': 'Player D', 'result': [2, 1], 'has_bye': False},
                        ],
                        'processed_at': '2025-08-17T10:00:00'
                    }
                },
                'created_at': '2025-08-17T09:00:00'
            }
        }
        
        # Sanitize tournament names
        sanitized = sanitize_tournament_names(tournaments, opted_in)
        
        matches = sanitized['001']['rounds']['1']['matches']
        
        # First match: both opted-in
        assert matches[0]['player1'] == 'Player A'
        assert matches[0]['player2'] == 'Player B'
        
        # Second match: neither opted-in
        assert matches[1]['player1'] == 'Hidden Player'
        assert matches[1]['player2'] == 'Hidden Player'
    
    def test_no_non_opted_in_names_in_json_output(self, temp_output_dir):
        """Test that no non-opted-in player names appear anywhere in output JSON."""
        opted_in = {'Player A'}
        
        players = {
            'Player A': {
                'name': 'Player A',
                'rating': 1500,
                'matches': [
                    {'opponent': 'SecretPlayer'},
                ],
                'history': [
                    {'opponent': 'SecretPlayer'},
                ]
            }
        }
        
        tournaments = {
            '001': {
                'id': '001',
                'rounds': {
                    '1': {
                        'matches': [
                            {'player1': 'Player A', 'player2': 'SecretPlayer', 'has_bye': False},
                        ],
                        'processed_at': '2025-08-17T10:00:00'
                    }
                },
                'created_at': '2025-08-17T09:00:00'
            }
        }
        
        # Apply privacy filters
        filtered_players = filter_opted_in_players(players, opted_in)
        sanitized_players = sanitize_opponent_names(filtered_players, opted_in)
        sanitized_tournaments = sanitize_tournament_names(tournaments, opted_in)
        
        # Save results
        save_results(sanitized_players, sanitized_tournaments, temp_output_dir)
        
        # Read all output JSON as one string
        with open(temp_output_dir / 'players.json', 'r') as f:
            players_json = f.read()
        with open(temp_output_dir / 'tournaments.json', 'r') as f:
            tournaments_json = f.read()
        
        combined = players_json + tournaments_json
        
        # "SecretPlayer" should NOT appear anywhere
        assert 'SecretPlayer' not in combined
        
        # "Hidden" placeholders should appear
        assert 'Hidden' in combined
