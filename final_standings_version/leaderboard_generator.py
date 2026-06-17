#!/usr/bin/env python3
"""
Generate interactive HTML leaderboard with expandable player histories.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Set


def load_players(output_dir: Path) -> dict:
    """Load player data from JSON."""
    players_file = output_dir / 'players.json'
    if not players_file.exists():
        return {}
    
    with open(players_file, 'r') as f:
        return json.load(f)


def load_opted_in_players(input_dir: Path) -> Set[str]:
    """Load opted-in player names from CSV file."""
    opt_in_file = input_dir / 'opt_in.csv'
    if not opt_in_file.exists():
        return set()
    
    with open(opt_in_file, 'r') as f:
        return {line.strip() for line in f if line.strip()}


def generate_leaderboard(output_file: Path):
    """Generate interactive leaderboard HTML with expandable histories."""
    output_dir = Path(__file__).parent / 'output'
    input_dir = Path(__file__).parent.parent / 'input'
    
    players = load_players(output_dir)
    opted_in_players = load_opted_in_players(input_dir)
    
    # Sort by rating and filter to only opted-in players
    sorted_players = sorted(
        [(name, data) for name, data in players.items() if name in opted_in_players],
        key=lambda p: p[1]['rating'],
        reverse=True
    )
    
    # Generate player rows with history
    player_rows = []
    for rank, (name, data) in enumerate(sorted_players, 1):
        rating = data['rating']
        history = data.get('history', [])
        
        # Generate history table HTML
        history_rows = []
        for event in history:
            # Extract date from tournament ID (first 8 chars: YYYYMMDD)
            tournament_id = event['tournament']
            date_str = tournament_id[:8]
            try:
                date_obj = datetime.strptime(date_str, '%Y%m%d')
                formatted_date = date_obj.strftime('%Y-%m-%d')
            except ValueError:
                formatted_date = date_str
            
            history_rows.append(f"""
          <tr>
            <td>{event['tournament']}</td>
            <td>{formatted_date}</td>
            <td>{event['rank']}</td>
            <td>{event['record']}</td>
            <td>{event['points']}</td>
            <td class="num">{event['rating_before']:.1f}</td>
            <td class="num">{event['rating_after']:.1f}</td>
            <td class="num {'positive' if event['change'] >= 0 else 'negative'}">{event['change']:+.1f}</td>
          </tr>
            """)
        
        history_table = ''.join(history_rows) if history_rows else '<tr><td colspan="8" style="text-align: center; color: #999;">No history yet</td></tr>'
        
        player_rows.append(f"""
    <tr class="player-row" onclick="toggleHistory('player-{rank}')">
      <td class="rank">{rank}</td>
      <td class="name">
        <span class="expand-icon">▶</span>
        {name}
      </td>
      <td class="rating">{rating:.1f}</td>
      <td class="tournaments">{len(history)}</td>
    </tr>
    <tr class="history-row" id="player-{rank}" style="display: none;">
      <td colspan="4">
        <table class="history-table">
          <thead>
            <tr>
              <th>Tournament</th>
              <th>Date</th>
              <th>Rank</th>
              <th>Record</th>
              <th>Points</th>
              <th>Rating Before</th>
              <th>Rating After</th>
              <th>Change</th>
            </tr>
          </thead>
          <tbody>
{history_table}
          </tbody>
        </table>
      </td>
    </tr>
        """)
    
    player_rows_html = '\n'.join(player_rows)
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Dummy Tournament Leaderboard</title>
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
    
    .header p {{
      font-size: 1.1em;
      opacity: 0.9;
      margin-bottom: 15px;
    }}
    
    .table-wrapper {{
      overflow-x: auto;
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
    
    .player-row {{
      cursor: pointer;
      user-select: none;
    }}
    
    .player-row:hover {{
      background: #f8f9fa;
    }}
    
    .rank {{
      font-weight: 600;
      color: #667eea;
      width: 60px;
    }}
    
    .name {{
      font-weight: 500;
      display: flex;
      align-items: center;
      gap: 10px;
    }}
    
    .expand-icon {{
      display: inline-block;
      transition: transform 0.2s;
      font-size: 0.8em;
      color: #667eea;
    }}
    
    .player-row.expanded .expand-icon {{
      transform: rotate(90deg);
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
    
    .history-row {{
      background: #f8f9fa;
    }}
    
    .history-row td {{
      padding: 20px 15px;
      border-bottom: none;
    }}
    
    .history-table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 0.9em;
    }}
    
    .history-table thead {{
      background: #e9ecef;
    }}
    
    .history-table th {{
      padding: 10px;
      text-align: left;
      font-weight: 600;
      color: #333;
      border-bottom: 1px solid #dee2e6;
    }}
    
    .history-table td {{
      padding: 10px;
      border-bottom: 1px solid #dee2e6;
    }}
    
    .history-table tr:hover {{
      background: #e9ecef;
    }}
    
    .num {{
      text-align: right;
      font-family: 'Courier New', monospace;
    }}
    
    .positive {{
      color: #28a745;
      font-weight: 600;
    }}
    
    .negative {{
      color: #dc3545;
      font-weight: 600;
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
      <h1>Tournament Standings</h1>
      <p>Click player names to see their tournament history</p>
      <nav style="margin-top: 15px;">
        <a href="leaderboard.html" style="color: rgba(255, 255, 255, 0.9); text-decoration: none; font-size: 14px; margin: 0 15px;">← Back to Leaderboard</a>
      </nav>
    </div>
    
    <div class="table-wrapper">
      <table>
        <thead>
          <tr>
            <th class="rank">Rank</th>
            <th class="name">Player</th>
            <th class="rating">Rating</th>
          <th class="tournaments">Tournaments</th>
          </tr>
        </thead>
        <tbody>
{player_rows_html}
        </tbody>
      </table>
    </div>
    
    <div class="footer">
      <p>Generated from final_standings_version ELO data</p>
    </div>
  </div>
  
  <script>
    function toggleHistory(playerId) {{
      const row = document.getElementById(playerId);
      const playerRow = row.previousElementSibling;
      
      if (row.style.display === 'none') {{
        row.style.display = 'table-row';
        playerRow.classList.add('expanded');
      }} else {{
        row.style.display = 'none';
        playerRow.classList.remove('expanded');
      }}
    }}
  </script>
</body>
</html>
"""
    
    with open(output_file, 'w') as f:
        f.write(html)
    
    print(f"Generated leaderboard: {output_file} ({len(sorted_players)} players)")


def main():
    """Main entry point."""
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent
    output_file = repo_root / 'standings.html'
    generate_leaderboard(output_file)


if __name__ == '__main__':
    main()
