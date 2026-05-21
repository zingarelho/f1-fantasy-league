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

    def _write_json(self, path, data):
        try:
            with open(path, "w") as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            print(f"Write Error {path}: {e}")

    def _read_json(self, path):
        if not os.path.exists(path): return {}
        try:
            with open(path, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"Read Error {path}: {e}")
            return {}

    def save_prediction(self, user, race, prediction, is_late):
        preds = self._read_json(self.predictions_file)
        if not isinstance(preds, dict): preds = {}
        if race not in preds: preds[race] = {}
        if not isinstance(preds[race], dict): preds[race] = {}
        preds[race][user] = {"picks": prediction, "is_late": is_late}
        self._write_json(self.predictions_file, preds)

    def remove_prediction(self, user, race):
        preds = self._read_json(self.predictions_file)
        if not isinstance(preds, dict): return
        if race in preds and isinstance(preds[race], dict) and user in preds[race]:
            del preds[race][user]
            self._write_json(self.predictions_file, preds)

    def add_user(self, user):
        users = self.get_users()
        if user not in users:
            users.append(user)
            self._write_json(self.users_file, sorted(users))

    def remove_user(self, user):
        users = self.get_users()
        if user in users:
            users.remove(user)
            self._write_json(self.users_file, users)
            preds = self._read_json(self.predictions_file)
            if isinstance(preds, dict):
                for race in preds:
                    if isinstance(preds[race], dict) and user in preds[race]:
                        del preds[race][user]
                self._write_json(self.predictions_file, preds)

    def save_race_data(self, schedule, results_map):
        self._write_json(self.calendar_file, schedule)
        self._write_json(self.results_file, results_map)

    def update_single_race_result(self, round_num, results):
        res_map = self._read_json(self.results_file)
        if not isinstance(res_map, dict): res_map = {}
        res_map[str(round_num)] = results
        self._write_json(self.results_file, res_map)

    def get_predictions(self):
        res = self._read_json(self.predictions_file)
        return res if isinstance(res, dict) else {}

    def get_schedule(self):
        res = self._read_json(self.calendar_file)
        return res if isinstance(res, list) else []

    def get_results_map(self):
        res = self._read_json(self.results_file)
        return res if isinstance(res, dict) else {}
        
    def get_users(self):
        res = self._read_json(self.users_file)
        return res if isinstance(res, list) else []
