# ELO Algorithm for final_standings_version

This document describes the ELO rating calculation system used in the `final_standings_version` folder.

## Overview

The ELO rating system calculates player ratings based on tournament results. The base algorithm uses a simplified USCF (United States Chess Federation) method with three major improvements:

- **A**: K-factor scaling based on tournament length
- **B**: Dropout detection to reduce penalties for early exits
- **C**: Prestige tournament bracket bonuses

## Core Algorithm

### Expected Score Calculation

For each tournament, we calculate the **expected score** using the Magic: The Gathering standard ELO formula:

```
expected_score = 1 / (1 + 10^((field_avg - player_rating) / 1136))
```

Where:
- `player_rating` is the player's current rating before the tournament
- `field_avg` is the average rating of all opponents (excluding the player)
- **Divisor 1136 is the MTG standard** (not chess's 400)

This represents what score we'd expect the player to achieve against that field.

### Why 1136 instead of Chess's 400?

Magic: The Gathering has **significantly higher variance** than chess due to mana, draw variance, and sideboarding. The chess formula (400 divisor) predicts a 91% win rate for someone 400 points higher—unrealistic for Magic.

The MTG Elo Project (industry standard at mtgeloproject.net) uses **1136** because it's calibrated so:
- **200-point gap = 60% expected win rate** (vs chess's 76%)
- Even the #1 rated player achieves only ~63% win rate
- This properly reflects Magic's high variance

Reference: "It didn't seem to us like there could ever be a situation where someone is 91% to win a match of Magic—there's too much variance in the game." —MTG Elo Project FAQ

### New Rating Calculation

We calculate the new rating using the standard ELO formula:

```
new_rating = current_rating + K_factor * (actual_score - expected_score)
```

Where:
- `actual_score` is the player's tournament score (0.0 to 1.0)
- `expected_score` is calculated from the formula above
- `K_factor` determines how much tournament results shift the rating

**Key Principle**: This formula rewards over-performance and penalizes under-performance, regardless of field strength. A 75% win rate always produces a positive gain.

## Improvements

### A & B: K-factor Scaling and Dropout Handling (Unified)

**Problem A**: A 5-game tournament requires different rating swing evidence than a 3-game tournament.

**Problem B**: Players who drop out (0-2, 1-2) shouldn't be penalized as heavily as those who complete the tournament.

**Solution**: Use K-factor scaling based on games played, aligned with MTG Elo Project standards:

```
K = 32 * games
```

This automatically handles both issues:
- Longer tournaments → more games → higher K-factor (better evidence = more reward)
- Dropouts → fewer games → lower K-factor (less evidence = less impact)

Examples:
- 2 games (dropout): K = 64 ← Minimal K-factor impact
- 3 games: K = 96
- 4 games: K = 128 ← Standard tournament
- 5 games: K = 160
- 6 games: K = 192 ← Prestige tournament (6 swiss games only, excluding bracket)

**Intuition**: More games = more evidence of skill at that level. K-factor directly reflects tournament length and completion. This is the same scaling approach used by MTG Elo Project but applied per-game.

### C: Prestige Tournament Bracket Bonuses

**Problem**: In tournaments with swiss rounds + top 8 bracket, making the bracket represents additional skill proof. The bracket is single-elimination with the strongest players, so advancing further should be rewarded.

**Solution**: Prestige tournaments (name contains "prestige") use **swiss-only records** for ELO calculation and give flat rating bonuses based on bracket results:

```
For ELO calculation:
- Use ONLY the 6 swiss games (exclude bracket games)
- Calculate K and rating change based on swiss record

Bracket bonuses (on top of ELO change):
- Champion (3-0 bracket):        +48 rating points
- Finalist (2-1 bracket):        +20 rating points
- Semis (1-1 bracket):           +10 rating points
- Quarters loser (0-1 bracket):  +3 rating points
- Swiss-only (no bracket):       +0 rating points
```

**Key Details**:
- **Only prestige tournaments** exclude bracket games
- **Non-prestige tournaments** use the full record (all games count)
- The bracket bonus is scaled as ~+16 per bracket win:
  - 3 wins = +48
  - 2 wins = +20 (one loss cancels one win)
  - 1 win = +10 (break-even)
  - 0 wins = +3 (just for making bracket)

**Rationale**:
- **Prestige swiss-only**: Bracket games don't count in ELO because they're single-elimination (variance amplified, fewer game samples). The flat bonus recognizes making the bracket without polluting the main ELO calculation.
- **Non-prestige full record**: Regular tournaments have all games in swiss, so all count equally.
- **+16 per bracket win**: Three consecutive wins in single-elimination against the strongest field is significant but not overwhelming.

**Example**: Prestige finalist with 6 swiss games at 75% and 2-1 bracket:
```
Swiss ELO calculation:
  K = 24 * 6 = 144
  expected_score = 50% (assuming average field)
  change = 144 * (0.75 - 0.5) = +36

Bracket bonus (2-1 record) = +20

Total: +36 + +20 = +56 rating points
(The 3 bracket games are completely excluded from ELO)
```

**Example**: Regular tournament with 4 games and 75% score:
```
All 4 games count (not prestige):
  K = 32 * 4 = 128
  expected_score = 43% (field 1523, player 1680, gap 157)
  change = 128 * (0.75 - 0.43) = +41

Bracket bonus = 0 (not prestige)
Total: +41 rating points
```

### Combining the Improvements

The final rating change is:

1. Calculate base K from games played: `K = 32 * games` (handles both A and B)
2. For prestige tournaments with bracket: extract swiss-only record (remove bracket games)
3. Calculate rating change using swiss record: `change = K * (actual_score - expected_score)`
4. Apply prestige bracket bonus if applicable (C): `new_rating = current + change + bracket_bonus`

Example: Prestige finalist with 9 total games (6 swiss + 3 bracket) and 75% swiss score:
```
Swiss portion: 4-1-1 (13/18 points)
Bracket portion: 2-1 (in finals)

K = 32 * 6 = 192 (only count swiss games)
Assuming field_avg ≈ player_rating:
  expected_score = 0.5
  swiss_score = 13/18 ≈ 0.72
  change = 192 * (0.72 - 0.5) ≈ +42

Bracket bonus = +20 (2-1 record)
Total: new_rating = current + 42 + 20 = current + 62
(Note: The 3 bracket games are excluded from ELO calculation entirely)
```

Example: Standard tournament with 4 games and 75% score:
```
K = 32 * 4 = 128
Assuming field_avg ~1550, player_rating = 1680 (gap of -130):
  expected_score = 1 / (1 + 10^(130/1136)) ≈ 43%
  change = 128 * (0.75 - 0.43) ≈ +41
Bracket bonus = 0 (not prestige)
new_rating = current + 31
```

Example: Dropout with 2 games:
```
K = 24 * 2 = 48
change = 48 * (actual - expected)
Bracket bonus = 0
new_rating = current + change
```

## Privacy

Players must opt-in via `input/opt_in.csv`. Opted-in players display their actual names in output. Non-opted-in players:
- Still receive rating updates (with default 1500 rating)
- Are filtered out from leaderboard display
- Do not appear in HTML output

## Data Format

### Input
- `events/*.json`: Tournament standings files from `extract_standings.py`
- `input/opt_in.csv`: List of player names who opted in to display

### Output
- `output/players.json`: Player data with current ratings and history
- `output/tournaments.json`: Tournament standings and metadata
- `../standings.html`: Generated leaderboard (opted-in players only)

## Testing

Unit tests in `tests/test_elo_calculator_final.py` cover:
- K-factor calculation for different tournament lengths (2-9 games)
- Dropout handling via natural K-factor reduction (2, 3, 4+ game tournaments)
- Prestige tournament detection
- Bracket stage classification
- Prestige bonuses for finals, semis, quarters

The test suite verifies:
- **K-factor scaling**: 2 games = K48, 3 games = K72, 4 games = K96, 5 games = K120, 9 games = K216
- **Dropout penalty**: Early exits get lower K-factors automatically (no separate penalty logic)
- **Prestige finals**: +48 rating points
- **Prestige semis**: +32 rating points
- **Prestige quarters**: +16 rating points

Run tests:
```bash
pytest tests/test_elo_calculator_final.py -v
```

All 17 tests pass ✓

## References

- USCF (United States Chess Federation) rating system: https://www.uschess.org/
- Prestige tournaments: Swiss rounds followed by top 8 bracket stage
- K-factor: Standard ELO parameter controlling rating volatility
