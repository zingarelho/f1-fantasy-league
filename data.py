
import json
import os

class DataManager:
    def __init__(self, file_path="predictions.json"):
        self.file_path = file_path

    def save_prediction(self, user, race, prediction, is_late):
        data = self.load_all()
        if race not in data: data[race] = {}
        data[race][user] = {"picks": prediction, "is_late": is_late}
        with open(self.file_path, "w") as f:
            json.dump(data, f)

    def load_all(self):
        if not os.path.exists(self.file_path): return {}
        with open(self.file_path, "r") as f:
            return json.load(f)
