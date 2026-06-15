# ELO Algorithm for final_standings_version

This document describes the ELO rating calculation system used in the `final_standings_version` folder.

## Overview

The ELO rating system calculates player ratings based on tournament results. The base algorithm uses a simplified USCF (United States Chess Federation) method with three major improvements:

- **A**: K-factor scaling based on tournament length
- **B**: Dropout detection to reduce penalties for early exits
- **C**: Prestige tournament bracket bonuses

## Core Algorithm

### Performance Rating Calculation

For each tournament, we calculate a **performance rating** representing the rating level the player demonstrated in that tournament:

```
performance_rating = R such that:
  expected_score(R, field_avg) = actual_score
```

This uses binary search against the logistic curve: `E(R) = 1 / (1 + 10^((field_avg - R)/400))`

### New Rating Calculation

Once we have the performance rating, we calculate the new rating as:

```
new_rating = current_rating + K_factor * (performance_rating - current_rating) / 400
```

The **K-factor** determines how much the performance rating can shift the current rating. A higher K-factor means tournament results matter more.

## Improvements

### A & B: K-factor Scaling and Dropout Handling (Unified)

**Problem A**: A 5-0 record in a 3-round tournament requires lower performance than a 5-0 record in a 5-round tournament.

**Problem B**: Players who drop out (0-2, 1-2) shouldn't be penalized as heavily as those who complete the tournament.

**Solution**: Use the same formula for all players based on games played:

```
K = 32 + (games - 3) * 12
```

This automatically handles both issues:
- Longer tournaments → more games → higher K-factor (better evidence = more reward)
- Dropouts → fewer games → lower K-factor (less evidence = less impact)

Examples:
- 2 games (dropout): K = 20 ← Minimal K-factor impact
- 3 games: K = 32 ← Baseline
- 4 games: K = 44 ← Higher impact
- 5 games: K = 56
- 9 games (prestige): K = 104 ← Significant impact

**Intuition**: More games = more evidence of skill at that level. K-factor directly reflects tournament length and completion.

### C: Prestige Tournament Bracket Bonuses

**Problem**: In tournaments with swiss rounds + top 8 bracket, making the bracket represents additional skill proof. A finals berth (7+ wins total) should reward more than 5 wins in swiss-only.

**Solution**: Prestige tournaments (name contains "prestige") get bracket stage bonuses:

```
Finals (ranks 1-2):      K *= 1.5  (+50%)
Semis (ranks 3-4):       K *= 1.3  (+30%)
Quarters (ranks 5-8):    K *= 1.1  (+10%)
Swiss-only (rank 9+):    K *= 1.0  (no bonus)
```

**Key Feature**: These bonuses are **additive, never subtractive**. They reward making the bracket but never penalize losing early in bracket play.

**Intuition**: Tournament progression = proven skill. Finals player gets more rating credit than a swiss-only player, even with similar records.

### Combining the Improvements

The final K-factor calculation is simple:

1. Calculate base K from games played: K = 32 + (games - 3) * 12 (handles both A and B)
2. Apply prestige bracket bonus if applicable (C)

Example: Prestige finalist with 9 games:
```
K_base = 32 + (9 - 3) * 12 = 104
K_final = 104 + 15 = 119 (finals +15 bonus)
```

Example: Regular tournament dropout (0-2 in 5 rounds):
```
K_base = 32 + (2 - 3) * 12 = 20
K_final = 20 (no prestige bonus)
```

Example: Prestige semi-finalist who made bracket (7 games):
```
K_base = 32 + (7 - 3) * 12 = 80
K_final = 80 + 10 = 90 (semis +10 bonus)
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
- `../dummy.html`: Generated leaderboard (opted-in players only)

## Testing

Unit tests in `tests/test_elo_calculator_final.py` cover:
- K-factor calculation for different tournament lengths (2-9 games)
- Dropout handling via natural K-factor reduction (2, 3, 4+ game tournaments)
- Prestige tournament detection
- Bracket stage classification
- Prestige bonuses for finals, semis, quarters

The test suite verifies:
- **K-factor scaling**: 2 games = K20, 3 games = K32, 4 games = K44, 5 games = K56, 9 games = K104
- **Dropout penalty**: Early exits get lower K-factors automatically (no separate penalty logic)
- **Prestige finals**: K × 1.5 bonus
- **Prestige semis**: K × 1.3 bonus
- **Prestige quarters**: K × 1.1 bonus

Run tests:
```bash
pytest tests/test_elo_calculator_final.py -v
```

All 17 tests pass ✓

## References

- USCF (United States Chess Federation) rating system: https://www.uschess.org/
- Prestige tournaments: Swiss rounds followed by top 8 bracket stage
- K-factor: Standard ELO parameter controlling rating volatility
