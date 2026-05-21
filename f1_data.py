import json
import os


class DataManager:
    def __init__(self):
        self.data_folder = "data"
        if not os.path.exists(self.data_folder):
            os.makedirs(self.data_folder, exist_ok=True)

        self.predictions_file = os.path.join(self.data_folder, "predictions.json")
        self.users_file = os.path.join(self.data_folder, "users.json")
        self.calendar_file = os.path.join(self.data_folder, "calendar.json")
        self.results_file = os.path.join(self.data_folder, "results.json")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _write_json(self, path, data):
        try:
            with open(path, "w") as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            print(f"Write Error {path}: {e}")

    def _read_json(self, path):
        if not os.path.exists(path):
            return {}
        try:
            with open(path, "r") as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            print(f"JSON Decode Error {path}: {e}")
            return {}
        except Exception as e:
            print(f"Read Error {path}: {e}")
            return {}

    # ------------------------------------------------------------------
    # Predictions
    # ------------------------------------------------------------------

    def save_prediction(self, user, race, prediction, is_late):
        preds = self._read_json(self.predictions_file)
        if not isinstance(preds, dict):
            preds = {}
        if race not in preds:
            preds[race] = {}
        if not isinstance(preds[race], dict):
            preds[race] = {}
        preds[race][user] = {"picks": prediction, "is_late": is_late}
        self._write_json(self.predictions_file, preds)

    def remove_prediction(self, user, race):
        preds = self._read_json(self.predictions_file)
        if not isinstance(preds, dict):
            return
        if race in preds and isinstance(preds[race], dict) and user in preds[race]:
            del preds[race][user]
            self._write_json(self.predictions_file, preds)

    def get_predictions(self):
        res = self._read_json(self.predictions_file)
        return res if isinstance(res, dict) else {}

    def get_last_valid_picks(self, user, race_name, schedule):
        """Find the user's most recent prediction from a race BEFORE the
        given race.  This is used to carry forward picks when a user
        misses a race.  Only races earlier in the schedule are considered,
        so we never pull a "future" prediction as the fallback."""
        all_preds = self.get_predictions()
        current_round = None
        for r in schedule:
            if r["name"] == race_name:
                current_round = r["round"]
                break
        if current_round is None:
            return None

        # Scan backwards through the schedule, skipping the current race
        # and any race that is at or after it.
        for r in reversed(schedule):
            if r["round"] >= current_round:
                continue
            prev_pred = all_preds.get(r["name"], {}).get(user)
            if prev_pred:
                return prev_pred["picks"]
        return None

    # ------------------------------------------------------------------
    # Users
    # ------------------------------------------------------------------

    def add_user(self, user):
        users = self.get_users()
        if user not in users:
            users.append(user)
            self._write_json(self.users_file, sorted(users))

    def remove_user(self, user):
        # Step 1: Remove from user list
        users = self.get_users()
        if user in users:
            users.remove(user)
            self._write_json(self.users_file, users)

        # Step 2: Remove from predictions by rebuilding the dict without the user
        preds = self._read_json(self.predictions_file)
        if not isinstance(preds, dict):
            return

        new_preds = {}
        for race, user_preds in preds.items():
            if isinstance(user_preds, dict):
                filtered_preds = {u: p for u, p in user_preds.items() if u != user}
                if filtered_preds:
                    new_preds[race] = filtered_preds
        self._write_json(self.predictions_file, new_preds)

    def get_users(self):
        res = self._read_json(self.users_file)
        return res if isinstance(res, list) else []

    # ------------------------------------------------------------------
    # Calendar & Results
    # ------------------------------------------------------------------

    def save_race_data(self, schedule, results_map):
        self._write_json(self.calendar_file, schedule)
        self._write_json(self.results_file, results_map)

    def update_single_race_result(self, round_num, results):
        res_map = self._read_json(self.results_file)
        if not isinstance(res_map, dict):
            res_map = {}
        res_map[str(round_num)] = results
        self._write_json(self.results_file, res_map)

    def get_schedule(self):
        res = self._read_json(self.calendar_file)
        return res if isinstance(res, list) else []

    def get_results_map(self):
        res = self._read_json(self.results_file)
        return res if isinstance(res, dict) else {}
