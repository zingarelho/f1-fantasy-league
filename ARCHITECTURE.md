# 🏗️ Architecture: F1 Fantasy League

## 1. System Overview
The application is a lightweight prediction engine that decouples the user interface (Streamlit) from the scoring logic, data persistence, and external API interactions.

## 2. Component Diagram
```text
[ Streamlit UI ] <---> [ DataManager ] <---> [ predictions.json ]
      ^                      ^
      |                      |
      v                      v
[ RaceClient ] <---> [ F1 External APIs / Mocks ]
      |
      v
[ ScoringEngine ] (Pure Logic)
```

## 3. Core Modules
### `app.py` (The Orchestrator)
- Handles the Streamlit session and page state.
- coordinates between the `RaceClient`, `DataManager`, and `ScoringEngine`.
- Manages the three primary views: Leaderboard, Input, and Info.

### `engine.py` (The Scoring Domain)
- **Single Responsibility:** Calculates points for a single race.
- **Logic:** Implements a reward-and-penalty system.
- **Stateless:** Does not store data; only processes input vs. results.

### `data.py` (The Persistence Layer)
- Manages reading/writing to `predictions.json`.
- Schema: `{ "Race Name": { "User": { "picks": [], "is_late": bool } } }`

### `client.py` (The Integration Layer)
- Abstracted interface for fetching race schedules and results.
- Currently implements mocked data for development and testing.

## 4. Scoring Algorithm
For each predicted driver in the Top 5:
- If `driver == official_results[pos]`: **+10 pts**
- If `driver` is in `official_results` but `pos` is wrong: **+5 pts**
- Final total is multiplied by **0.5** if the submission was marked as `is_late`.
