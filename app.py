import streamlit as st
from f1_engine import ScoringEngine
from f1_client import RaceClient
from f1_data import DataManager

st.set_page_config(page_title="F1 Fantasy League", layout="wide")
st.title("🏎️ F1 Fantasy League")

client = RaceClient()
dm = DataManager()
engine = ScoringEngine()

# PERSISTENCE SYNC: Update calendar and results if missing
current_schedule = dm.get_schedule()
if not current_schedule:
    st.info("Updating 2026 Calendar...")
    current_schedule = client.get_full_2026_calendar()
    results_map = {}
    for race in current_schedule:
        if race['status'] == 'Finished':
            results_map[race['round']] = client.get_results(race['round'])
    dm.save_race_data(current_schedule, results_map)
    current_schedule = dm.get_schedule()

tab1, tab2, tab3 = st.tabs(["Leaderboard", "Input Predictions", "Race Info"])

with tab1:
    st.header("Current Standings")
    all_predictions = dm.get_predictions()
    results_map = dm.get_results_map()
    leaderboard = {}
    all_users = set()
    for r_data in all_predictions.values():
        all_users.update(r_data.keys())
    for race in current_schedule:
        race_name = race['name']
        results = results_map.get(race['round'], [])
        if race['status'] == 'Finished' and not results:
            results = client.get_results(race['round'])
        for user in all_users:
            pred_data = all_predictions.get(race_name, {}).get(user)
            if pred_data:
                pts = engine.calculate_points(pred_data['picks'], results, is_late=pred_data.get('is_late', False))
            else:
                last_valid_picks = None
                for prev_race in reversed(current_schedule):
                    if prev_race['name'] == race_name: continue
                    prev_pred = all_predictions.get(prev_race['name'], {}).get(user)
                    if prev_pred:
                        last_valid_picks = prev_pred['picks']
                        break
                pts = engine.calculate_points(last_valid_picks, results, is_missing=True) if last_valid_picks else 0
            leaderboard[user] = leaderboard.get(user, 0) + pts

    sorted_leaderboard = sorted(leaderboard.items(), key=lambda x: x[1], reverse=True)
    if sorted_leaderboard:
        st.table([{"User": u, "Total Points": p} for u, p in sorted_leaderboard])
    else:
        st.write("No predictions found yet!")

with tab2:
    st.header("Submit Prediction")
    if current_schedule:
        selected_race = st.selectbox("Race", [r['name'] for r in current_schedule])
        user_name = st.text_input("Your Name")
        picks = st.text_input("Top 5 (comma separated, e.g., VER, NOR, HAM, LEC, PER)")
        is_late = st.checkbox("Submitted after qualifying?")
        if st.button("Save Prediction"):
            if user_name and picks:
                pick_list = [p.strip().upper() for p in picks.split(",")]
                dm.save_prediction(user_name, selected_race, pick_list, is_late)
                st.success(f"Prediction saved for {user_name}!")
                st.rerun()

with tab3:
    st.header("Schedule & Results")
    if current_schedule:
        full_info = []
        results_map = dm.get_results_map()
        for race in current_schedule:
            res = results_map.get(race['round'], "N/A")
            res_str = ", ".join(res) if isinstance(res, list) else res
            full_info.append({**race, "Top 5 Results": res_str})
        st.table(full_info)
