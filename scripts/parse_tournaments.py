#!/usr/bin/env python3
"""
Parse tournament HTML files and extract clean event data.
Stores results in events/ folder and logs to log.txt
Functional implementation with pure functions.
"""

import json
import csv
from pathlib import Path
from datetime import datetime
import re
from typing import Dict, List, Tuple, Optional, Set
from bs4 import BeautifulSoup


def extract_player_name(cell) -> Optional[str]:
    """
    Extract player name from table cell.
    
    Args:
        cell: BeautifulSoup cell element
        
    Returns:
        Player name string or None
    """
    team_div = cell.find('div', class_='team')
    if not team_div:
        return None
    
    name_span = team_div.find('span', class_='team__text')
    if name_span:
        name_elem = name_span.find('span')
        if name_elem:
            return name_elem.get_text(strip=True)
    
    return None


def extract_match_result(cell) -> Optional[Tuple[int, int]]:
    """
    Extract match result from result cell.
    
    Args:
        cell: BeautifulSoup cell element
        
    Returns:
        Tuple (player1_wins, player2_wins) or None if no result
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


def parse_tournament_file(filepath: Path) -> List[Dict]:
    """
    Parse a tournament HTML file and extract match data.
    
    Args:
        filepath: Path to tournament HTML file
        
    Returns:
        List of match dictionaries with keys: table, player1, player2, result, has_bye
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    soup = BeautifulSoup(html_content, 'html.parser')
    matches = []
    
    # Find pairings table
    table = soup.find('table', class_='pairings-table')
    if not table:
        return matches
    
    tbody = table.find('tbody')
    if not tbody:
        return matches
    
    # Parse each match row
    for row in tbody.find_all('tr'):
        cells = row.find_all('td', class_='pairings-table__cell')
        if len(cells) < 6:
            continue
        
        # Extract table number
        table_num = cells[0].get_text(strip=True)
        
        # Extract player 1
        player1_cell = cells[2]
        player1_name = extract_player_name(player1_cell)
        if not player1_name:
            continue
        
        # Extract score
        result_cell = cells[3]
        result = extract_match_result(result_cell)
        
        # Extract player 2 or bye
        player2_cell = cells[4]
        bye_div = player2_cell.find('div', class_='bye')
        
        if bye_div:
            # Player 1 got a bye
            matches.append({
                'table': table_num if table_num else None,
                'player1': player1_name,
                'player2': None,
                'result': None,
                'has_bye': True
            })
        else:
            player2_name = extract_player_name(player2_cell)
            if player2_name:
                matches.append({
                    'table': table_num if table_num else None,
                    'player1': player1_name,
                    'player2': player2_name,
                    'result': result,
                    'has_bye': False
                })
    
    return matches


def log_message(buffer: List[str], message: str) -> List[str]:
    """
    Add timestamped message to log buffer.
    
    Args:
        buffer: Current log buffer
        message: Message to log
        
    Returns:
        Updated log buffer
    """
    timestamp = datetime.now().isoformat()
    buffer.append(f"[{timestamp}] {message}")
    print(message)
    return buffer


def flush_logs(buffer: List[str], log_file: Path) -> None:
    """
    Write all buffered logs to file.
    
    Args:
        buffer: Log buffer to flush
        log_file: Path to log file
    """
    if not buffer:
        return
    
    new_entries = "\n".join(buffer) + "\n"
    with open(log_file, 'a') as f:
        f.write(new_entries)


def load_parsed_tournaments(csv_file: Path) -> Set[str]:
    """
    Load already parsed tournament IDs from CSV file.
    
    Args:
        csv_file: Path to parsed_events.csv
        
    Returns:
        Set of tournament IDs
    """
    if not csv_file.exists() or csv_file.stat().st_size == 0:
        return set()
    
    parsed = set()
    with open(csv_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row and 'tournament_id' in row:
                parsed.add(row['tournament_id'])
    
    return parsed


def find_round_files(tournament_dir: Path) -> List[Path]:
    """
    Find and sort all round files in a tournament directory.
    
    Args:
        tournament_dir: Path to tournament directory
        
    Returns:
        Sorted list of round file paths
    """
    return sorted(
        tournament_dir.glob('r*.htm'),
        key=lambda p: int(re.search(r'r(\d+)', p.name).group(1))
    )


def parse_tournament_rounds(
    tournament_id: str,
    round_files: List[Path],
    log_func
) -> Tuple[Dict, int, int]:
    """
    Parse all rounds for a tournament.
    
    Args:
        tournament_id: Tournament ID
        round_files: List of round file paths
        log_func: Logging function
        
    Returns:
        Tuple (tournament_data, round_count, total_matches)
    """
    tournament_data = {
        'id': tournament_id,
        'rounds': {},
        'parsed_at': datetime.now().isoformat()
    }
    
    total_matches = 0
    
    for round_file in round_files:
        match = re.search(r'r(\d+)', round_file.name)
        if not match:
            continue
        
        round_num = int(match.group(1))
        matches = parse_tournament_file(round_file)
        tournament_data['rounds'][str(round_num)] = {
            'matches': matches,
            'count': len(matches)
        }
        
        total_matches += len(matches)
        log_func(f"  Parsed round {round_num}: {len(matches)} matches")
    
    return tournament_data, len(round_files), total_matches


def save_tournament_data(
    tournament_id: str,
    tournament_data: Dict,
    round_count: int,
    total_matches: int,
    events_dir: Path,
    csv_file: Path
) -> None:
    """
    Save tournament data to JSON and CSV.
    
    Args:
        tournament_id: Tournament ID
        tournament_data: Tournament data dictionary
        round_count: Number of rounds
        total_matches: Total matches across all rounds
        events_dir: Path to events directory
        csv_file: Path to parsed_events.csv
    """
    output_file = events_dir / f'{tournament_id}.json'
    with open(output_file, 'w') as f:
        json.dump(tournament_data, f, indent=2)
    
    with open(csv_file, 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['timestamp', 'tournament_id', 'rounds', 'matches', 'file'])
        writer.writerow({
            'timestamp': datetime.now().isoformat(),
            'tournament_id': tournament_id,
            'rounds': round_count,
            'matches': total_matches,
            'file': output_file.name
        })


def main():
    """Main entry point."""
    repo_root = Path(__file__).parent.parent
    input_dir = repo_root / 'input'
    events_dir = repo_root / 'events'
    csv_file = events_dir / 'parsed_events.csv'
    log_file = repo_root / 'log.txt'
    
    # Create events directory
    events_dir.mkdir(exist_ok=True)
    
    # Initialize CSV if it doesn't exist
    if not csv_file.exists():
        with open(csv_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['timestamp', 'tournament_id', 'rounds', 'matches', 'file'])
            writer.writeheader()
    
    log_buffer = []
    
    def log_func(msg: str):
        nonlocal log_buffer
        log_buffer = log_message(log_buffer, msg)
    
    log_func("Starting tournament parsing")
    
    # Load already parsed tournaments
    parsed_tournaments = load_parsed_tournaments(csv_file)
    
    processed_count = 0
    skipped_count = 0
    
    # Process each tournament directory
    for tournament_dir in sorted(input_dir.iterdir()):
        if not tournament_dir.is_dir():
            continue
        
        tournament_id = tournament_dir.name
        
        # Check if already parsed
        if tournament_id in parsed_tournaments:
            log_func(f"Skipping tournament {tournament_id} (already parsed)")
            skipped_count += 1
            continue
        
        log_func(f"Parsing tournament: {tournament_id}")
        
        # Find all round files
        round_files = find_round_files(tournament_dir)
        
        # Parse tournament rounds
        tournament_data, round_count, total_matches = parse_tournament_rounds(
            tournament_id, round_files, log_func
        )
        
        # Save results
        save_tournament_data(
            tournament_id, tournament_data, round_count, total_matches,
            events_dir, csv_file
        )
        
        log_func(f"Parsed tournament {tournament_id}: {round_count} rounds, {total_matches} matches -> events/{tournament_id}.json")
        processed_count += 1
    
    log_func(f"Tournament parsing complete: {processed_count} processed, {skipped_count} skipped")
    flush_logs(log_buffer, log_file)


if __name__ == '__main__':
    main()
