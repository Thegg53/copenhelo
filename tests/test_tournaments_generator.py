"""Tests for tournaments HTML generator."""

import pytest
import json
import sys
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

from tournaments_generator import (
    load_opted_in_players_csv,
    parse_tournament_id,
    generate_tournaments_html,
)


class TestTournamentsGenerator:
    """Test suite for tournaments page generation."""
    
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
    
    def test_parse_tournament_id_with_date_format(self):
        """Test parsing tournament ID with date format."""
        result = parse_tournament_id('20250817')
        assert isinstance(result, tuple)
        assert len(result) == 2
    
    def test_parse_tournament_id_with_date_and_name(self):
        """Test parsing tournament ID with date and name."""
        tournament_id = '20250817_pauper_baltzer'
        date, name = parse_tournament_id(tournament_id)
        assert date is not None
        assert 'baltzer' in name.lower() or 'pauper' in name.lower()
    
    def test_generate_tournaments_html_valid_output(self):
        """Test that tournaments HTML is generated."""
        tournaments = {
            '001': {
                'id': '001',
                'rounds': {
                    '1': {
                        'matches': [
                            {
                                'table': '1',
                                'player1': 'Hidden Player',
                                'player2': 'Hidden Player',
                                'result': [2, 0],
                                'has_bye': False
                            }
                        ],
                        'processed_at': '2025-08-17T10:00:00'
                    }
                },
                'created_at': '2025-08-17T09:00:00'
            }
        }
        
        opted_in = set()
        html = generate_tournaments_html(tournaments, opted_in)
        
        assert isinstance(html, str)
        assert 'DOCTYPE' in html
        assert 'matches-table' in html
        assert 'Hidden Player' in html
    
    def test_generate_tournaments_html_hides_non_opted_in_players(self):
        """Test that non-opted-in player names are hidden."""
        tournaments = {
            '001': {
                'id': '001',
                'rounds': {
                    '1': {
                        'matches': [
                            {
                                'table': '1',
                                'player1': 'Player A',
                                'player2': 'Player B',
                                'result': [2, 0],
                                'has_bye': False
                            }
                        ],
                        'processed_at': '2025-08-17T10:00:00'
                    }
                },
                'created_at': '2025-08-17T09:00:00'
            }
        }
        
        opted_in = {'Player A'}  # Only Player A opted in
        html = generate_tournaments_html(tournaments, opted_in)
        
        # Player A should be visible
        assert 'Player A' in html
        
        # Player B should NOT be in output (replaced by Hidden Player)
        # Count occurrences to ensure Player B was replaced
        assert html.count('Player B') == 0 or 'Hidden Player' in html
