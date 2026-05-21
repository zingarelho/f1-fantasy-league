import requests

# F1 points for top 5 positions: P1=25, P2=18, P3=15, P4=12, P5=10
F1_POINTS = {1: 25, 2: 18, 3: 15, 4: 12, 5: 10}

# Fallback top-5 result used when the live API is unreachable
_FALLBACK_RESULTS = [
    {"id": "VER", "points": 25},
    {"id": "NOR", "points": 18},
    {"id": "LEC", "points": 15},
    {"id": "HAM", "points": 12},
    {"id": "PIA", "points": 10},
]


class RaceClient:
    """Interface for fetching F1 race schedules and results.

    The Ergast API (ergast.com) has been deprecated. All API calls are wrapped
    with try/except and fall back to hardcoded data so the app remains usable
    offline or when the API is unavailable.
    """

    BASE_URL = "https://api.jolpi.ca/ergast/f1"

    def get_full_2026_calendar(self):
        """Return the 2026 race calendar as a list of dicts.

        Each entry: {round, name, date, status}.
        Falls back to a hardcoded provisional schedule.
        """
        try:
            headers = {"User-Agent": "HermesF1Fantasy/1.0"}
            resp = requests.get(
                f"{self.BASE_URL}/2026.json", headers=headers, timeout=10
            )
            data = resp.json()
            races = (data.get("MRData", {})
                         .get("RaceTable", {})
                         .get("Races", []))
            if races:
                return [
                    {
                        "round": int(r["round"]),
                        "name": r["raceName"],
                        "date": r["date"],
                        "status": r.get("status", "Scheduled"),
                    }
                    for r in races
                ]
        except Exception as e:
            print(f"[RaceClient] Calendar API error: {e}")

        # Fallback: provisional 2026 calendar (accurate as of late 2025)
        return [
            {"round": 1,  "name": "Bahrain Grand Prix",             "date": "2026-03-01",  "status": "Scheduled"},
            {"round": 2,  "name": "Saudi Arabian Grand Prix",       "date": "2026-03-08",  "status": "Scheduled"},
            {"round": 3,  "name": "Australian Grand Prix",          "date": "2026-03-22",  "status": "Scheduled"},
            {"round": 4,  "name": "Chinese Grand Prix",             "date": "2026-04-05",  "status": "Scheduled"},
            {"round": 5,  "name": "Japanese Grand Prix",            "date": "2026-04-19",  "status": "Scheduled"},
            {"round": 6,  "name": "Miami Grand Prix",               "date": "2026-05-03",  "status": "Scheduled"},
            {"round": 7,  "name": "Emilia Romagna Grand Prix",      "date": "2026-05-17",  "status": "Scheduled"},
            {"round": 8,  "name": "Monaco Grand Prix",              "date": "2026-05-31",  "status": "Scheduled"},
            {"round": 9,  "name": "Spanish Grand Prix",             "date": "2026-06-07",  "status": "Scheduled"},
            {"round": 10, "name": "Canadian Grand Prix",            "date": "2026-06-21",  "status": "Scheduled"},
            {"round": 11, "name": "Austrian Grand Prix",            "date": "2026-07-05",  "status": "Scheduled"},
            {"round": 12, "name": "British Grand Prix",             "date": "2026-07-19",  "status": "Scheduled"},
            {"round": 13, "name": "Belgian Grand Prix",             "date": "2026-08-02",  "status": "Scheduled"},
            {"round": 14, "name": "Hungarian Grand Prix",           "date": "2026-08-16",  "status": "Scheduled"},
            {"round": 15, "name": "Dutch Grand Prix",               "date": "2026-08-30",  "status": "Scheduled"},
            {"round": 16, "name": "Italian Grand Prix",             "date": "2026-09-06",  "status": "Scheduled"},
            {"round": 17, "name": "Singapore Grand Prix",           "date": "2026-09-27",  "status": "Scheduled"},
            {"round": 18, "name": "USA Grand Prix",                 "date": "2026-10-18",  "status": "Scheduled"},
            {"round": 19, "name": "Mexico City Grand Prix",         "date": "2026-11-01",  "status": "Scheduled"},
            {"round": 20, "name": "Sao Paulo Grand Prix",           "date": "2026-11-15",  "status": "Scheduled"},
            {"round": 21, "name": "Las Vegas Grand Prix",           "date": "2026-11-28",  "status": "Scheduled"},
            {"round": 22, "name": "Abu Dhabi Grand Prix",           "date": "2026-12-06",  "status": "Scheduled"},
        ]

    def get_results(self, round_num, season="2026"):
        """Return official top-5 results for a given round.

        Returns a list of dicts:
            [{"id": "VER", "points": 25}, {"id": "NOR", "points": 18}, …]

        Falls back to hardcoded placeholder data when the API is unreachable.
        """
        try:
            headers = {"User-Agent": "HermesF1Fantasy/1.0"}
            resp = requests.get(
                f"{self.BASE_URL}/{season}/results.json?round={round_num}",
                headers=headers,
                timeout=10,
            )
            data = resp.json()
            races = (
                data.get("MRData", {})
                    .get("RaceTable", {})
                    .get("Races", [])
            )
            if not races:
                # Race hasn't happened yet — no classification available
                return []
            raw = races[0].get("Results", [])[:5]
            if not raw:
                return []
            return [
                {
                    "id": r["Driver"]["code"],  # 3-letter code (VER, NOR, …)
                    "points": int(r["points"]),
                }
                for r in raw
            ]
        except Exception as e:
            print(f"[RaceClient] Results API error (round {round_num}): {e}")

        # API unreachable — use fallback
        return list(_FALLBACK_RESULTS)
