import streamlit as st
from f1_engine import ScoringEngine
from f1_client import RaceClient
from f1_data import DataManager

st.set_page_config(page_title="F1 Fantasy League", layout="wide")
st.title("🏎️ F1 Fantasy League")

# Initialize clients with caching
@st.cache_data(ttl=3600) # Cache API data for 1 hour
def get_cached_schedule():
    return RaceClient().get_schedule()

@st.cache_data(ttl=3600) # Cache API data for 1 hour
def get_cached_results(round_num):
    return RaceClient().get_results(round_num)

client = RaceClient()
dm = DataManager()
engine = ScoringEngine()

tab1, tab2, tab3 = st.tabs(["Leaderboard", "Input Predictions", "Race Info"])

with tab1:
    st.header("Current Standings")
    
    all_predictions = dm.load_all() 
    schedule = get_cached_schedule()
    
    if not schedule:
        st.error("Unable to load race schedule. Please check back later.")
    else:
        leaderboard = {}
        
        # Find all unique users across the whole dataset
        all_users = set()
        for r_data in all_predictions.values():
            all_users.update(r_data.keys())
            
        for race in schedule:
            race_name = race['name']
            results = get_cached_results(race['round'])
            
            for user in all_users:
                pred_data = all_predictions.get(race_name, {}).get(user)
                
                if pred_data:
                    pts = engine.calculate_points(
                        pred_data['picks'], 
                        results, 
                        is_late=pred_data.get('is_late', False)
                    )
                else:
                    last_valid_picks = None
                    for prev_race in reversed(schedule):
                        if prev_race['name'] == race_name:
                            continue
                        prev_pred = all_predictions.get(prev_race['name'], {}).get(user)
                        if prev_pred:
                            last_valid_picks = prev_pred['picks']
                            break
                    
                    if last_valid_picks:
                        pts = engine.calculate_points(
                            last_valid_picks, 
                            results, 
                            is_missing=True
                        )
                    else:
                        pts = 0
                
                leaderboard[user] = leaderboard.get(user, 0) + pts

        sorted_leaderboard = sorted(leaderboard.items(), key=lambda x: x[1], reverse=True)
        if sorted_leaderboard:
            st.table([{"User": u, "Total Points": p} for u, p in sorted_leaderboard])
        else:
            st.write("No predictions found yet!")

with tab2:
    st.header("Submit Prediction")
    races = get_cached_schedule()
    if races:
        selected_race = st.selectbox("Race", [r['name'] for r in races])
        user_name = st.text_input("Your Name")
        picks = st.text_input("Top 5 (comma separated, e.g., VER, NOR, HAM, LEC, PER)")
        is_late = st.checkbox("Submitted after qualifying?")
        
        if st.button("Save Prediction"):
            if user_name and picks:
                pick_list = [p.strip().upper() for p in picks.split(",")]
                dm.save_prediction(user_name, selected_race, pick_list, is_late)
                st.success(f"Prediction saved for {user_name}!")
                st.rerun()
    else:
        st.error("Race schedule not available.")

with tab3:
    st.header("Schedule & Results")
    schedule_data = get_cached_schedule()
    if schedule_data:
        st.table(schedule_data)
    else:
        st.write("No schedule data to display.")
