# 🏗️ Architecture: F1 Fantasy League

## 1. System Overview
The application is a lightweight prediction engine that decouples the user interface (Streamlit) from the scoring logic, data persistence, and external API interactions.

## 2. Component Diagram
```text
[ Streamlit UI ] <───> [ DataManager ] <───> [ predictions.json     ]
      ^                       ^                 [ users.json          ]
      |                       |                 [ calendar.json       ]
      v                       v                 [ results.json        ]
[ RaceClient ] <───> [ F1 API / Hardcoded Fallback ]
      |
      v
[ ScoringEngine ]  (Pure logic, stateless)
```

## 3. Core Modules

### `app.py` (The Orchestrator)
- Handles the Streamlit session and page state.
- Coordinates between `RaceClient`, `DataManager`, and `ScoringEngine`.
- Manages five tabbed views: Leaderboard, User Details, Input Predictions, Race Info, User Management.
- Uses `_calculate_user_pts()` helper to avoid duplicated scoring logic across tabs.

### `f1_engine.py` (The Scoring Domain)
- **Single Responsibility:** Calculates points for a single race.
- **Logic:** Implements a reward-and-penalty system using real F1 points.
- **Stateless:** Does not store data; only processes input vs. results.
- **Scoring:**
  - Predicted position matches actual → full F1 points (25/18/15/12/10)
  - Predicted driver is in actual Top 5 but wrong position → half points
  - Late or missing submission → total ×0.5 (non-compounding)

### `f1_data.py` (The Persistence Layer)
- Manages reading/writing JSON files in the `data/` directory.
- **Schema — predictions.json:**
  ```json
  { "Race Name": { "User": { "picks": ["VER", …], "is_late": bool } } }
  ```
- **Schema — users.json:** `["User1", "User2", …]`
- **Schema — calendar.json:** `[{round, name, date, status}, …]`
- **Schema — results.json:** `{"round_number": [{"id": "VER", "points": 25}, …], …}`
- `get_last_valid_picks()` — finds the most recent prediction from a **prior** race when a user misses one (direction-safe: never pulls forward from a future race).

### `f1_client.py` (The Integration Layer)
- Abstracted interface for fetching race schedules and results.
- Queries the (deprecated) Ergast API; falls back to hardcoded data when the API is unreachable.
- Returns structured data matching the ScoringEngine's expected format (`[{"id": …, "points": …}]`).

## 4. Scoring Algorithm — Detail
For each of the 5 predicted drivers (by position):
- If `predicted_driver == actual_driver_at_position[pos]`: **+real F1 points** (25, 18, 15, 12, 10)
- If `predicted_driver` is in the actual Top 5 but at a different position: **+half those points**
- If submission was `is_late` or the user `is_missing`: final total **×0.5** (flat, non-compounding)