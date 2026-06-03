# Final Standings ELO System

This folder contains an alternative ELO rating system that calculates ratings **from tournament final standings only**, without requiring round-by-round match data.

## How It Works

Uses a simplified USCF performance rating method:

1. **Extract final standings** from EventLink HTML tournament exports
2. **Calculate field strength** by averaging opponent ratings (excluding the player)
3. **Determine performance rating** - the rating that would explain the player's actual score
4. **Update player rating** based on how far their performance rating is from their current rating

### Key Formula

```
Expected Score vs Field Avg = 1 / (1 + 10^((field_avg - rating) / 400))
Performance Rating = Rating that would produce actual_score against field_avg
New Rating = Current Rating + K * (Performance Rating - Current Rating) / 400
```

## Configuration

- **K-Factor**: 40 (bi-weekly tournaments with variable attendance)
- **Default Rating**: 1500
- **Penalties/Rewards**: 
  - Good performance vs weak field = smaller gain
  - Poor performance vs weak field = penalty
  - Good performance vs strong field = bigger gain

## Usage

```bash
cd /path/to/copenhelo
python3 final_standings_version/elo_from_standings.py <path-to-standings-html> [tournament-name]
```

Or with a specific HTML file:

```python
from final_standings_version.elo_from_standings import TournamentProcessor

processor = TournamentProcessor(Path("final_standings_version/output/player_ratings.txt"))
processor.process_tournament(
    standings_html=Path("events/MyTournament.htm"),
    tournament_name="My Tournament (2026-06-03)"
)
```

## Output

The script prints a table showing:
- **Name**: Player name
- **Rank**: Final placement
- **Record**: W-L-D record
- **Old Elo**: Rating before tournament
- **Field Avg**: Average rating of opponents (excluding player)
- **Perf**: Performance rating from this tournament
- **New Elo**: Updated rating
- **Change**: Rating adjustment

Ratings are automatically saved to `output/player_ratings.txt` and used as baseline for the next tournament.

## Advantages

✅ Works with old tournaments where round data isn't available
✅ Only needs final standings HTML
✅ Field strength automatically factored in
✅ Single consolidated update per tournament (more stable)
✅ Progressive rating evolution across tournaments

## Limitations

⚠️ Assumes field average as opponent for all games (approximation)
⚠️ Cannot see if a player played mostly top-8 vs bottom field
⚠️ Doesn't capture individual match variation

For more detailed match-level analysis, see the main ELO system in `scripts/elo_calculator.py`.
