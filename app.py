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
# CSS helper for card styling
# ---------------------------------------------------------------------------

_CARD_CSS = """
<style>
.f1-card {
    border: 1px solid #e0e0e0;
    border-radius: 12px;
    padding: 18px;
    margin-bottom: 16px;
    background: #fafafa;
}
.f1-card h4 {
    margin: 0 0 4px 0;
}
.f1-card .subtitle {
    margin: 0 0 12px 0;
    color: #888;
    font-size: 0.9em;
}
.f1-driver-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.95em;
}
.f1-driver-table th {
    padding: 6px 12px;
    background: #f0f0f0;
    font-weight: bold;
    text-align: left;
}
.f1-driver-table td {
    padding: 4px 12px;
    border-bottom: 1px solid #eee;
}
.f1-driver-table .pts { text-align: right; }
.f1-driver-table .detail { font-size: 0.85em; color: #666; }
.f1-total-row td {
    padding: 8px 12px;
    text-align: right;
    font-weight: bold;
    font-size: 1.1em;
    border-bottom: none;
}
.f1-penalty-row td {
    padding: 4px 12px;
    text-align: right;
    color: #d40;
    font-weight: bold;
    border-bottom: none;
}
</style>
"""


# ---------------------------------------------------------------------------
# Bootstrap data on first load
# ---------------------------------------------------------------------------

current_schedule = dm.get_schedule()
if not current_schedule:
    refresh_all_data()
    current_schedule = dm.get_schedule()

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Leaderboard", "Predictions", "Input Predictions", "Race Info",
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
# TAB 2 — Predictions (card-per-race with per-driver points)
# ---------------------------------------------------------------------------

with tab2:
    st.header("Predictions")
    users = dm.get_users()
    if not users:
        st.write("No users registered.")
    else:
        selected_user = st.selectbox(
            "Select User", users, key="user_pred_perf",
        )
        all_predictions = dm.get_predictions()
        results_map = dm.get_results_map()

        st.html(_CARD_CSS)

        for race in current_schedule:
            race_name = race["name"]
            round_num = race["round"]
            date = race.get("date", "")
            res = results_map.get(str(round_num), [])
            has_results = bool(res and isinstance(res, list) and len(res) > 0)

            status_icon = "✅" if has_results else "📅"
            status_text = "Finished" if has_results else "Scheduled"

            # Determine prediction source
            pred_data = all_predictions.get(race_name, {}).get(selected_user)

            if pred_data:
                picks = pred_data["picks"]
                is_late = pred_data.get("is_late", False)
                is_missing = False
                source_note = ""
                late_badge = " ⏰ Late" if is_late else ""
            else:
                last_picks = dm.get_last_valid_picks(
                    selected_user, race_name, current_schedule
                )
                if last_picks:
                    picks = last_picks
                    is_late = False
                    is_missing = True
                    source_note = "⏩ Carried forward from a prior race"
                    late_badge = ""
                else:
                    picks = None
                    source_note = ""
                    late_badge = ""

            # --- Card ---
            card_html = f"""
            <div class="f1-card">
                <h4>Round {round_num} — {race_name}</h4>
                <div class="subtitle">{date} · {status_icon} {status_text}{late_badge}</div>
            """

            if picks and has_results:
                breakdown, subtotal, final_total = engine.calculate_driver_breakdown(
                    picks, res, is_late=is_late, is_missing=is_missing,
                )

                rows = ""
                for b in breakdown:
                    rows += f"""<tr>
                        <td>P{b['pos']}</td>
                        <td><b>{b['driver']}</b></td>
                        <td class="pts">{b['earned']:.1f}</td>
                        <td class="detail">{b['detail']}</td>
                    </tr>"""

                penalty = ""
                if is_late:
                    penalty = f"""<tr class="f1-penalty-row">
                        <td colspan="4">⏰ Late penalty (-50%): {subtotal:.1f} → {final_total:.1f}</td>
                    </tr>"""
                elif is_missing:
                    penalty = f"""<tr class="f1-penalty-row">
                        <td colspan="4">⏩ Carry-forward penalty (-50%): {subtotal:.1f} → {final_total:.1f}</td>
                    </tr>"""

                card_html += f"""
                <table class="f1-driver-table">
                    <tr><th>Slot</th><th>Driver</th><th class="pts">Points</th><th>Detail</th></tr>
                    {rows}
                    {penalty}
                    <tr class="f1-total-row">
                        <td colspan="4">🏁 Total: {final_total:.1f} pts</td>
                    </tr>
                </table>
                """

                if source_note:
                    card_html += f'<p style="margin:8px 0 0 0;font-size:0.85em;color:#999;">{source_note}</p>'

            elif picks and not has_results:
                card_html += f'<p style="margin:8px 0 0 0;color:#999;">Picks: <b>{", ".join(picks)}</b> — race not yet run</p>'
            else:
                card_html += '<p style="margin:8px 0 0 0;color:#999;">No prediction yet</p>'

            card_html += "</div>"
            st.html(card_html)

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
# TAB 4 — Race Info (card-per-race)
# ---------------------------------------------------------------------------

with tab4:
    st.header("Schedule & Results")
    if current_schedule:
        if st.button("🔄 Refresh All Data from API"):
            refresh_all_data()
            st.rerun()

        results_map = dm.get_results_map()
        st.html(_CARD_CSS)

        for race in current_schedule:
            round_num = race["round"]
            race_name = race["name"]
            date = race.get("date", "")
            res = results_map.get(str(round_num), [])
            has_results = bool(res and isinstance(res, list) and len(res) > 0)

            status_icon = "✅" if has_results else "📅"
            status_text = "Finished" if has_results else "Scheduled"

            card_html = f"""
            <div class="f1-card">
                <h4>Round {round_num} — {race_name}</h4>
                <div class="subtitle">{date} · {status_icon} {status_text}</div>
            """

            if has_results:
                rows = ""
                for i, r in enumerate(res):
                    pos = i + 1
                    rows += f"""<tr>
                        <td>P{pos}</td>
                        <td><b>{r['id']}</b></td>
                        <td class="pts">{r['points']}</td>
                    </tr>"""

                card_html += f"""
                <table class="f1-driver-table">
                    <tr><th>Pos</th><th>Driver</th><th class="pts">Points</th></tr>
                    {rows}
                </table>
                """

            card_html += "</div>"
            st.html(card_html)

        st.markdown("---")
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