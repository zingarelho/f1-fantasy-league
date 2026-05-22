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

    @staticmethod
    def calculate_driver_breakdown(prediction, official_results_with_points, is_late=False, is_missing=False):
        """
        Returns (breakdown, subtotal, final_total).

        breakdown: list of dicts — one per driver slot:
            {pos: int, driver: str, earned: float, detail: str}
        subtotal: raw sum before penalty
        final_total: points after late/missing penalty
        """
        breakdown = []
        if not prediction or not official_results_with_points:
            return breakdown, 0.0, 0.0

        official_map = {res['id']: res['points'] for res in official_results_with_points}
        official_top_5_ids = [res['id'] for res in official_results_with_points[:5]]

        subtotal = 0.0
        for pos, driver in enumerate(prediction[:5]):
            pos_num = pos + 1
            if driver in official_top_5_ids:
                driver_raw = float(official_map.get(driver, 0))
                actual_pos = official_top_5_ids.index(driver) + 1
                if pos < len(official_results_with_points) and official_results_with_points[pos]['id'] == driver:
                    earned = driver_raw
                    detail = f"✅ Correct P{pos_num}"
                else:
                    earned = driver_raw / 2.0
                    detail = f"⚠️ In top 5 (actual P{actual_pos})"
            else:
                earned = 0.0
                detail = "❌ Not in top 5"

            subtotal += earned
            breakdown.append({
                "pos": pos_num,
                "driver": driver,
                "earned": earned,
                "detail": detail,
            })

        if is_late or is_missing:
            final_total = subtotal * 0.5
        else:
            final_total = subtotal

        return breakdown, subtotal, final_total
