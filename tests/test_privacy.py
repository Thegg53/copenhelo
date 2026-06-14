"""Tests for privacy and data sanitization."""

import pytest
import json
import sys
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

from elo_calculator import TournamentDataProcessor


class TestPrivacySanitization:
    """Test suite for privacy protection and data sanitization."""
    
    def test_filtered_players_exclude_non_opted_in(self, temp_output_dir, opted_in_players):
        """Test that non-opted-in players are excluded from output."""
        if not opted_in_players:
            pytest.skip("No opted-in players in test data")
        
        processor = TournamentDataProcessor(temp_output_dir, opt_in_set=opted_in_players)
        
        # Add some sample players
        processor.players = {
            'Player A': {'name': 'Player A', 'rating': 1500},
            'Player B': {'name': 'Player B', 'rating': 1600},
        }
        
        # Simulate Player A being opted-in, Player B not
        opted_in_players.add('Player A')
        processor.opted_in_players = opted_in_players
        
        # Save and check filtering
        processor.save()
        
        # Load the saved players
        with open(temp_output_dir / 'players.json', 'r') as f:
            saved_players = json.load(f)
        
        assert 'Player A' in saved_players
        assert 'Player B' not in saved_players
    
    def test_opponent_names_sanitized_in_match_history(self, temp_output_dir):
        """Test that non-opted-in opponent names are replaced with 'Hidden Opponent'."""
        opted_in = {'Player A', 'Player B'}
        processor = TournamentDataProcessor(temp_output_dir, opt_in_set=opted_in)
        
        # Create player with matches against opted-in and non-opted-in players
        processor.players = {
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
        
        processor.save()
        
        with open(temp_output_dir / 'players.json', 'r') as f:
            saved_players = json.load(f)
        
        player_a = saved_players['Player A']
        
        # Check matches
        assert player_a['matches'][0]['opponent'] == 'Player B'  # Opted-in, not hidden
        assert player_a['matches'][1]['opponent'] == 'Hidden Opponent'  # Not opted-in, hidden
        
        # Check history
        assert player_a['history'][0]['opponent'] == 'Player B'  # Opted-in, not hidden
        assert player_a['history'][1]['opponent'] == 'Hidden Opponent'  # Not opted-in, hidden
    
    def test_tournament_player_names_sanitized(self, temp_output_dir):
        """Test that non-opted-in player names are replaced in tournament data."""
        opted_in = {'Player A', 'Player B'}
        processor = TournamentDataProcessor(temp_output_dir, opt_in_set=opted_in)
        
        processor.tournaments = {
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
        
        processor.save()
        
        with open(temp_output_dir / 'tournaments.json', 'r') as f:
            saved_tournaments = json.load(f)
        
        matches = saved_tournaments['001']['rounds']['1']['matches']
        
        # First match: both opted-in
        assert matches[0]['player1'] == 'Player A'
        assert matches[0]['player2'] == 'Player B'
        
        # Second match: neither opted-in
        assert matches[1]['player1'] == 'Hidden Player'
        assert matches[1]['player2'] == 'Hidden Player'
    
    def test_no_non_opted_in_names_in_json_output(self, temp_output_dir):
        """Test that no non-opted-in player names appear anywhere in output JSON."""
        opted_in = {'Player A'}
        processor = TournamentDataProcessor(temp_output_dir, opt_in_set=opted_in)
        
        processor.players = {
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
        
        processor.tournaments = {
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
        
        processor.save()
        
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
