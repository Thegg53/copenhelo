#!/usr/bin/env python3
"""
Generate HTML tournaments page from tournament data.
Functional implementation with pure functions.
"""

import json
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, Set, Tuple


def load_tournaments_data(output_dir: Path) -> Dict:
    """Load tournaments data from JSON file."""
    tournaments_file = output_dir / 'tournaments.json'
    if not tournaments_file.exists():
        return {}
    
    with open(tournaments_file, 'r') as f:
        return json.load(f)


def load_opted_in_players_csv(input_dir: Path) -> Set[str]:
    """Load opted-in player names from CSV file."""
    opt_in_file = input_dir / 'opt_in.csv'
    if not opt_in_file.exists():
        return set()
    
    with open(opt_in_file, 'r') as f:
        return {line.strip() for line in f if line.strip()}


def parse_tournament_id(tournament_id: str) -> Tuple[str, str]:
    """Parse tournament ID into date and name components."""
    parts = tournament_id.split('_', 1)
    date = parts[0] if parts else 'Unknown'
    name = parts[1] if len(parts) > 1 else parts[0]
    name = name.replace('_', ' ').title()
    return date, name


def generate_match_rows(matches: list, opted_in_players: Set[str]) -> str:
    """Generate table rows for tournament matches."""
    rows = []
    for match in matches:
        player1 = match.get('player1', 'Unknown')
        player2 = match.get('player2', 'Unknown')
        
        if player1 not in opted_in_players:
            player1 = 'Hidden Player'
        if player2 and player2 != 'BYE' and player2 not in opted_in_players:
            player2 = 'Hidden Player'
        
        result = match.get('result')
        if result:
            p1_wins, p2_wins = result
            if p1_wins > p2_wins:
                score_html = f'<span class="match-score"><strong>{player1}</strong> {p1_wins}-{p2_wins}</span>'
            elif p2_wins > p1_wins:
                score_html = f'<span class="match-score">{p1_wins}-{p2_wins} <strong>{player2}</strong></span>'
            else:
                score_html = f'<span class="match-score">{p1_wins}-{p2_wins} (Draw)</span>'
        else:
            score_html = f'<span class="bye-badge">BYE</span>'
        
        rows.append(f"""
          <tr>
            <td>{player1}</td>
            <td>{player2 if player2 else '—'}</td>
            <td>{score_html}</td>
          </tr>
        """)
    
    return '\n'.join(rows)


def generate_tournament_section(tournament_id: str, tournament: Dict, opted_in_players: Set[str]) -> str:
    """Generate collapsible section for a single tournament."""
    date, name = parse_tournament_id(tournament_id)
    slug = tournament_id.lower().replace('_', '-')
    
    round_sections = []
    for round_key, round_data in sorted(tournament.get('rounds', {}).items(), key=lambda x: int(x[0])):
        matches = round_data.get('matches', [])
        match_rows = generate_match_rows(matches, opted_in_players)
        
        round_sections.append(f"""
        <div class="round">
          <h3>Round {round_key}</h3>
          <table class="matches-table">
            <thead>
              <tr>
                <th>Player 1</th>
                <th>Player 2</th>
                <th>Result</th>
              </tr>
            </thead>
            <tbody>
{match_rows}
            </tbody>
          </table>
        </div>
        """)
    
    rounds_html = '\n'.join(round_sections)
    
    return f"""
      <details>
        <summary id="{slug}">
          <span class="tournament-date">{date}</span>
          <span class="tournament-name">{name}</span>
        </summary>
        <div class="tournament-details">
{rounds_html}
        </div>
      </details>
    """


def generate_tournaments_html(tournaments: Dict[str, Dict], opted_in_players: Set[str]) -> str:
    """Generate complete tournaments HTML page."""
    tournament_sections = []
    for tournament_id in sorted(tournaments.keys(), reverse=True):
        section = generate_tournament_section(tournament_id, tournaments[tournament_id], opted_in_players)
        tournament_sections.append(section)
    
    sections_html = '\n'.join(tournament_sections)
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Tournaments</title>
  <style>
    * {{
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }}
    
    body {{
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      min-height: 100vh;
      padding: 20px;
    }}
    
    .container {{
      max-width: 1200px;
      margin: 0 auto;
      background: white;
      border-radius: 12px;
      box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
      overflow: hidden;
    }}
    
    .header {{
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      padding: 40px 20px;
      text-align: center;
    }}
    
    .header h1 {{
      font-size: 2.5em;
      margin-bottom: 10px;
    }}
    
    .header nav {{
      margin-top: 15px;
    }}
    
    .header a {{
      color: rgba(255, 255, 255, 0.9);
      text-decoration: none;
      font-size: 14px;
      margin: 0 15px;
    }}
    
    .header a:hover {{
      text-decoration: underline;
    }}
    
    .content {{
      padding: 20px;
    }}
    
    details {{
      margin: 15px 0;
      border: 1px solid #dee2e6;
      border-radius: 8px;
      overflow: hidden;
    }}
    
    summary {{
      background: #f8f9fa;
      padding: 15px;
      cursor: pointer;
      display: flex;
      align-items: center;
      font-weight: 600;
    }}
    
    summary:hover {{
      background: #e9ecef;
    }}
    
    .tournament-date {{
      color: #667eea;
      font-weight: 700;
      margin-right: 15px;
      min-width: 100px;
    }}
    
    .tournament-name {{
      color: #333;
      flex: 1;
    }}
    
    .tournament-details {{
      padding: 15px;
      background: white;
    }}
    
    .round {{
      margin: 15px 0;
    }}
    
    .round h3 {{
      color: #667eea;
      font-size: 1.1em;
      margin-bottom: 10px;
    }}
    
    .matches-table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 0.9em;
    }}
    
    .matches-table th {{
      background: #f8f9fa;
      padding: 10px;
      text-align: left;
      font-weight: 600;
      border-bottom: 2px solid #dee2e6;
    }}
    
    .matches-table td {{
      padding: 10px;
      border-bottom: 1px solid #dee2e6;
    }}
    
    .matches-table tr:hover {{
      background: #f8f9fa;
    }}
    
    .match-score {{
      font-weight: 600;
    }}
    
    .bye-badge {{
      background: #fff3cd;
      color: #856404;
      padding: 4px 8px;
      border-radius: 4px;
      font-weight: 600;
      font-size: 0.85em;
    }}
    
    .footer {{
      background: #f8f9fa;
      padding: 20px;
      text-align: center;
      color: #666;
      font-size: 0.9em;
      border-top: 1px solid #dee2e6;
    }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>Tournaments</h1>
      <nav>
        <a href="leaderboard.html">Leaderboard</a>
        <a href="players.html">Players</a>
      </nav>
    </div>
    
    <div class="content">
{sections_html}
    </div>
    
    <div class="footer">
      <p>Click tournament to expand details</p>
    </div>
  </div>
</body>
</html>
"""
    return html


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
    output_dir = repo_root / 'output'
    input_dir = repo_root / 'input'
    log_file = repo_root / 'log.txt'
    
    log_buffer = []
    
    def log_func(msg: str):
        nonlocal log_buffer
        log_buffer = log_message(log_buffer, msg)
    
    log_func("Starting tournaments page generation")
    
    tournaments = load_tournaments_data(output_dir)
    opted_in_players = load_opted_in_players_csv(input_dir)
    
    html = generate_tournaments_html(tournaments, opted_in_players)
    
    output_file = repo_root / 'tournaments.html'
    with open(output_file, 'w') as f:
        f.write(html)
    
    log_func(f"Generated tournaments page: tournaments.html ({len(tournaments)} tournaments)")
    log_func("Tournaments page generation complete")
    flush_logs(log_buffer, log_file)


if __name__ == '__main__':
    main()
