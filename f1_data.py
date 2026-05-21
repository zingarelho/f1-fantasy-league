import json
import os

class DataManager:
    def __init__(self, file_path="predictions.json"):
        self.file_path = file_path

    def save_prediction(self, user, race, prediction, is_late):
        data = self.load_all()
        predictions = data.get('predictions', {})
        if race not in predictions: predictions[race] = {}
        predictions[race][user] = {"picks": prediction, "is_late": is_late}
        data['predictions'] = predictions
        with open(self.file_path, "w") as f:
            json.dump(data, f)

    def save_race_data(self, schedule, results_map):
        data = self.load_all()
        data['schedule'] = schedule
        data['results'] = results_map 
        with open(self.file_path, "w") as f:
            json.dump(data, f)

    def load_all(self):
        if not os.path.exists(self.file_path): return {}
        with open(self.file_path, "r") as f:
            try:
                return json.load(f)
            except:
                return {}

    def get_predictions(self):
        return self.load_all().get('predictions', {})

    def get_schedule(self):
        return self.load_all().get('schedule', [])

    def get_results_map(self):
        return self.load_all().get('results', {})
