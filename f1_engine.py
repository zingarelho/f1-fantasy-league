class ScoringEngine:
    @staticmethod
    def calculate_points(prediction, official_results_with_points, is_late=False, is_missing=False):
        """
        prediction: List of driver IDs (e.g., ['VER', 'NOR', 'HAM', 'LEC', 'PER'])
        official_results_with_points: List of dicts [{'id': 'VER', 'points': 25}, ...]
        """
        total_points = 0
        if not prediction:
            return 0

        # Map official results for easy lookup
        official_map = {res['id']: res['points'] for res in official_results_with_points}
        
        for pos, driver in enumerate(prediction):
            if pos >= 5: break
            
            # Check if driver is in the actual Top 5
            official_top_5_ids = [res['id'] for res in official_results_with_points[:5]]
            
            if driver in official_top_5_ids:
                driver_real_points = official_map.get(driver, 0)
                
                # RULE: Right position = Full Points. Wrong position (but in Top 5) = Half Points.
                if pos < len(official_results_with_points) and official_results_with_points[pos]['id'] == driver:
                    total_points += driver_real_points
                else:
                    total_points += (driver_real_points / 2)
        
        # Flat 50% penalty for late or missing, non-compounding.
        if is_late or is_missing:
            total_points *= 0.5
            
        return total_points
