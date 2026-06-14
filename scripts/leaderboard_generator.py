#!/usr/bin/env python3
"""
Generate HTML leaderboard from player data.
Functional implementation with pure functions.
"""

import json
import re
from pathlib import Path
from datetime import datetime
from typing import List, Dict


def slugify(text: str) -> str:
    """Convert text to URL-friendly slug."""
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'-+', '-', text)
    text = re.sub(r' +', '-', text)
    return text


def load_players_data(output_dir: Path) -> Dict[str, Dict]:
    """Load player data from JSON file."""
    players_file = output_dir / 'players.json'
    if not players_file.exists():
        return {}
    
    with open(players_file, 'r') as f:
        return json.load(f)


def sort_players_by_rating(players: Dict[str, Dict]) -> List[Dict]:
    """Sort players by rating in descending order."""
    return sorted(
        players.values(),
        key=lambda p: p['rating'],
        reverse=True
    )


def generate_player_row(rank: int, player: Dict) -> str:
    """Generate a single row for the leaderboard table."""
    slug = slugify(player['name'])
    return f"""
    <tr>
      <td class="rank">{rank}</td>
      <td class="name"><a href="players.html#{slug}">{player['name']}</a></td>
      <td class="rating">{player['rating']}</td>
      <td class="matches">{len(player.get('matches', []))}</td>
    </tr>
    """


def generate_leaderboard_html(players: Dict[str, Dict]) -> str:
    """Generate complete leaderboard HTML."""
    sorted_players = sort_players_by_rating(players)
    rows = [generate_player_row(rank, player) for rank, player in enumerate(sorted_players, 1)]
    rows_html = '\n'.join(rows)
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>ELO Leaderboard</title>
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
      max-width: 900px;
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
    
    .header p {{
      font-size: 1.1em;
      opacity: 0.9;
      margin-bottom: 15px;
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
    
    table {{
      width: 100%;
      border-collapse: collapse;
    }}
    
    thead {{
      background: #f8f9fa;
      border-bottom: 2px solid #dee2e6;
    }}
    
    th {{
      padding: 15px;
      text-align: left;
      font-weight: 600;
      color: #333;
    }}
    
    td {{
      padding: 15px;
      border-bottom: 1px solid #dee2e6;
    }}
    
    tr:hover {{
      background: #f8f9fa;
    }}
    
    .rank {{
      font-weight: 600;
      color: #667eea;
      width: 60px;
    }}
    
    .name {{
      font-weight: 500;
      flex-grow: 1;
    }}
    
    .name a {{
      color: #667eea;
      text-decoration: none;
      transition: color 0.2s;
    }}
    
    .name a:hover {{
      color: #764ba2;
      text-decoration: underline;
    }}
    
    .rating {{
      text-align: right;
      font-weight: 600;
      color: #764ba2;
      width: 100px;
    }}
    
    .matches {{
      text-align: center;
      color: #666;
      width: 80px;
    }}
    
    th.rank, th.rating, th.matches {{
      text-align: right;
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
      <h1>ELO Leaderboard</h1>
      <p>Tournament Ratings</p>
      <nav>
        <a href="players.html">Players</a>
        <a href="tournaments.html">Tournaments</a>
      </nav>
    </div>
    
    <table>
      <thead>
        <tr>
          <th class="rank">Rank</th>
          <th class="name">Player</th>
          <th class="rating">Rating</th>
          <th class="matches">Matches</th>
        </tr>
      </thead>
      <tbody>
{rows_html}
      </tbody>
    </table>
    
    <div class="footer">
      <p>Last updated at runtime</p>
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
    log_file = repo_root / 'log.txt'
    
    log_buffer = []
    
    def log_func(msg: str):
        nonlocal log_buffer
        log_buffer = log_message(log_buffer, msg)
    
    log_func("Starting leaderboard generation")
    
    players = load_players_data(output_dir)
    html = generate_leaderboard_html(players)
    
    output_file = repo_root / 'leaderboard.html'
    with open(output_file, 'w') as f:
        f.write(html)
    
    log_func(f"Generated leaderboard: leaderboard.html ({len(players)} players)")
    log_func("Leaderboard generation complete")
    flush_logs(log_buffer, log_file)


if __name__ == '__main__':
    main()
