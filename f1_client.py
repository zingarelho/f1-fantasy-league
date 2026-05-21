
import requests

class RaceClient:
    BASE_URL = "http://ergast.com/api/f1"
    
    def get_schedule(self, season="2024"):
        """Fetches the race schedule for the given season."""
        try:
            response = requests.get(f"{self.BASE_URL}/{season}.json")
            data = response.json()
            races = data['MRos']['Race']}") # Ergast structure is nested
            # Note: Ergast often requires specific parsing for their JSON structure.
            # Let's simplify to a robust request for the actual data.
            return self._parse_schedule(data)
        except Exception as e:
            print(f"Error fetching schedule: {e}")
            return []

    def get_results(self, round_num, season="2024"):
        """Fetches the Top 5 drivers for a specific round."""
        try:
            response = requests.get(f"{self.BASE_URL}/{season}/results.json?round={round_num}")
            data = response.json()
            # Extract Top 5 Driver names/IDs
            results = []
            race_results = data['MRos'][0]['Race']
            for i in range(min(5, len(race_results))):
                # We'll use the driver's givenName or driverId for consistency
                driver_info = race_results[i]['Driver']
                results.append(driver_info['driverId'].upper())
            return results
        except Exception as e:
            print(f"Error fetching results: {e}")
            return []

    def _parse_schedule(self, data):
        # Helper to flatten Ergast JSON
        races = []
        try:
            races_list = data['MRos'][0]['Races']
            for r in races_list:
                races.append({
                    "round": r['round'],
                    "name": r['raceName'],
                    "date": r['date'],
                    "status": "Finished" if "Finished" in r.get('status', '') else "Scheduled"
                })
        except:
            pass
        return races
