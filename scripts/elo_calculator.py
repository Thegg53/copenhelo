#!/usr/bin/env python3
"""
ELO Rating Calculator for Tournaments - Functional implementation
Reads parsed tournament data from events/ and calculates ratings.
"""

import json
import math
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Set, Callable
from datetime import datetime


# Constants
DEFAULT_RATING = 1500
K_FACTOR = 32


def calculate_new_rating(
    current_rating: float,
    opponent_rating: float,
    score: float,
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
        New rating rounded to 1 decimal place
    """
    expected_score = 1 / (1 + math.pow(10, (opponent_rating - current_rating) / 400))
    rating_change = k_factor * (score - expected_score)
    new_rating = current_rating + rating_change
    return round(new_rating, 1)


def determine_result_code(p1_wins: int, p2_wins: int) -> str:
    """Determine result code (W/L/D) from match scores."""
    if p1_wins > p2_wins:
        return 'W'
    elif p1_wins < p2_wins:
        return 'L'
    else:
        return 'D'


def determine_result_score(p1_wins: int, p2_wins: int) -> Tuple[float, float]:
    """Determine ELO scores (1.0/0.5/0.0) from match scores."""
    if p1_wins > p2_wins:
        return (1.0, 0.0)
    elif p1_wins < p2_wins:
        return (0.0, 1.0)
    else:
        return (0.5, 0.5)


def get_opponent_rating(
    opponent_name: str,
    opponent_actual_rating: float,
    opted_in_players: Set[str]
) -> float:
    """
    Get opponent rating for ELO calculation.
    Returns actual rating if opted in, DEFAULT_RATING otherwise.
    """
    return opponent_actual_rating if opponent_name in opted_in_players else DEFAULT_RATING


def load_or_init_players(output_dir: Path) -> Dict[str, Dict]:
    """Load existing player data or initialize empty dict."""
    players_file = output_dir / 'players.json'
    if players_file.exists():
        with open(players_file, 'r') as f:
            return json.load(f)
    return {}


def load_or_init_tournaments(output_dir: Path) -> Dict[str, Dict]:
    """Load existing tournament data or initialize empty dict."""
    tournaments_file = output_dir / 'tournaments.json'
    if tournaments_file.exists():
        with open(tournaments_file, 'r') as f:
            return json.load(f)
    return {}


def init_player(name: str) -> Dict:
    """Create a new player data structure."""
    return {
        'name': name,
        'rating': DEFAULT_RATING,
        'matches': [],
        'history': []
    }


def init_tournament(tournament_id: str) -> Dict:
    """Create a new tournament data structure."""
    return {
        'id': tournament_id,
        'rounds': {},
        'created_at': datetime.now().isoformat()
    }


def process_match(
    match: Dict,
    players: Dict[str, Dict],
    tournament_id: str,
    round_num: int,
    opted_in_players: Set[str],
    log_func: Callable
) -> Dict[str, Dict]:
    """
    Process a single match and update player ratings.
    Returns updated players dict.
    """
    if match['has_bye']:
        p1_name = match['player1']
        if p1_name not in players:
            players[p1_name] = init_player(p1_name)
        return players
    
    p1_name = match['player1']
    p2_name = match['player2']
    result = match['result']
    
    # Initialize players if not exist
    if p1_name not in players:
        players[p1_name] = init_player(p1_name)
    if p2_name not in players:
        players[p2_name] = init_player(p2_name)
    
    # Skip if no result
    if not result:
        return players
    
    p1_rating_before = players[p1_name]['rating']
    p2_rating_before = players[p2_name]['rating']
    
    # Get opponent ratings (use 1500 for non-opted-in)
    p1_opponent_rating = get_opponent_rating(p2_name, p2_rating_before, opted_in_players)
    p2_opponent_rating = get_opponent_rating(p1_name, p1_rating_before, opted_in_players)
    
    # Get scores and result code
    p1_wins, p2_wins = result
    result_code = determine_result_code(p1_wins, p2_wins)
    p1_score, p2_score = determine_result_score(p1_wins, p2_wins)
    
    # Calculate new ratings
    p1_new_rating = calculate_new_rating(p1_rating_before, p1_opponent_rating, p1_score)
    p2_new_rating = calculate_new_rating(p2_rating_before, p2_opponent_rating, p2_score)
    
    p1_rating_change = round(p1_new_rating - p1_rating_before, 1)
    p2_rating_change = round(p2_new_rating - p2_rating_before, 1)
    
    # Log the match
    log_func(f"    {p1_name} ({result_code}) {p2_name} [{p1_rating_change:+.1f} {p2_rating_change:+.1f}]")
    
    # Update ratings
    players[p1_name]['rating'] = p1_new_rating
    players[p2_name]['rating'] = p2_new_rating
    
    # Record match history
    players[p1_name]['history'].append({
        'tournament': tournament_id,
        'round': round_num,
        'opponent': p2_name,
        'result_code': 'W' if p1_score == 1.0 else ('D' if p1_score == 0.5 else 'L'),
        'rating_before': p1_rating_before,
        'rating_after': p1_new_rating,
        'rating_change': p1_rating_change,
        'score': (p1_wins, p2_wins)
    })
    players[p2_name]['history'].append({
        'tournament': tournament_id,
        'round': round_num,
        'opponent': p1_name,
        'result_code': 'W' if p2_score == 1.0 else ('D' if p2_score == 0.5 else 'L'),
        'rating_before': p2_rating_before,
        'rating_after': p2_new_rating,
        'rating_change': p2_rating_change,
        'score': (p2_wins, p1_wins)
    })
    
    # Record matches played
    players[p1_name]['matches'].append({
        'tournament': tournament_id,
        'round': round_num,
        'opponent': p2_name,
        'result': result
    })
    players[p2_name]['matches'].append({
        'tournament': tournament_id,
        'round': round_num,
        'opponent': p1_name,
        'result': (p2_wins, p1_wins)
    })
    
    return players


def process_round(
    tournament_id: str,
    round_num: int,
    matches: List[Dict],
    players: Dict[str, Dict],
    tournaments: Dict[str, Dict],
    opted_in_players: Set[str],
    log_func: Callable
) -> Tuple[Dict[str, Dict], Dict[str, Dict]]:
    """Process all matches in a round. Returns updated (players, tournaments) dicts."""
    if tournament_id not in tournaments:
        tournaments[tournament_id] = init_tournament(tournament_id)
    
    round_key = str(round_num)
    tournaments[tournament_id]['rounds'][round_key] = {
        'matches': matches,
        'processed_at': datetime.now().isoformat()
    }
    
    # Process each match
    for match in matches:
        players = process_match(match, players, tournament_id, round_num, opted_in_players, log_func)
    
    return players, tournaments


def sanitize_opponent_names(
    players: Dict[str, Dict],
    opted_in_players: Set[str]
) -> Dict[str, Dict]:
    """Replace non-opted-in opponent names with 'Hidden Opponent' in player history."""
    sanitized = {}
    for player_name, player_data in players.items():
        sanitized[player_name] = dict(player_data)
        
        # Sanitize matches
        if 'matches' in sanitized[player_name]:
            sanitized[player_name]['matches'] = [
                {
                    **match,
                    'opponent': 'Hidden Opponent' if match.get('opponent') and match['opponent'] not in opted_in_players else match.get('opponent')
                }
                for match in sanitized[player_name]['matches']
            ]
        
        # Sanitize history
        if 'history' in sanitized[player_name]:
            sanitized[player_name]['history'] = [
                {
                    **match,
                    'opponent': 'Hidden Opponent' if match.get('opponent') and match['opponent'] not in opted_in_players else match.get('opponent')
                }
                for match in sanitized[player_name]['history']
            ]
    
    return sanitized


def sanitize_tournament_names(
    tournaments: Dict[str, Dict],
    opted_in_players: Set[str]
) -> Dict[str, Dict]:
    """Replace non-opted-in player names with 'Hidden Player' in tournament data."""
    sanitized = {}
    for tournament_id, tournament_data in tournaments.items():
        sanitized[tournament_id] = {
            'id': tournament_data.get('id'),
            'created_at': tournament_data.get('created_at'),
            'rounds': {}
        }
        
        for round_key, round_data in tournament_data.get('rounds', {}).items():
            sanitized_matches = []
            for match in round_data.get('matches', []):
                sanitized_match = dict(match)
                
                if 'player1' in sanitized_match and sanitized_match['player1'] not in opted_in_players:
                    sanitized_match['player1'] = 'Hidden Player'
                
                if 'player2' in sanitized_match and not sanitized_match.get('has_bye', False):
                    if sanitized_match['player2'] not in opted_in_players:
                        sanitized_match['player2'] = 'Hidden Player'
                
                sanitized_matches.append(sanitized_match)
            
            sanitized[tournament_id]['rounds'][round_key] = {
                'matches': sanitized_matches,
                'processed_at': round_data.get('processed_at')
            }
    
    return sanitized


def filter_opted_in_players(
    players: Dict[str, Dict],
    opted_in_players: Set[str]
) -> Dict[str, Dict]:
    """Filter players to only include those who opted in."""
    return {
        name: data for name, data in players.items()
        if name in opted_in_players
    }


def save_results(
    players: Dict[str, Dict],
    tournaments: Dict[str, Dict],
    output_dir: Path
) -> None:
    """Save player and tournament data to JSON files."""
    players_file = output_dir / 'players.json'
    tournaments_file = output_dir / 'tournaments.json'
    
    with open(players_file, 'w') as f:
        json.dump(players, f, indent=2, default=str)
    
    with open(tournaments_file, 'w') as f:
        json.dump(tournaments, f, indent=2, default=str)


def load_opted_in_players(opt_in_file: Path) -> Set[str]:
    """Load opted-in player names from CSV file."""
    if not opt_in_file.exists():
        return set()
    
    with open(opt_in_file, 'r') as f:
        return {line.strip() for line in f if line.strip()}


def log_message(buffer: List[str], message: str) -> List[str]:
    """Add timestamped message to log buffer."""
    timestamp = datetime.now().isoformat()
    buffer.append(f"[{timestamp}] {message}")
    print(message)
    return buffer


def flush_logs(buffer: List[str], log_file: Path) -> None:
    """Write all buffered logs to file."""
    if not buffer:
        return
    
    new_entries = "\n".join(buffer) + "\n"
    with open(log_file, 'a') as f:
        f.write(new_entries)


def main():
    """Main entry point."""
    repo_root = Path(__file__).parent.parent
    events_dir = repo_root / 'events'
    output_dir = repo_root / 'output'
    log_file = repo_root / 'log.txt'
    opt_in_file = repo_root / 'input' / 'opt_in.csv'
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    opted_in_players = load_opted_in_players(opt_in_file)
    if not opted_in_players:
        print(f"Warning: {opt_in_file} not found. All players will be treated as opted in.")
    
    log_buffer = []
    players = load_or_init_players(output_dir)
    tournaments = load_or_init_tournaments(output_dir)
    
    def log_func(msg: str):
        nonlocal log_buffer
        log_buffer = log_message(log_buffer, msg)
    
    log_func("Starting ELO calculation")
    
    if not events_dir.exists():
        log_func("Error: events/ directory not found. Run parse_tournaments.py first.")
        flush_logs(log_buffer, log_file)
        return
    
    processed_count = 0
    skipped_count = 0
    
    for tournament_file in sorted(events_dir.glob('*.json')):
        tournament_id = tournament_file.stem
        
        if tournament_id in tournaments:
            log_func(f"Skipping tournament {tournament_id} (already processed)")
            skipped_count += 1
            continue
        
        try:
            with open(tournament_file, 'r') as f:
                tournament_data = json.load(f)
            
            log_func(f"Processing tournament: {tournament_id}")
            
            for round_key, round_data in tournament_data['rounds'].items():
                round_num = int(round_key)
                matches = round_data['matches']
                players, tournaments = process_round(
                    tournament_id, round_num, matches, players, tournaments,
                    opted_in_players, log_func
                )
                log_func(f"  Round {round_num}: {len(matches)} matches")
            
            processed_count += 1
        
        except Exception as e:
            log_func(f"Error processing {tournament_id}: {str(e)}")
    
    filtered_players = filter_opted_in_players(players, opted_in_players)
    sanitized_players = sanitize_opponent_names(filtered_players, opted_in_players)
    sanitized_tournaments = sanitize_tournament_names(tournaments, opted_in_players)
    
    if len(filtered_players) < len(players):
        filtered_out = len(players) - len(filtered_players)
        log_func(f"Filtering: {filtered_out} non-opted-in players excluded from output")
    
    save_results(sanitized_players, sanitized_tournaments, output_dir)
    log_func(f"ELO calculation complete: {processed_count} processed, {skipped_count} skipped")
    
    flush_logs(log_buffer, log_file)
    print(f"Saved {len(sanitized_players)} players to output/players.json")
    print(f"Saved {len(sanitized_tournaments)} tournaments to output/tournaments.json")


if __name__ == '__main__':
    main()
