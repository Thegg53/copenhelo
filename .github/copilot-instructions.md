---
name: copenhelo-rules
description: Project-wide rules for copenhelo ELO system
---

# Copenhelo Agent Instructions

## Every Session
- **ALWAYS re-read** `README.md` and `Makefile` at the start of a session to understand the current pipeline and available commands
- Understand the context: this is a Magic: The Gathering ELO rating system with tournament parsing, rating calculation, and HTML generation

## Code Style
- Write **functional, not object-oriented** code
- Use pure functions with explicit inputs/outputs
- Avoid classes and stateful objects unless absolutely necessary
- Prefer composition and function pipelines over inheritance
- Keep functions small, single-purpose, and testable

## Testing Requirements
- **Tests MUST pass before any commit to main**
- Run `make test` to verify the full test suite (54 tests)
- All 6 test modules must pass:
  - test_elo_calculator.py
  - test_elo_calculator_final.py
  - test_parse_tournaments.py
  - test_leaderboard_generator.py
  - test_players_generator.py
  - test_tournaments_generator.py
  - test_privacy.py

## Development Workflow
1. Parse tournaments from HTML input
2. Recalculate ELO ratings
3. Generate HTML outputs
4. Run full test suite
5. Commit only when tests pass
