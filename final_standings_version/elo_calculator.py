#!/usr/bin/env python3
"""
Calculate ELO ratings from tournament standings.
Reads extracted standings and updates player ratings and tournament data.
"""

import json
import math
import csv
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Set


# Constants
DEFAULT_RATING = 1500
K_FACTOR = 64


def calculate_expected_score(player_rating: float, field_avg_rating: float) -> float:
    """
    Calculate the expected score for a player against the field average.
    
    Uses divisor of 1136 following MTG Elo Project standards:
    - 200-point rating gap = 60% expected win rate
    - (vs chess's 400 divisor where 200-point gap = 76%)
    - Accounts for Magic's high variance compared to chess
    
    Args:
        player_rating: Player's current rating
        field_avg_rating: Average rating of opponents (excluding this player)
        
    Returns:
        Expected score as fraction (0.0 to 1.0)
    """
    return 1.0 / (1.0 + math.pow(10, (field_avg_rating - player_rating) / 1136))


def calculate_performance_rating(
    current_rating: float,
    field_avg_rating: float,
    score: float,  # 0.0 to 1.0, where 1.0 = perfect score
    num_games: int
) -> float:
    """
    Calculate expected score using standard Elo method.
    
    This is a compatibility wrapper. The actual Elo gain now uses
    (actual_score - expected_score) instead of (performance_rating - current_rating).
    
    Args:
        current_rating: Player's current rating
        field_avg_rating: Average rating of opponents (excluding this player)
        score: Actual score as fraction (e.g., 3.5/5 = 0.7)
        num_games: Number of games played
        
    Returns:
        The expected score (for use in standard Elo formula)
    """
    # Return expected score instead of performance rating
    # This is used in the standard Elo formula: gain = K * (actual - expected)
    return calculate_expected_score(current_rating, field_avg_rating)


def calculate_new_rating(
    current_rating: float,
    expected_score: float,
    actual_score: float,
    k_factor: int = K_FACTOR
) -> float:
    """
    Calculate new rating using standard Elo formula.
    
    Args:
        current_rating: Player's rating before tournament
        expected_score: Expected score (from standard Elo calculation)
        actual_score: Actual score achieved (0.0 to 1.0)
        k_factor: K-factor (default 64)
        
    Returns:
        New rating
    """
    rating_change = k_factor * (actual_score - expected_score)
    new_rating = current_rating + rating_change
    return round(new_rating, 1)


def load_players(players_file: Path) -> Dict[str, Dict]:
    """Load players from JSON, or return empty dict if file doesn't exist."""
    if not players_file.exists():
        return {}
    
    with open(players_file, 'r') as f:
        return json.load(f)


def load_tournaments(tournaments_file: Path) -> Dict[str, Dict]:
    """Load tournaments from JSON, or return empty dict if file doesn't exist."""
    if not tournaments_file.exists():
        return {}
    
    with open(tournaments_file, 'r') as f:
        return json.load(f)


def load_opted_in_players(opt_in_file: Path) -> Set[str]:
    """Load opted-in player names from CSV file."""
    if not opt_in_file.exists():
        return set()
    
    with open(opt_in_file, 'r') as f:
        return {line.strip() for line in f if line.strip()}


def save_players(players: Dict, players_file: Path):
    """Save players to JSON file."""
    with open(players_file, 'w') as f:
        json.dump(players, f, indent=2)


def save_tournaments(tournaments: Dict, tournaments_file: Path):
    """Save tournaments to JSON file."""
    with open(tournaments_file, 'w') as f:
        json.dump(tournaments, f, indent=2)


def is_prestige_tournament(tournament_id: str) -> bool:
    """Detect if tournament is a prestige event with bracket stage."""
    return 'prestige' in tournament_id.lower()


def detect_swiss_baseline_games(standings: List[Dict]) -> int:
    """Detect number of swiss rounds by finding min games (usually rank 9+)."""
    if len(standings) <= 8:
        return 0  # All players in bracket, assume pure bracket tournament
    
    # Find minimum games (likely the swiss-only players)
    min_games = min(s['games'] for s in standings[8:])
    return min_games


def get_bracket_stage(rank: int) -> str:
    """Determine which bracket stage a player reached (for prestige tournaments)."""
    if rank <= 2:
        return 'finals'
    elif rank <= 4:
        return 'semis'
    elif rank <= 8:
        return 'quarters'
    else:
        return 'swiss_only'


def detect_swiss_games(standings: List[Dict]) -> int:
    """
    Detect number of swiss rounds by finding games played by rank 9+ players.
    Returns the minimum games (which should be all swiss-only players).
    """
    if len(standings) <= 8:
        return 0  # No swiss-only players, all in bracket
    
    # Find min games in rank 9+ (swiss-only players)
    swiss_games = min(s['games'] for s in standings[8:])
    return swiss_games


def extract_swiss_record(rank: int, wins: int, losses: int, draws: int) -> tuple:
    """
    Extract the swiss-only record for a bracket player.
    In prestige tournaments with 8-player bracket:
    - Rank 1 (champion): 3 bracket games (3 wins)
    - Rank 2 (finalist): 3 bracket games (2 wins, 1 loss)
    - Rank 3-4 (semis): 2 bracket games (1 win, 1 loss)
    - Rank 5-8 (quarters): 1 bracket game (1 loss)
    
    Args:
        rank: Player's final rank (1-8 are bracket)
        wins: Total wins
        losses: Total losses
        draws: Total draws
        
    Returns:
        (swiss_wins, swiss_losses, swiss_draws)
    """
    if rank == 1:
        # Champion: won all 3 bracket games
        return (max(0, wins - 3), losses, draws)
    elif rank == 2:
        # Finalist: won 2, lost 1 in bracket
        return (max(0, wins - 2), max(0, losses - 1), draws)
    elif rank <= 4:
        # Semis loser: won 1, lost 1 in bracket
        return (max(0, wins - 1), max(0, losses - 1), draws)
    elif rank <= 8:
        # Quarters loser: lost 1 in bracket
        return (wins, max(0, losses - 1), draws)
    else:
        # Swiss only: no changes
        return (wins, losses, draws)


def calculate_k_factor(
    base_k: int,
    tournament_id: str,
    rank: int,
    games_played: int,
    standings: List[Dict],
    player: Dict
) -> int:
    """
    Calculate K-factor based on games played.
    
    Formula: K = 32 * games (aligned with MTG Elo Project standards)
    
    This scales with tournament length - more games = more evidence = higher volatility:
    - 2 games (dropout): K=64 → less impact
    - 3 games: K=96
    - 4 games: K=128 ← Standard tournament
    - 5 games: K=160
    - 6 games: K=192 ← Prestige tournament (swiss-only, excluding bracket)
    
    Each game is worth 32 K-factor points. Players are penalized for their 
    losses proportionally to tournament length (more games = more evidence = larger swings).
    
    Note: Prestige tournaments with 9 total games (6 swiss + 3 bracket) use K=32*6=192,
    as only the 6 swiss games count for ELO calculation.
    
    Args:
        base_k: Unused (kept for compatibility)
        tournament_id: Tournament identifier
        rank: Player's final rank
        games_played: Number of games player participated in
        standings: Full standings list (unused)
        player: Player standings dict (unused)
    
    Returns:
        Adjusted K-factor
    """
    # K = 32 * games (MTG Elo Project scaling)
    k = 32 * games_played
    
    return k


def get_bracket_advancement_bonus(tournament_id: str, rank: int) -> float:
    """
    Get flat rating bonus for bracket advancement in prestige tournaments.
    Independent of performance - purely for making the bracket and placement.
    No penalties for losing in bracket - only pure bonuses for reaching stages.
    
    Scaling based on bracket placement:
    - Champion (3-0): +40
    - Runner-up (2-1): +20
    - Semis (1-1): +8
    - Quarters (0-1): +4
    
    Args:
        tournament_id: Tournament identifier
        rank: Player's final rank (1-8 are bracket)
        
    Returns:
        Rating points to add (0 for non-prestige or swiss-only)
    """
    if not is_prestige_tournament(tournament_id):
        return 0.0
    
    if rank == 1:
        return 40.0    # Champion: +40 rating points
    elif rank == 2:
        return 20.0    # Runner-up: +20 rating points
    elif rank <= 4:
        return 8.0     # Semis: +8 rating points
    elif rank <= 8:
        return 4.0     # Quarters: +4 rating points
    else:
        return 0.0     # Swiss-only: no bonus


def get_current_rating(name: str, players: Dict) -> float:
    """Get player's current rating, default to 1500."""
    if name in players:
        return players[name]['rating']
    return DEFAULT_RATING


def process_tournament_standings(
    tournament_id: str,
    tournament_name: str,
    standings: List[Dict],
    players: Dict,
    tournaments: Dict,
    opted_in_players: Set[str]
) -> tuple:
    """
    Process a tournament's standings and calculate ELO changes.
    
    Args:
        tournament_id: Tournament identifier
        tournament_name: Human-readable tournament name
        standings: List of standings dicts
        players: Current players data
        tournaments: Current tournaments data
        
    Returns:
        (updated_players, updated_tournaments, results_for_display)
    """
    # Calculate field average
    field_ratings = [get_current_rating(p['name'], players) for p in standings]
    total_rating = sum(field_ratings)
    
    # Detect number of swiss games for this tournament
    swiss_games = detect_swiss_games(standings)
    
    results = []
    
    for player in standings:
        name = player['name']
        games = player['games']
        
        if games == 0:
            continue
        
        # Get current rating
        current_rating = get_current_rating(name, players)
        
        # Calculate field average excluding this player
        field_avg = (total_rating - current_rating) / (len(standings) - 1)
        
        # For prestige tournaments: extract swiss-only record (remove bracket games for top 8)
        # For other tournaments: use full record
        if is_prestige_tournament(tournament_id):
            swiss_wins, swiss_losses, swiss_draws = extract_swiss_record(
                player['rank'],
                player['wins'],
                player['losses'],
                player['draws']
            )
        else:
            # Non-prestige: use full record
            swiss_wins, swiss_losses, swiss_draws = player['wins'], player['losses'], player['draws']
        
        # Calculate swiss games and points for this player
        swiss_games_played = swiss_wins + swiss_losses + swiss_draws
        swiss_points = swiss_wins * 3 + swiss_draws
        
        # Calculate actual score using swiss-only record
        if swiss_games_played > 0:
            actual_score = swiss_points / (swiss_games_played * 3)
        else:
            actual_score = 0.0
        
        # Calculate expected score using standard Elo method
        expected_score = calculate_performance_rating(
            current_rating,
            field_avg,
            actual_score,
            swiss_games_played
        )
        
        # Calculate adjusted K-factor based on swiss games only
        adjusted_k = calculate_k_factor(
            K_FACTOR,
            tournament_id,
            player['rank'],
            swiss_games_played,
            standings,
            player
        )
        
        # Calculate new rating with adjusted K-factor using standard Elo formula (swiss-only)
        new_rating = calculate_new_rating(current_rating, expected_score, actual_score, adjusted_k)
        
        # Add bracket advancement bonus (independent of performance)
        bracket_bonus = get_bracket_advancement_bonus(tournament_id, player['rank'])
        new_rating_with_bracket = new_rating + bracket_bonus
        
        # Update player data
        if name not in players:
            players[name] = {
                'name': name,
                'rating': new_rating_with_bracket,
                'matches': [],
                'history': []
            }
        else:
            players[name]['rating'] = new_rating_with_bracket
        
        # Add to history
        history_entry = {
            'tournament': tournament_id,
            'date': datetime.now().isoformat(),
            'rank': player['rank'],
            'record': f"{player['wins']}-{player['losses']}-{player['draws']}",
            'points': player['points'],
            'rating_before': current_rating,
            'rating_after': new_rating_with_bracket,
            'change': new_rating_with_bracket - current_rating
        }
        players[name]['history'].append(history_entry)
        
        # Store result for display
        results.append({
            'name': name,
            'rank': player['rank'],
            'record': f"{player['wins']}-{player['losses']}-{player['draws']}",
            'points': player['points'],
            'old_rating': current_rating,
            'field_avg': field_avg,
            'expected_score': expected_score,
            'actual_score': actual_score,
            'new_rating': new_rating_with_bracket,
            'change': new_rating_with_bracket - current_rating
        })
    
    # Sort by rating change
    results.sort(key=lambda x: x['change'], reverse=True)
    
    # Update tournament data
    if tournament_id not in tournaments:
        tournaments[tournament_id] = {
            'id': tournament_id,
            'name': tournament_name,
            'created_at': datetime.now().isoformat(),
            'standings': []
        }
    
    tournaments[tournament_id]['standings'] = standings
    
    return players, tournaments, results


def print_results_table(results: List[Dict], opted_in_players: Set[str]):
    """Pretty print results table, hiding non-opted-in players."""
    print(f"\n{'Name':<25} {'Rank':<6} {'Record':<12} {'Old Elo':<10} "
          f"{'Expected':<10} {'Actual':<10} {'New Elo':<10} {'Change':<10}")
    print("-" * 113)
    
    for r in results:
        display_name = r['name'] if r['name'] in opted_in_players else 'Hidden Player'
        change_str = f"+{r['change']:.1f}" if r['change'] >= 0 else f"{r['change']:.1f}"
        print(f"{display_name:<25} {r['rank']:<6} {r['record']:<12} "
              f"{r['old_rating']:<10.1f} {r['expected_score']:<10.2%} "
              f"{r['actual_score']:<10.2%} {r['new_rating']:<10.1f} {change_str:<10}")


def load_processed_tournaments(csv_file: Path) -> set:
    """
    Load set of already-processed tournament IDs from parsed_events.csv.
    
    Args:
        csv_file: Path to parsed_events.csv
        
    Returns:
        Set of tournament IDs marked as elo_calculated
    """
    if not csv_file.exists():
        return set()
    
    processed = set()
    try:
        with open(csv_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row and row.get('elo_calculated') == 'yes':
                    processed.add(row['tournament_id'])
    except (csv.Error, KeyError):
        pass
    
    return processed


def mark_tournament_processed(csv_file: Path, tournament_id: str):
    """
    Mark a tournament as processed (elo_calculated=yes) in the CSV.
    
    Args:
        csv_file: Path to parsed_events.csv
        tournament_id: Tournament identifier to mark as calculated
    """
    if not csv_file.exists():
        return
    
    # Read all rows
    rows = []
    try:
        with open(csv_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['tournament_id'] == tournament_id:
                    row['elo_calculated'] = 'yes'
                rows.append(row)
    except (csv.Error, KeyError):
        return
    
    # Write all rows back
    try:
        with open(csv_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['timestamp', 'tournament_id', 'players', 'htm_parsed_to_json', 'elo_calculated', 'file'])
            writer.writeheader()
            writer.writerows(rows)
    except csv.Error:
        pass


def load_tournaments_from_json(tournaments_file: Path) -> set:
    """
    Load set of tournament IDs from tournaments.json (unused now, kept for reference).
    
    Args:
        tournaments_file: Path to tournaments.json
        
    Returns:
        Set of tournament IDs in the file
    """
    if not tournaments_file.exists():
        return set()
    
    try:
        with open(tournaments_file, 'r') as f:
            data = json.load(f)
            return set(data.keys())
    except (json.JSONDecodeError, KeyError):
        return set()


def process_all_standings(events_dir: Path, output_dir: Path, exclude_dummy: bool = True):
    """
    Process all extracted standings files and calculate ratings.
    Skips tournaments that have already been processed.
    
    Args:
        events_dir: Directory containing extracted standings JSON files
        output_dir: Directory to save output (players.json, tournaments.json)
        exclude_dummy: If True, skip tournaments with 'dummy' in the name (default: True)
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    players_file = output_dir / 'players.json'
    tournaments_file = output_dir / 'tournaments.json'
    csv_file = events_dir / 'parsed_events.csv'
    
    # Load existing data
    players = load_players(players_file)
    tournaments = load_tournaments(tournaments_file)
    
    # Load opted-in players from main input directory
    repo_root = events_dir.parent.parent
    opt_in_file = repo_root / 'input' / 'opt_in.csv'
    opted_in_players = load_opted_in_players(opt_in_file)
    
    # Get already processed tournaments from CSV
    processed_tournaments = load_processed_tournaments(csv_file)
    
    # Find all standings files (excluding parsed_events.csv)
    standings_files = sorted([f for f in events_dir.glob("*.json") if f.name != 'parsed_events.csv'])
    
    if not standings_files:
        print(f"No standings files found in {events_dir}")
        return
    
    print(f"Found {len(standings_files)} standings file(s)\n")
    
    processed_count = 0
    skipped_count = 0
    
    for standings_file in standings_files:
        try:
            with open(standings_file, 'r') as f:
                data = json.load(f)
            
            tournament_id = data['tournament_id']
            
            # Skip dummy tournaments if exclude_dummy is True
            if exclude_dummy and 'dummy' in tournament_id.lower():
                print(f"Skipping: {tournament_id} (dummy tournament)")
                skipped_count += 1
                continue
            
            # Check if already processed
            if tournament_id in processed_tournaments:
                print(f"Skipping: {tournament_id} (already calculated)")
                skipped_count += 1
                continue
            
            tournament_name = tournament_id.replace("_", " ").title()
            standings = data['standings']
            
            print(f"{'='*80}")
            print(f"Processing: {tournament_name}")
            print(f"{'='*80}")
            
            # Process standings
            players, tournaments, results = process_tournament_standings(
                tournament_id,
                tournament_name,
                standings,
                players,
                tournaments,
                opted_in_players
            )
            
            # Display results
            print_results_table(results, opted_in_players)
            
            # Mark as processed in CSV
            mark_tournament_processed(csv_file, tournament_id)
            processed_count += 1
            
        except Exception as e:
            print(f"Error processing {standings_file}: {e}")
    
    # Save all data only if we processed anything new
    if processed_count > 0:
        save_players(players, players_file)
        save_tournaments(tournaments, tournaments_file)
        print(f"\nSaved to {output_dir}")
        print(f"  - players.json")
        print(f"  - tournaments.json")
    
    print(f"\nProcessing complete: {processed_count} processed, {skipped_count} skipped")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Calculate ELO ratings from tournament standings')
    parser.add_argument('--include-dummy', action='store_true', 
                       help='Include dummy tournaments (for testing/dev only)')
    args = parser.parse_args()
    
    script_dir = Path(__file__).parent
    events_dir = script_dir / "events"
    output_dir = script_dir / "output"
    
    if not events_dir.exists():
        print(f"Error: {events_dir} does not exist")
        print("Run extract_standings.py first")
        return
    
    exclude_dummy = not args.include_dummy
    process_all_standings(events_dir, output_dir, exclude_dummy=exclude_dummy)


if __name__ == '__main__':
    main()
