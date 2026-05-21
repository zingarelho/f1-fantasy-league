# F1 Fantasy League - Development Log

## Project Overview
A fantasy league tracker for F1 predictions (Top 5).

## Log
- **2026-05-20**: Project initialized in `myfiles/f1-fantasy-league/`.
- **2026-05-20**: Implemented `RaceClient` and basic `DataManager`.
- **2026-05-20**: Implemented `ScoringEngine` with specific rules (10/5 split, 50% flat penalty).
- **2026-05-20**: Corrected penalty logic: Penalties (late/missing) do NOT compound.
- **2026-05-20**: Implemented 'Last Valid Prediction' carry-over system for missed races.
- **2026-05-21**: Comprehensive bug fix pass:
  - Fixed type mismatch between `RaceClient.get_results()` and `ScoringEngine.calculate_points()` — now returns `[{"id": "VER", "points": 25}, …]` instead of flat strings.
  - Fixed Ergast API access path (`MRData[0]` → `MRData.RaceTable.Races`) so real API queries work when the endpoint is available.
  - Fixed carry-over direction bug: `get_last_valid_picks()` now only searches races **before** the current one, never pulling from future rounds.
  - Extracted duplicated carry-over logic into `DataManager.get_last_valid_picks()` helper, used by all tabs.
  - Removed unused `pandas` dependency from requirements.txt.
  - Updated `ARCHITECTURE.md` and `STATUS_REPORT.md` to match the actual implementation.
  - All races marked `Scheduled` in fallback data (no more fake `Finished` statuses).
