#!/usr/bin/env python3
"""
Recalculate ELO history from scratch.
Useful when input tournaments have outdated dates or need to be reordered.
Functional implementation.
"""

import json
from pathlib import Path
from datetime import datetime
import sys
from elo_calculator import (
    load_opted_in_players,
    process_round,
    filter_opted_in_players,
    sanitize_opponent_names,
    sanitize_tournament_names,
    save_results,
    init_tournament
)


def log_message(buffer: list, message: str) -> list:
    """Buffer and print log message."""
    timestamp = datetime.now().isoformat()
    buffer.append(f"[{timestamp}] {message}")
    print(message)
    return buffer


def flush_logs(buffer: list, log_file: Path) -> None:
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
    
    log_buffer = []
    
    def log_func(msg: str):
        nonlocal log_buffer
        log_buffer = log_message(log_buffer, msg)
    
    log_func("=" * 60)
    log_func("RECALCULATING HISTORY FROM SCRATCH")
    log_func("=" * 60)
    
    # Load opt-in list
    opted_in_players = load_opted_in_players(opt_in_file)
    if opted_in_players:
        log_func(f"Loaded {len(opted_in_players)} opted-in players from opt_in.csv")
    else:
        log_func(f"Warning: {opt_in_file} not found. All players will be treated as opted in.")
    
    # Find all tournament JSON files
    if not events_dir.exists():
        log_func("Error: events/ directory not found.")
        flush_logs(log_buffer, log_file)
        return
    
    tournament_files = sorted(events_dir.glob('*.json'))
    if not tournament_files:
        log_func("No tournament files found in events/")
        flush_logs(log_buffer, log_file)
        return
    
    log_func(f"Found {len(tournament_files)} tournament(s)")
    
    # Initialize fresh data structures
    players = {}
    tournaments = {}
    log_func("Cleared existing player and tournament data")
    
    processed_count = 0
    
    # Process all tournaments in order
    for tournament_file in tournament_files:
        tournament_id = tournament_file.stem
        
        try:
            with open(tournament_file, 'r') as f:
                tournament_data = json.load(f)
            
            log_func(f"Processing tournament: {tournament_id}")
            
            # Process each round in order
            sorted_rounds = sorted(
                tournament_data['rounds'].items(),
                key=lambda x: int(x[0])
            )
            
            for round_key, round_data in sorted_rounds:
                round_num = int(round_key)
                matches = round_data['matches']
                
                # Process round with functional API
                players, tournaments = process_round(
                    tournament_id, round_num, matches, players, tournaments,
                    opted_in_players, log_func
                )
                log_func(f"  Round {round_num}: {len(matches)} matches")
            
            processed_count += 1
        
        except Exception as e:
            log_func(f"Error processing {tournament_id}: {str(e)}")
            import traceback
            log_func(traceback.format_exc())
    
    # Filter and sanitize output
    filtered_players = filter_opted_in_players(players, opted_in_players)
    sanitized_players = sanitize_opponent_names(filtered_players, opted_in_players)
    sanitized_tournaments = sanitize_tournament_names(tournaments, opted_in_players)
    
    # Save results
    save_results(sanitized_players, sanitized_tournaments, output_dir)
    
    # Summary
    log_func(f"Recalculation complete!")
    log_func(f"  Tournaments processed: {processed_count}")
    log_func(f"  Total players calculated: {len(players)}")
    log_func(f"  Players in output (opted-in): {len(filtered_players)}")
    log_func("=" * 60)
    
    flush_logs(log_buffer, log_file)


if __name__ == '__main__':
    main()
