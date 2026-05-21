import streamlit as st
from f1_engine import ScoringEngine
from f1_client import RaceClient
from f1_data import DataManager

st.set_page_config(page_title="F1 Fantasy League", layout="wide")
st.title("🏎️ F1 Fantasy League")

client = RaceClient()
dm = DataManager()
engine = ScoringEngine()


# ---------------------------------------------------------------------------
# Data refresh helpers
# ---------------------------------------------------------------------------

def refresh_all_data():
    st.info("Fetching latest 2026 calendar and results from API...")
    schedule = client.get_full_2026_calendar()
    results_map = {}
    for race in schedule:
        results = client.get_results(race["round"])
        if results:
            results_map[race["round"]] = results
    dm.save_race_data(schedule, results_map)
    st.success("Global data refresh complete!")


def refresh_single_race(round_num):
    try:
        results = client.get_results(round_num)
        if results:
            dm.update_single_race_result(round_num, results)
            st.success(f"Updated results for Round {round_num}!")
        else:
            st.info(f"Round {round_num} hasn't happened yet — no classification available.")
    except Exception as e:
        st.error(f"Failed to fetch results for Round {round_num}: {e}")


def _calculate_user_pts(user, race, results, schedule, all_preds):
    """Calculate points for one user for one race, handling missing/late."""
    race_name = race["name"]
    pred_data = all_preds.get(race_name, {}).get(user)
    if pred_data:
        return engine.calculate_points(
            pred_data["picks"], results,
            is_late=pred_data.get("is_late", False),
        )
    # No prediction — carry forward last valid picks from a prior race
    last_picks = dm.get_last_valid_picks(user, race_name, schedule)
    if last_picks:
        return engine.calculate_points(
            last_picks, results, is_missing=True,
        )
    return 0


# ---------------------------------------------------------------------------
# Bootstrap data on first load
# ---------------------------------------------------------------------------

current_schedule = dm.get_schedule()
if not current_schedule:
    refresh_all_data()
    current_schedule = dm.get_schedule()

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Leaderboard", "User Details", "Input Predictions", "Race Info",
    "User Management",
])

# ---------------------------------------------------------------------------
# TAB 1 — Leaderboard
# ---------------------------------------------------------------------------

with tab1:
    st.header("Current Standings")
    all_predictions = dm.get_predictions()
    results_map = dm.get_results_map()
    leaderboard = {}
    all_users = dm.get_users()

    for race in current_schedule:
        results = results_map.get(str(race["round"]), [])
        for user in all_users:
            pts = _calculate_user_pts(
                user, race, results, current_schedule, all_predictions,
            )
            leaderboard[user] = leaderboard.get(user, 0) + pts

    sorted_leaderboard = sorted(
        leaderboard.items(), key=lambda x: x[1], reverse=True,
    )
    if sorted_leaderboard:
        st.table([
            {"User": u, "Total Points": round(p, 1)}
            for u, p in sorted_leaderboard
        ])
    else:
        st.write("No results to display yet!")

# ---------------------------------------------------------------------------
# TAB 2 — User Details
# ---------------------------------------------------------------------------

with tab2:
    st.header("User Performance")
    users = dm.get_users()
    if not users:
        st.write("No users registered.")
    else:
        selected_user = st.selectbox(
            "Select User for Performance", users, key="user_perf_select",
        )
        all_predictions = dm.get_predictions()
        results_map = dm.get_results_map()

        user_data = []
        for race in current_schedule:
            race_name = race["name"]
            res = results_map.get(str(race["round"]), [])
            pred = all_predictions.get(race_name, {}).get(selected_user)

            picks_str = ", ".join(pred["picks"]) if pred else "No Prediction"
            pts = _calculate_user_pts(
                selected_user, race, res, current_schedule, all_predictions,
            )

            user_data.append({
                "Race": race_name,
                "Predictions": picks_str,
                "Points": round(pts, 1),
            })
        st.table(user_data)

# ---------------------------------------------------------------------------
# TAB 3 — Submit Prediction
# ---------------------------------------------------------------------------

with tab3:
    st.header("Submit Prediction")
    if current_schedule:
        users = dm.get_users()
        if not users:
            st.warning("Please add users in 'User Management' first.")
        else:
            selected_user = st.selectbox(
                "Select User for Prediction", users, key="user_pred_select",
            )
            selected_race = st.selectbox(
                "Race", [r["name"] for r in current_schedule],
                key="race_pred_select",
            )
            picks = st.text_input(
                "Top 5 (comma separated, e.g., VER, NOR, HAM, LEC, PER)",
            )
            is_late = st.checkbox("Submitted after qualifying?")
            if st.button("Save Prediction"):
                if picks:
                    pick_list = [p.strip().upper() for p in picks.split(",")]
                    dm.save_prediction(
                        selected_user, selected_race, pick_list, is_late,
                    )
                    st.success(f"Prediction saved for {selected_user}!")
                    st.rerun()

            st.write("---")
            st.write("Remove existing prediction")
            if st.button("Delete Prediction for this Race"):
                dm.remove_prediction(selected_user, selected_race)
                st.success("Prediction removed!")
                st.rerun()

# ---------------------------------------------------------------------------
# TAB 4 — Race Info
# ---------------------------------------------------------------------------

with tab4:
    st.header("Schedule & Results")
    if current_schedule:
        if st.button("🔄 Refresh All Data from API"):
            refresh_all_data()
            st.rerun()

        full_info = []
        results_map = dm.get_results_map()
        for race in current_schedule:
            res = results_map.get(str(race["round"]), [])
            if res and isinstance(res, list):
                res_str = ", ".join(r["id"] for r in res)
                status = "Finished"
            else:
                res_str = "N/A"
                status = "Scheduled"
            full_info.append({
                "round": race["round"],
                "name": race["name"],
                "date": race["date"],
                "status": status,
                "Top 5 Official Results": res_str,
            })
        st.table(full_info)

        st.write("---")
        st.subheader("Update Specific Race Result")
        col1, col2 = st.columns([3, 1])
        race_to_upd = col1.selectbox(
            "Select Race to Update", [r["name"] for r in current_schedule],
            key="race_update_select",
        )
        if col2.button("Update Result"):
            rd = next(
                r["round"] for r in current_schedule
                if r["name"] == race_to_upd
            )
            refresh_single_race(rd)
            st.rerun()

# ---------------------------------------------------------------------------
# TAB 5 — User Management
# ---------------------------------------------------------------------------

with tab5:
    st.header("User Management")
    new_user = st.text_input("Add New User")
    if st.button("Add User"):
        if new_user:
            dm.add_user(new_user)
            st.success(f"User {new_user} added!")
            st.rerun()

    st.write("### Registered Users")
    users = dm.get_users()
    for u in users:
        col1, col2 = st.columns([4, 1])
        with col1:
            st.write(u)
        with col2:
            if st.button(f"Delete", key=f"del_{u}"):
                try:
                    dm.remove_user(u)
                    st.success(f"User {u} removed!")
                except Exception as e:
                    st.error(f"Failed to remove user {u}: {e}")
                st.rerun()