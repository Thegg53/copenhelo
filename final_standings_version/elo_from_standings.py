#!/usr/bin/env python3
"""
Calculate ELO ratings from tournament final standings.
Uses simplified USCF performance rating method (field average opponent strength).
"""

import json
import math
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime
from bs4 import BeautifulSoup
import re


class StandingsELOCalculator:
    """Calculate ELO ratings from tournament final standings."""
    
    DEFAULT_RATING = 1500
    K_FACTOR = 40
    
    @staticmethod
    def calculate_performance_rating(
        current_rating: float,
        field_avg_rating: float,
        score: float,  # 0.0 to 1.0, where 1.0 = perfect score
        num_games: int
    ) -> float:
        """
        Calculate performance rating using simplified USCF method.
        
        Find the rating R such that a player with rating R would be expected
        to score exactly 'score' points against the field.
        
        Args:
            current_rating: Player's current rating
            field_avg_rating: Average rating of opponents (excluding this player)
            score: Actual score as fraction (e.g., 3.5/5 = 0.7)
            num_games: Number of games played
            
        Returns:
            Performance rating
        """
        if score == 1.0:
            # Perfect score: performance rating is very high
            return field_avg_rating + 400
        elif score == 0.0:
            # Goose egg: performance rating is very low
            return field_avg_rating - 400
        
        # Binary search for performance rating
        # Find R where expected_score(R vs field_avg) == actual_score
        low = 0
        high = 4000
        
        for _ in range(50):  # Sufficient iterations for convergence
            mid = (low + high) / 2
            expected = 1 / (1 + math.pow(10, (field_avg_rating - mid) / 400))
            
            if expected < score:
                low = mid
            else:
                high = mid
        
        return round((low + high) / 2, 1)
    
    @staticmethod
    def calculate_new_rating(
        current_rating: float,
        performance_rating: float,
        k_factor: int = K_FACTOR
    ) -> float:
        """
        Calculate new rating based on performance rating.
        
        Args:
            current_rating: Player's rating before tournament
            performance_rating: Performance rating from tournament
            k_factor: K-factor (default 40)
            
        Returns:
            New rating
        """
        rating_change = k_factor * (performance_rating - current_rating) / 400
        new_rating = current_rating + rating_change
        return round(new_rating, 1)


class StandingsParser:
    """Parse tournament standings from HTML."""
    
    @staticmethod
    def parse_standings_html(html_file: Path) -> List[Dict]:
        """
        Parse standings table from EventLink HTML file.
        
        Returns:
            List of dicts with keys: name, rank, points, wins, losses, draws, omw, gwp, ogwp
        """
        with open(html_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        soup = BeautifulSoup(html_content, 'html.parser')
        standings = []
        
        # Find standings table
        table = soup.find('table', class_='standings')
        if not table:
            raise ValueError("No standings table found in HTML")
        
        tbody = table.find('tbody')
        if not tbody:
            raise ValueError("No tbody found in standings table")
        
        # Parse each player row
        for row in tbody.find_all('tr'):
            cells = row.find_all('td', class_='standings__cell')
            if len(cells) < 7:
                continue
            
            try:
                rank = int(cells[0].get_text(strip=True))
                name = cells[1].get_text(strip=True)
                points = int(cells[2].get_text(strip=True))
                
                # Parse W/L/D
                wld_text = cells[3].get_text(strip=True)
                wld_match = re.match(r'(\d+)/(\d+)/(\d+)', wld_text)
                if not wld_match:
                    continue
                
                wins = int(wld_match.group(1))
                losses = int(wld_match.group(2))
                draws = int(wld_match.group(3))
                
                omw = cells[4].get_text(strip=True)
                gwp = cells[5].get_text(strip=True)
                ogwp = cells[6].get_text(strip=True)
                
                standings.append({
                    'name': name,
                    'rank': rank,
                    'points': points,
                    'wins': wins,
                    'losses': losses,
                    'draws': draws,
                    'omw': omw,
                    'gwp': gwp,
                    'ogwp': ogwp,
                    'games': wins + losses + draws
                })
            except (ValueError, AttributeError, IndexError) as e:
                continue
        
        return standings


class PlayerRatingsFile:
    """Manage player ratings file."""
    
    def __init__(self, filepath: Path):
        self.filepath = filepath
        self.ratings: Dict[str, float] = {}
        self.load()
    
    def load(self):
        """Load ratings from file."""
        if not self.filepath.exists():
            self.ratings = {}
            return
        
        with open(self.filepath, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                parts = line.rsplit(',', 1)
                if len(parts) == 2:
                    name, rating_str = parts
                    try:
                        self.ratings[name.strip()] = float(rating_str.strip())
                    except ValueError:
                        pass
    
    def get_rating(self, name: str) -> float:
        """Get player rating, default to 1500."""
        return self.ratings.get(name, StandingsELOCalculator.DEFAULT_RATING)
    
    def set_rating(self, name: str, rating: float):
        """Set player rating."""
        self.ratings[name] = rating
    
    def save(self):
        """Save ratings to file."""
        with open(self.filepath, 'w') as f:
            f.write("# Player Ratings\n")
            f.write(f"# Last updated: {datetime.now().isoformat()}\n")
            f.write("# Format: Player Name, Rating\n\n")
            
            for name in sorted(self.ratings.keys()):
                f.write(f"{name}, {self.ratings[name]}\n")


class TournamentProcessor:
    """Process a tournament and update ratings."""
    
    def __init__(self, ratings_file: Path):
        self.ratings_file = PlayerRatingsFile(ratings_file)
        self.calculator = StandingsELOCalculator()
        self.parser = StandingsParser()
    
    def process_tournament(self, standings_html: Path, tournament_name: str = None):
        """
        Process a tournament and update ratings.
        
        Args:
            standings_html: Path to HTML file with standings table
            tournament_name: Optional tournament name for display
        """
        if not tournament_name:
            tournament_name = standings_html.stem
        
        print(f"\n{'='*80}")
        print(f"Processing: {tournament_name}")
        print(f"{'='*80}\n")
        
        # Parse standings
        standings = self.parser.parse_standings_html(standings_html)
        
        if not standings:
            print("ERROR: No standings found in file")
            return
        
        # Calculate field average (excluding each player)
        field_ratings = [self.ratings_file.get_rating(p['name']) for p in standings]
        total_rating = sum(field_ratings)
        
        # Process each player
        results = []
        for player in standings:
            name = player['name']
            games = player['games']
            
            if games == 0:
                continue
            
            # Get current rating
            current_rating = self.ratings_file.get_rating(name)
            
            # Calculate field average excluding this player
            field_avg = (total_rating - current_rating) / (len(standings) - 1)
            
            # Calculate actual score (0.0 to 1.0)
            actual_score = player['points'] / (games * 3)  # Max 3 points per game
            
            # Calculate performance rating
            perf_rating = self.calculator.calculate_performance_rating(
                current_rating,
                field_avg,
                actual_score,
                games
            )
            
            # Calculate new rating
            new_rating = self.calculator.calculate_new_rating(
                current_rating,
                perf_rating,
                k_factor=self.calculator.K_FACTOR
            )
            
            # Update rating
            self.ratings_file.set_rating(name, new_rating)
            
            # Store result for display
            rating_change = new_rating - current_rating
            results.append({
                'name': name,
                'rank': player['rank'],
                'record': f"{player['wins']}-{player['losses']}-{player['draws']}",
                'points': player['points'],
                'old_rating': current_rating,
                'field_avg': field_avg,
                'perf_rating': perf_rating,
                'new_rating': new_rating,
                'change': rating_change
            })
        
        # Sort by rating change (descending)
        results.sort(key=lambda x: x['change'], reverse=True)
        
        # Print table
        self._print_results_table(results)
        
        # Save updated ratings
        self.ratings_file.save()
        print(f"\nRatings saved to: {self.ratings_file.filepath}")
    
    @staticmethod
    def _print_results_table(results: List[Dict]):
        """Pretty print results table."""
        print(f"\n{'Name':<25} {'Rank':<6} {'Record':<12} {'Old Elo':<10} "
              f"{'Field Avg':<12} {'Perf':<10} {'New Elo':<10} {'Change':<10}")
        print("-" * 115)
        
        for r in results:
            change_str = f"+{r['change']:.1f}" if r['change'] >= 0 else f"{r['change']:.1f}"
            print(f"{r['name']:<25} {r['rank']:<6} {r['record']:<12} "
                  f"{r['old_rating']:<10.1f} {r['field_avg']:<12.1f} "
                  f"{r['perf_rating']:<10.1f} {r['new_rating']:<10.1f} {change_str:<10}")


def main():
    """Main entry point."""
    repo_root = Path(__file__).parent.parent
    
    # Path to standings HTML (the one currently open)
    standings_file = repo_root / "final_standings_version" / "EventLink - Standings for Faraos Cigarer Lyngby_ Pauper Turnering.htm"
    
    # Path to player ratings file (local to this folder)
    ratings_file = Path(__file__).parent / "output" / "player_ratings.txt"
    
    if not standings_file.exists():
        print(f"ERROR: Standings file not found: {standings_file}")
        return
    
    # Process tournament
    processor = TournamentProcessor(ratings_file)
    processor.process_tournament(standings_file, "Faraos Cigarer Pauper (2026-05-30)")


if __name__ == '__main__':
    main()
