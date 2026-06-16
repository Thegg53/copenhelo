#!/usr/bin/env python3
"""
Generate HTML player detail pages from player data.
Functional implementation with pure functions.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Set


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


def generate_match_rows(player: Dict, opted_in_players: Set[str]) -> str:
    """Generate table rows for player match history."""
    rows = []
    for match in player.get('history', []):
        opponent = match.get('opponent', 'Unknown')
        if opponent not in opted_in_players:
            opponent = 'Hidden Opponent'
        
        result_code = match.get('result_code', '?')
        result_class = 'win' if result_code == 'W' else ('loss' if result_code == 'L' else 'draw')
        result_text = 'Win' if result_code == 'W' else ('Loss' if result_code == 'L' else 'Draw')
        
        rating_change = match.get('rating_change', 0)
        change_class = 'positive' if rating_change > 0 else ('negative' if rating_change < 0 else 'neutral')
        
        rows.append(f"""
            <tr>
              <td>{match.get('tournament', '')}</td>
              <td>{match.get('round', '')}</td>
              <td>{opponent}</td>
              <td><span class="result {result_class}">{result_text}</span></td>
              <td><span class="rating-change {change_class}">{rating_change:+d}</span></td>
              <td>{match.get('rating_after', '')}</td>
            </tr>
        """)
    
    return '\n'.join(rows)


def generate_player_section(player: Dict, opted_in_players: Set[str]) -> str:
    """Generate collapsible section for a single player."""
    slug = player['name'].lower().replace(' ', '-')
    match_rows = generate_match_rows(player, opted_in_players)
    
    return f"""
        <details>
          <summary id="{slug}">
            <span class="player-name">{player['name']}</span>
            <span class="player-rating">{player['rating']}</span>
          </summary>
          <div class="player-details">
            <table class="matches-table">
              <thead>
                <tr>
                  <th>Tournament</th>
                  <th>Round</th>
                  <th>Opponent</th>
                  <th>Result</th>
                  <th>Rating Change</th>
                  <th>New Rating</th>
                </tr>
              </thead>
              <tbody>
{match_rows}
              </tbody>
            </table>
          </div>
        </details>
    """


def generate_player_pages_html(players: Dict[str, Dict], opted_in_players: Set[str]) -> str:
    """Generate complete players HTML page."""
    sorted_players = sorted(players.values(), key=lambda p: p['rating'], reverse=True)
    player_sections = [generate_player_section(p, opted_in_players) for p in sorted_players]
    sections_html = '\n'.join(player_sections)
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Player Details</title>
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
      max-width: 1000px;
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
      justify-content: space-between;
      align-items: center;
      font-weight: 600;
    }}
    
    summary:hover {{
      background: #e9ecef;
    }}
    
    .player-name {{
      color: #333;
      flex: 1;
    }}
    
    .player-rating {{
      color: #764ba2;
      font-weight: 700;
      margin-right: 10px;
    }}
    
    .player-details {{
      padding: 15px;
      background: white;
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
    
    .result {{
      padding: 4px 8px;
      border-radius: 4px;
      font-weight: 600;
      font-size: 0.85em;
    }}
    
    .result.win {{
      background: #d4edda;
      color: #155724;
    }}
    
    .result.loss {{
      background: #f8d7da;
      color: #721c24;
    }}
    
    .result.draw {{
      background: #e2e3e5;
      color: #383d41;
    }}
    
    .rating-change {{
      font-weight: 600;
    }}
    
    .rating-change.positive {{
      color: #28a745;
    }}
    
    .rating-change.negative {{
      color: #dc3545;
    }}
    
    .rating-change.neutral {{
      color: #666;
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
      <h1>Player Details</h1>
      <nav>
        <a href="leaderboard.html">Leaderboard</a>
        <a href="tournaments.html">Tournaments</a>
      </nav>
    </div>
    
    <div class="content">
{sections_html}
    </div>
    
    <div class="footer">
      <p>Click player name to expand details</p>
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
    
    log_func("Starting player pages generation")
    
    players = json.loads((output_dir / 'players.json').read_text() or '{}')
    opted_in_players = load_opted_in_players_csv(input_dir)
    
    html = generate_player_pages_html(players, opted_in_players)
    
    output_file = repo_root / 'players.html'
    with open(output_file, 'w') as f:
        f.write(html)
    
    log_func(f"Generated players page: players.html ({len(players)} players)")
    log_func("Player pages generation complete")
    flush_logs(log_buffer, log_file)


if __name__ == '__main__':
    main()
