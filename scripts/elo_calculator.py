#!/usr/bin/env python3
"""
ELO Rating Calculator for Tournaments
Parses EventLink HTML files and calculates ELO ratings.
"""

import json
import os
import re
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime
from bs4 import BeautifulSoup
import math


class ELOCalculator:
    """Standard chess ELO rating calculator."""
    
    DEFAULT_RATING = 1600
    K_FACTOR = 32
    
    @staticmethod
    def calculate_new_rating(
        current_rating: float,
        opponent_rating: float,
        score: float,  # 1.0 = win, 0.5 = draw, 0.0 = loss
        k_factor: int = K_FACTOR
    ) -> float:
        """
        Calculate new rating using standard ELO formula.
        
        Args:
            current_rating: Player's current rating
            opponent_rating: Opponent's rating
            score: Match result (1.0 = win, 0.5 = draw, 0.0 = loss)
            k_factor: ELO K-factor (default 32)
            
        Returns:
            New rating
        """
        expected_score = 1 / (1 + math.pow(10, (opponent_rating - current_rating) / 400))
        rating_change = k_factor * (score - expected_score)
        new_rating = current_rating + rating_change
        return round(new_rating, 1)


class TournamentParser:
    """Parses EventLink HTML tournament files."""
    
    @staticmethod
    def parse_tournament_file(filepath: Path) -> List[Dict]:
        """
        Parse a tournament HTML file and extract match data.
        
        Args:
            filepath: Path to .htm file
            
        Returns:
            List of match dictionaries with keys: player1, player2, result, has_bye
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        soup = BeautifulSoup(html_content, 'html.parser')
        matches = []
        
        # Find pairings table
        table = soup.find('table', class_='pairings-table')
        if not table:
            print(f"Warning: No pairings table found in {filepath}")
            return matches
        
        tbody = table.find('tbody')
        if not tbody:
            return matches
        
        # Parse each match row
        for row in tbody.find_all('tr'):
            cells = row.find_all('td', class_='pairings-table__cell')
            if len(cells) < 6:
                continue
            
            # Extract player 1
            player1_cell = cells[2]
            player1_name = TournamentParser._extract_player_name(player1_cell)
            if not player1_name:
                continue
            
            # Extract score
            result_cell = cells[3]
            result = TournamentParser._extract_match_result(result_cell)
            
            # Extract player 2 or bye
            player2_cell = cells[4]
            bye_div = player2_cell.find('div', class_='bye')
            
            if bye_div:
                # Player 1 got a bye
                matches.append({
                    'player1': player1_name,
                    'player2': None,
                    'result': None,
                    'has_bye': True
                })
            else:
                player2_name = TournamentParser._extract_player_name(player2_cell)
                if player2_name:
                    matches.append({
                        'player1': player1_name,
                        'player2': player2_name,
                        'result': result,
                        'has_bye': False
                    })
        
        return matches
    
    @staticmethod
    def _extract_player_name(cell) -> str:
        """Extract player name from table cell."""
        team_div = cell.find('div', class_='team')
        if not team_div:
            return None
        
        name_span = team_div.find('span', class_='team__text')
        if name_span:
            # Get the innermost span with the actual name
            name_elem = name_span.find('span')
            if name_elem:
                return name_elem.get_text(strip=True)
        
        return None
    
    @staticmethod
    def _extract_match_result(cell) -> Tuple[int, int]:
        """
        Extract match result from result cell.
        Returns tuple (player1_wins, player2_wins) or None if no result.
        """
        scores = cell.find_all('div', class_='box-score')
        if len(scores) >= 2:
            try:
                p1_score = int(scores[0].get_text(strip=True))
                p2_score = int(scores[1].get_text(strip=True))
                return (p1_score, p2_score)
            except (ValueError, AttributeError):
                pass
        
        return None


class TournamentDataProcessor:
    """Process tournament data and calculate ratings."""
    
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.players_file = output_dir / 'players.json'
        self.tournaments_file = output_dir / 'tournaments.json'
        
        self.players: Dict[str, Dict] = self._load_or_init_players()
        self.tournaments: Dict[str, Dict] = self._load_or_init_tournaments()
    
    def _load_or_init_players(self) -> Dict[str, Dict]:
        """Load existing player data or initialize empty dict."""
        if self.players_file.exists():
            with open(self.players_file, 'r') as f:
                return json.load(f)
        return {}
    
    def _load_or_init_tournaments(self) -> Dict[str, Dict]:
        """Load existing tournament data or initialize empty dict."""
        if self.tournaments_file.exists():
            with open(self.tournaments_file, 'r') as f:
                return json.load(f)
        return {}
    
    def process_tournament(self, tournament_id: str, round_num: int, matches: List[Dict]):
        """
        Process matches from a round and update ratings.
        
        Args:
            tournament_id: Tournament identifier
            round_num: Round number
            matches: List of match dictionaries
        """
        if tournament_id not in self.tournaments:
            self.tournaments[tournament_id] = {
                'id': tournament_id,
                'rounds': {},
                'created_at': datetime.now().isoformat()
            }
        
        round_key = str(round_num)
        self.tournaments[tournament_id]['rounds'][round_key] = {
            'matches': matches,
            'processed_at': datetime.now().isoformat()
        }
        
        # Process each match
        for match in matches:
            if match['has_bye']:
                # Initialize player if not exists, but don't change rating
                if match['player1'] not in self.players:
                    self.players[match['player1']] = {
                        'name': match['player1'],
                        'rating': ELOCalculator.DEFAULT_RATING,
                        'matches': [],
                        'history': []
                    }
            else:
                # Both players in match
                p1_name = match['player1']
                p2_name = match['player2']
                result = match['result']
                
                # Initialize players if not exist
                if p1_name not in self.players:
                    self.players[p1_name] = {
                        'name': p1_name,
                        'rating': ELOCalculator.DEFAULT_RATING,
                        'matches': [],
                        'history': []
                    }
                if p2_name not in self.players:
                    self.players[p2_name] = {
                        'name': p2_name,
                        'rating': ELOCalculator.DEFAULT_RATING,
                        'matches': [],
                        'history': []
                    }
                
                # Calculate rating change if we have a result
                if result:
                    p1_rating_before = self.players[p1_name]['rating']
                    p2_rating_before = self.players[p2_name]['rating']
                    
                    # Determine scores (1.0 = win, 0.0 = loss, 0.5 = draw)
                    p1_wins, p2_wins = result
                    if p1_wins > p2_wins:
                        p1_score = 1.0
                        p2_score = 0.0
                    elif p1_wins < p2_wins:
                        p1_score = 0.0
                        p2_score = 1.0
                    else:
                        # Draw
                        p1_score = 0.5
                        p2_score = 0.5
                    
                    # Calculate new ratings
                    p1_new_rating = ELOCalculator.calculate_new_rating(
                        p1_rating_before,
                        p2_rating_before,
                        p1_score
                    )
                    p2_new_rating = ELOCalculator.calculate_new_rating(
                        p2_rating_before,
                        p1_rating_before,
                        p2_score
                    )
                    
                    # Update ratings
                    self.players[p1_name]['rating'] = p1_new_rating
                    self.players[p2_name]['rating'] = p2_new_rating
                    
                    # Record match history
                    self.players[p1_name]['history'].append({
                        'tournament': tournament_id,
                        'round': round_num,
                        'opponent': p2_name,
                        'result_code': 'W' if p1_score == 1.0 else ('D' if p1_score == 0.5 else 'L'),
                        'rating_before': p1_rating_before,
                        'rating_after': p1_new_rating,
                        'rating_change': round(p1_new_rating - p1_rating_before, 1),
                        'score': (p1_wins, p2_wins)
                    })
                    self.players[p2_name]['history'].append({
                        'tournament': tournament_id,
                        'round': round_num,
                        'opponent': p1_name,
                        'result_code': 'W' if p2_score == 1.0 else ('D' if p2_score == 0.5 else 'L'),
                        'rating_before': p2_rating_before,
                        'rating_after': p2_new_rating,
                        'rating_change': round(p2_new_rating - p2_rating_before, 1),
                        'score': (p2_wins, p1_wins)
                    })
                    
                    # Record matches played
                    self.players[p1_name]['matches'].append({
                        'tournament': tournament_id,
                        'round': round_num,
                        'opponent': p2_name,
                        'result': result
                    })
                    self.players[p2_name]['matches'].append({
                        'tournament': tournament_id,
                        'round': round_num,
                        'opponent': p1_name,
                        'result': (p2_wins, p1_wins)  # Reversed
                    })
    
    def save(self):
        """Save player and tournament data to JSON files."""
        with open(self.players_file, 'w') as f:
            json.dump(self.players, f, indent=2, default=str)
        
        with open(self.tournaments_file, 'w') as f:
            json.dump(self.tournaments, f, indent=2, default=str)
        
        print(f"Saved {len(self.players)} players to {self.players_file}")
        print(f"Saved {len(self.tournaments)} tournaments to {self.tournaments_file}")


def main():
    """Main entry point."""
    repo_root = Path(__file__).parent.parent
    input_dir = repo_root / 'input'
    output_dir = repo_root / 'output'
    
    processor = TournamentDataProcessor(output_dir)
    
    # Find all tournament directories
    for tournament_dir in sorted(input_dir.iterdir()):
        if not tournament_dir.is_dir():
            continue
        
        tournament_id = tournament_dir.name
        print(f"\nProcessing tournament: {tournament_id}")
        
        # Find all round files
        round_files = sorted(
            tournament_dir.glob('r*.htm'),
            key=lambda p: int(re.search(r'r(\d+)', p.name).group(1))
        )
        
        for round_file in round_files:
            match = re.search(r'r(\d+)', round_file.name)
            if not match:
                continue
            
            round_num = int(match.group(1))
            print(f"  Round {round_num}...", end=' ')
            
            matches = TournamentParser.parse_tournament_file(round_file)
            processor.process_tournament(tournament_id, round_num, matches)
            
            print(f"({len(matches)} matches)")
    
    processor.save()


if __name__ == '__main__':
    main()
