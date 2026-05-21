import json
import os

class DataManager:
    def __init__(self, data_folder="data"):
        self.data_folder = data_folder
        # Ensure folder exists
        if not os.path.exists(self.data_folder):
            try:
                os.makedirs(self.data_folder, exist_ok=True)
            except Exception as e:
                print(f"DataManager Folder Error: {e}")
            
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
        if race not in preds: preds[race] = {}
        preds[race][user] = {"picks": prediction, "is_late": is_late}
        self._write_json(self.predictions_file, preds)

    def remove_prediction(self, user, race):
        preds = self._read_json(self.predictions_file)
        if race in preds and user in preds[race]:
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
            for race in preds:
                if user in preds[race]:
                    del preds[race][user]
            self._write_json(self.predictions_file, preds)

    def save_race_data(self, schedule, results_map):
        self._write_json(self.calendar_file, schedule)
        self._write_json(self.results_file, results_map)

    def update_single_race_result(self, round_num, results):
        res_map = self._read_json(self.results_file)
        res_map[str(round_num)] = results
        self._write_json(self.results_file, res_map)

    def get_predictions(self):
        return self._read_json(self.predictions_file)

    def get_schedule(self):
        return self._read_json(self.calendar_file)

    def get_results_map(self):
        return self._read_json(self.results_file)
        
    def get_users(self):
        res = self._read_json(self.users_file)
        return res if isinstance(res, list) else []
