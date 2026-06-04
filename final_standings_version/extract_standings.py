#!/usr/bin/env python3
"""
Extract tournament standings from HTML files.
Parses EventLink standings tables and stores clean data as JSON.
"""

import json
import csv
import re
from pathlib import Path
from datetime import datetime
from bs4 import BeautifulSoup


def parse_standings_html(html_file: Path) -> list:
    """
    Parse standings table from EventLink HTML file.
    
    Args:
        html_file: Path to HTML standings file
        
    Returns:
        List of dicts with keys: name, rank, points, wins, losses, draws, omw, gwp, ogwp, games
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
        except (ValueError, AttributeError, IndexError):
            continue
    
    return standings


def save_standings(tournament_id: str, standings: list, output_dir: Path):
    """
    Save standings to events/ folder as JSON.
    
    Args:
        tournament_id: Tournament identifier
        standings: List of standings dicts
        output_dir: Directory to save to (typically events/)
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    data = {
        'tournament_id': tournament_id,
        'timestamp': datetime.now().isoformat(),
        'standings': standings
    }
    
    output_file = output_dir / f"{tournament_id}.json"
    with open(output_file, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"Saved standings: {output_file}")


def load_parsed_tournaments(csv_file: Path) -> set:
    """
    Load set of already-parsed tournament IDs from CSV.
    
    Args:
        csv_file: Path to parsed_events.csv
        
    Returns:
        Set of tournament IDs that have already been parsed
    """
    if not csv_file.exists() or csv_file.stat().st_size == 0:
        return set()
    
    parsed = set()
    try:
        with open(csv_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row and 'tournament_id' in row:
                    parsed.add(row['tournament_id'])
    except (csv.Error, KeyError):
        pass
    
    return parsed


def save_parsed_tournament(csv_file: Path, tournament_id: str, players_count: int):
    """
    Record that a tournament has been extracted in the CSV.
    
    Args:
        csv_file: Path to parsed_events.csv
        tournament_id: Tournament identifier
        players_count: Number of players in standings
    """
    # Create CSV with header if it doesn't exist
    if not csv_file.exists():
        with open(csv_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['timestamp', 'tournament_id', 'players', 'htm_parsed_to_json', 'elo_calculated', 'file'])
            writer.writeheader()
    
    # Append new entry
    with open(csv_file, 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['timestamp', 'tournament_id', 'players', 'htm_parsed_to_json', 'elo_calculated', 'file'])
        writer.writerow({
            'timestamp': datetime.now().isoformat(),
            'tournament_id': tournament_id,
            'players': players_count,
            'htm_parsed_to_json': 'yes',
            'elo_calculated': 'no',
            'file': f'events/{tournament_id}.json'
        })


def extract_all_standings(input_dir: Path, output_dir: Path):
    """
    Extract all standings HTML files from input directory.
    Skips tournaments that have already been parsed.
    
    Args:
        input_dir: Directory containing HTML files
        output_dir: Directory to save extracted standings (events/)
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_file = output_dir / 'parsed_events.csv'
    
    html_files = sorted(input_dir.glob("*.htm"))
    html_files.extend(sorted(input_dir.glob("*.html")))
    
    if not html_files:
        print(f"No HTML files found in {input_dir}")
        return
    
    print(f"Found {len(html_files)} HTML file(s)\n")
    
    # Load already parsed tournaments
    parsed_tournaments = load_parsed_tournaments(csv_file)
    
    processed_count = 0
    skipped_count = 0
    
    for html_file in html_files:
        tournament_id = html_file.stem
        
        # Check if already parsed
        if tournament_id in parsed_tournaments:
            print(f"Skipping: {html_file.name} (already parsed)")
            skipped_count += 1
            continue
        
        try:
            print(f"Extracting: {html_file.name}")
            standings = parse_standings_html(html_file)
            
            if not standings:
                print(f"  ✗ No standings found")
                continue
            
            save_standings(tournament_id, standings, output_dir)
            save_parsed_tournament(csv_file, tournament_id, len(standings))
            print(f"  ✓ {len(standings)} players extracted\n")
            processed_count += 1
            
        except Exception as e:
            print(f"  ✗ Error: {e}\n")
    
    print(f"Extraction complete: {processed_count} processed, {skipped_count} skipped")


def main():
    """Main entry point."""
    script_dir = Path(__file__).parent
    input_dir = script_dir / "input"
    events_dir = script_dir / "events"
    
    if not input_dir.exists():
        print(f"Error: {input_dir} does not exist")
        return
    
    extract_all_standings(input_dir, events_dir)


if __name__ == '__main__':
    main()
