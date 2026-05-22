# 🗄️ F1 Fantasy League — Google Sheets Persistence Guide

> **Problem:** On Streamlit Community Cloud, the `data/` folder with `predictions.json`, `users.json`, `calendar.json`, and `results.json` **disappears on every restart** because containers are ephemeral.
>
> **Solution:** Replace local JSON file storage with **Google Sheets**. Your data lives in a real spreadsheet that survives restarts, scaling, and inactivity — and you can even edit cells manually for quick fixes.

---

## 📖 Table of Contents

1. [Create a Google Cloud project & enable Sheets API](#step-1--create-a-google-cloud-project--enable-sheets-api)
2. [Create the 4 Google Sheets tabs](#step-2--create-the-4-google-sheets-tabs)
3. [Install `gspread`](#step-3--install-gspread)
4. [Rewrite `f1_data.py`](#step-4--rewrite-f1_datapy)
5. [Set up local secrets](#step-5--set-up-local-secrets-streamlit-secrets)
6. [Set secrets on Streamlit Cloud](#step-6--set-secrets-on-streamlit-community-cloud)
7. [Test locally](#step-7--test-locally)
8. [Deploy & verify persistence](#step-8--deploy--verify-persistence)
9. [What the sheet looks like](#-how-it-works-visually)

---

## Step 1 — Create a Google Cloud project & enable Sheets API

1. Go to https://console.cloud.google.com
2. Click **Create Project** → name it `f1-fantasy-league` (or whatever you like)
3. Once the project opens, go to **APIs & Services → Library**
4. Search for **Google Sheets API**, click it, then **Enable**
5. Go to **APIs & Services → Credentials**
6. Click **Create Credentials → Service Account**
   - Name: `f1-sheets-bot`
   - Role: leave as *Basic → Editor* (or skip and set later)
   - Click **Done**
7. In the service accounts list, click the one you just created
8. Go to the **Keys** tab → **Add Key → Create New Key**
   - Format: **JSON**
   - A `.json` file will download — **keep this safe**, this is your only copy
9. Open that JSON file — you'll need its contents in [Step 5](#step-5--set-up-local-secrets-streamlit-secrets)

---

## Step 2 — Create the 4 Google Sheets tabs

1. Go to https://sheets.new → name the spreadsheet `F1 Fantasy League`
2. Rename the default tab (right-click → Rename) to **Users**
3. Add 3 more tabs (click the **+** at the bottom): **Predictions**, **Calendar**, **Results**
4. Fill in **header rows** (Row 1) for each tab:

**Users tab** (1 column):

```
username
```

**Predictions tab** (4 columns):

```
race_name | username | picks | is_late
```

> `picks` will be stored as a JSON string like `["VER","NOR","HAM","LEC","PIA"]`
> `is_late` will be `True` or `False`

**Calendar tab** (4 columns):

```
round | name | date | status
```

**Results tab** (2 columns):

```
round | top5
```

> `top5` will be stored as a JSON string like `[{"id":"VER","points":25},...]`

5. Click **Share** in the top-right corner
6. Paste the **service account email** from Step 1 (looks like `f1-sheets-bot@your-project.iam.gserviceaccount.com`)
7. Give it **Editor** permission
8. Copy the **spreadsheet ID** from the URL:

```
https://docs.google.com/spreadsheets/d/THIS_IS_THE_ID/edit#gid=...
```

👉 `THIS_IS_THE_ID` — you'll need it in Step 5.

---

## Step 3 — Install `gspread`

Add to `requirements.txt`:

```txt
streamlit
requests
gspread
```

---

## Step 4 — Rewrite `f1_data.py`

Replace the entire `f1_data.py` file with the code below.  
The **public API is identical** (`save_prediction`, `get_predictions`, `add_user`, `get_users`, `save_race_data`, `get_schedule`, `get_results_map`, etc.) — `app.py`, `f1_engine.py`, and `f1_client.py` need **zero changes**.

```python
# myfiles/f1-fantasy-league/f1_data.py
import json
import streamlit as st
import gspread
from typing import List, Dict, Any, Optional
from oauth2client.service_account import ServiceAccountCredentials


# ----------------------------------------------------------------------
# Google Sheets client – initialised once per process
# ----------------------------------------------------------------------
_SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]


def _get_sheet() -> gspread.Worksheet:
    """Return the main spreadsheet object."""
    creds_dict = st.secrets["GDRIVE"]["service_account"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, _SCOPE)
    client = gspread.authorize(creds)
    spreadsheet_id = st.secrets["GDRIVE"]["spreadsheet_id"]
    return client.open_by_key(spreadsheet_id)


def _worksheet(name: str) -> gspread.Worksheet:
    return _get_sheet().worksheet(name)


# ----------------------------------------------------------------------
# Low-level helpers
# ----------------------------------------------------------------------

def _clear_and_write(ws: gspread.Worksheet, headers: List[str], rows: List[List]):
    """Replace entire sheet content atomically."""
    ws.clear()
    if rows:
        ws.update([headers] + rows, value_input_option="USER_ENTERED")
    else:
        ws.update([headers], value_input_option="USER_ENTERED")


def _read_all(ws: gspread.Worksheet) -> List[Dict[str, Any]]:
    """Read all rows as a list of dicts (keys from header row)."""
    records = ws.get_all_records()
    return records if records else []


def _add_row(ws: gspread.Worksheet, row: List[Any]):
    """Append a single row."""
    ws.append_row(row, value_input_option="USER_ENTERED")


# ----------------------------------------------------------------------
# DataManager – public API unchanged
# ----------------------------------------------------------------------

class DataManager:
    def __init__(self):
        pass

    # -------------------- Predictions --------------------

    def save_prediction(self, user: str, race: str, prediction: List[str], is_late: bool) -> None:
        """
        Upsert a prediction for a user/race.
        (race is a string like "Bahrain Grand Prix")
        """
        ws = _worksheet("Predictions")
        all_rows = ws.get_all_values()
        headers = all_rows[0] if all_rows else []
        data_rows = all_rows[1:] if len(all_rows) > 1 else []

        # Look for existing entry for this user+race
        found = False
        new_data_rows = []
        for row in data_rows:
            if len(row) >= 2 and row[0] == race and row[1] == user:
                # Update existing row
                new_data_rows.append([race, user, json.dumps(prediction), str(is_late)])
                found = True
            else:
                new_data_rows.append(row)

        if not found:
            # Append new row
            new_data_rows.append([race, user, json.dumps(prediction), str(is_late)])

        # If sheet only had headers, just set it
        if not all_rows:
            new_data_rows = [[race, user, json.dumps(prediction), str(is_late)]]
            ws.update([headers, *new_data_rows], value_input_option="USER_ENTERED")
        else:
            # Re-write all rows
            ws.update([headers, *new_data_rows], value_input_option="USER_ENTERED")

    def remove_prediction(self, user: str, race: str) -> None:
        ws = _worksheet("Predictions")
        all_rows = ws.get_all_values()
        if not all_rows:
            return
        headers = all_rows[0]
        data_rows = all_rows[1:] if len(all_rows) > 1 else []
        filtered = [row for row in data_rows if not (row[0] == race and row[1] == user)]
        ws.update([headers, *filtered], value_input_option="USER_ENTERED")

    def get_predictions(self) -> Dict[str, Dict[str, Dict]]:
        """
        Returns: { race_name: { user: { "picks": [...], "is_late": bool } } }
        """
        records = _read_all(_worksheet("Predictions"))
        out: Dict[str, Dict[str, Dict]] = {}
        for rec in records:
            race = rec.get("race_name", "").strip()
            username = rec.get("username", "").strip()
            picks_str = rec.get("picks", "[]").strip()
            late_str = rec.get("is_late", "False").strip()
            try:
                picks = json.loads(picks_str)
            except (json.JSONDecodeError, TypeError):
                picks = []
            is_late = late_str.lower() == "true"
            if race and username:
                out.setdefault(race, {})[username] = {
                    "picks": picks,
                    "is_late": is_late,
                }
        return out

    def get_last_valid_picks(self, user: str, race_name: str, schedule: List[Dict]) -> Optional[List[str]]:
        """
        Unchanged logic – uses the new get_predictions().
        """
        all_preds = self.get_predictions()
        current_round = None
        for r in schedule:
            if r["name"] == race_name:
                current_round = r["round"]
                break
        if current_round is None:
            return None

        for r in reversed(schedule):
            if r["round"] >= current_round:
                continue
            prev = all_preds.get(r["name"], {}).get(user)
            if prev:
                return prev["picks"]
        return None

    # -------------------- Users --------------------

    def add_user(self, user: str) -> None:
        ws = _worksheet("Users")
        existing = ws.col_values(1)  # column A
        if user not in existing:
            _add_row(ws, [user])

    def remove_user(self, user: str) -> None:
        # Remove from Users sheet
        ws = _worksheet("Users")
        all_rows = ws.get_all_values()
        if not all_rows:
            return
        headers = all_rows[0]
        data_rows = all_rows[1:] if len(all_rows) > 1 else []
        filtered = [row for row in data_rows if row[0] != user]
        ws.update([headers, *filtered], value_input_option="USER_ENTERED")

        # Remove from Predictions too
        ws_pred = _worksheet("Predictions")
        pred_rows = ws_pred.get_all_values()
        if len(pred_rows) > 1:
            h = pred_rows[0]
            d = pred_rows[1:]
            clean = [row for row in d if len(row) >= 2 and row[1] != user]
            ws_pred.update([h, *clean], value_input_option="USER_ENTERED")

    def get_users(self) -> List[str]:
        records = _read_all(_worksheet("Users"))
        return [r.get("username", "").strip() for r in records if r.get("username", "").strip()]

    # -------------------- Calendar & Results --------------------

    def save_race_data(self, schedule: List[Dict], results_map: Dict[int, List[Dict]]) -> None:
        """
        schedule: list of dicts with keys: round, name, date, status
        results_map: { round: [ {"id": "...", "points": ...}, ... ] }
        """
        # Save calendar
        ws_cal = _worksheet("Calendar")
        cal_headers = ["round", "name", "date", "status"]
        cal_rows = [
            [r.get("round", ""), r.get("name", ""), r.get("date", ""), r.get("status", "Scheduled")]
            for r in schedule
        ]
        _clear_and_write(ws_cal, cal_headers, cal_rows)

        # Save results
        ws_res = _worksheet("Results")
        res_headers = ["round", "top5"]
        res_rows = [
            [str(round_num), json.dumps(top5)]
            for round_num, top5 in results_map.items()
        ]
        _clear_and_write(ws_res, res_headers, res_rows)

    def update_single_race_result(self, round_num: int, results: List[Dict]) -> None:
        ws = _worksheet("Results")
        all_rows = ws.get_all_values()
        headers = all_rows[0] if all_rows else ["round", "top5"]
        data_rows = all_rows[1:] if len(all_rows) > 1 else []

        round_str = str(round_num)
        found = False
        new_data_rows = []
        for row in data_rows:
            if row[0] == round_str:
                new_data_rows.append([round_str, json.dumps(results)])
                found = True
            else:
                new_data_rows.append(row)

        if not found:
            new_data_rows.append([round_str, json.dumps(results)])

        if not all_rows:
            ws.update([headers, *new_data_rows], value_input_option="USER_ENTERED")
        else:
            ws.update([headers, *new_data_rows], value_input_option="USER_ENTERED")

    def get_schedule(self) -> List[Dict]:
        records = _read_all(_worksheet("Calendar"))
        out = []
        for rec in records:
            out.append({
                "round": int(rec.get("round", 0)),
                "name": str(rec.get("name", "")),
                "date": str(rec.get("date", "")),
                "status": str(rec.get("status", "Scheduled")),
            })
        return out

    def get_results_map(self) -> Dict[str, List[Dict]]:
        records = _read_all(_worksheet("Results"))
        out: Dict[str, List[Dict]] = {}
        for rec in records:
            round_str = str(rec.get("round", ""))
            top5_str = rec.get("top5", "[]")
            try:
                top5 = json.loads(top5_str) if isinstance(top5_str, str) else top5_str
            except (json.JSONDecodeError, TypeError):
                top5 = []
            out[round_str] = top5
        return out
```

---

## Step 5 — Set up local secrets (`.streamlit/secrets.toml`)

Create the file `.streamlit/secrets.toml` inside the `f1-fantasy-league/` folder:

```toml
[GDRIVE]
spreadsheet_id = "THE_SPREADSHEET_ID_FROM_STEP_2"

[GDRIVE.service_account]
type = "service_account"
project_id = "your-project-id"
private_key_id = "your-key-id"
private_key = "-----BEGIN PRIVATE KEY-----\nYOUR_KEY_HERE\n-----END PRIVATE KEY-----\n"
client_email = "f1-sheets-bot@your-project.iam.gserviceaccount.com"
client_id = "your-client-id"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/f1-sheets-bot%40your-project.iam.gserviceaccount.com"
```

> ⚠️ **Do NOT commit this file to git!**

Add `.streamlit/secrets.toml` to your `.gitignore`:

```
# .gitignore
.streamlit/secrets.toml
```

---

## Step 6 — Set secrets on Streamlit Community Cloud

1. Push your code to GitHub (without `secrets.toml`)
2. In the Streamlit Cloud dashboard → your app → **Settings → Secrets**
3. Paste the **entire** TOML content from Step 5 (the whole `[GDRIVE]` + `[GDRIVE.service_account]` block)
4. Click **Save**

The app will now use these secrets at runtime instead of a local file.

---

## Step 7 — Test locally

```bash
cd myfiles/f1-fantasy-league
pip install -r requirements.txt
streamlit run app.py
```

Checklist:
- [ ] Adding a user writes to the **Users** tab
- [ ] Submitting a prediction appears in the **Predictions** tab
- [ ] Clicking "Refresh All Data from API" fills the **Calendar** and **Results** tabs
- [ ] Refreshing the Streamlit page **reloads all data** from the sheet

You can also open the Google Sheet in a browser tab and watch cells update in real time as you interact with the app.

---

## Step 8 — Deploy & verify persistence

1. Push your code to GitHub (ensure `.streamlit/secrets.toml` is in `.gitignore`)
2. Deploy via Streamlit Cloud (it auto-detects `requirements.txt`)
3. Confirm secrets are set in **Settings → Secrets** (Step 6)
4. Open the deployed app → add a user → submit a prediction
5. **Manually restart the app** from the Streamlit Cloud dashboard (or wait for the container to recycle due to inactivity)
6. After restart → **verify that users, predictions, calendar, and results are all still there** 🎉

---

## 📋 How it works visually

After you interact with the app, your Google Sheet will look like this:

### Users tab

| username |
|---|
| Carlos |
| Maria |
| João |

### Predictions tab

| race_name | username | picks | is_late |
|---|---|---|---|
| Bahrain Grand Prix | Carlos | ["VER","NOR","LEC","HAM","PIA"] | False |
| Chinese Grand Prix | Maria | ["NOR","VER","LEC","RUS","HAM"] | True |

### Calendar tab

| round | name | date | status |
|---|---|---|---|
| 1 | Bahrain Grand Prix | 2026-03-01 | Scheduled |
| 2 | Saudi Arabian Grand Prix | 2026-03-08 | Scheduled |
| 3 | Australian Grand Prix | 2026-03-22 | Scheduled |
| … | … | … | … |
| 22 | Abu Dhabi Grand Prix | 2026-12-06 | Scheduled |

### Results tab

| round | top5 |
|---|---|
| 1 | [{"id":"VER","points":25},{"id":"NOR","points":18},{"id":"LEC","points":15},{"id":"HAM","points":12},{"id":"PIA","points":10}] |

---

## 🧰 Pro tips

- **Manual edits:** You can edit any cell directly in Google Sheets. The app will pick up the changes on the next read — handy for quick data fixes or testing without the UI.
- **JSON formatting:** `picks` and `top5` columns store JSON strings. Make sure any manual edits are valid JSON (use double quotes, not single quotes).
- **Rate limits:** Google Sheets has a limit of ~60 requests per minute per user. For a small fantasy league this is more than enough. If you expect hundreds of concurrent users, consider Supabase or a proper database instead.
- **Backup:** Since the data is in Google Sheets, Google handles backups automatically (version history is available under **File → Version history**).
- **Debugging:** If something goes wrong, open the sheet and check the raw cells. You can also enable Streamlit's debug mode to see API call errors.

---

> ✅ **Once these steps are done, the F1 Fantasy League app will retain its state across Streamlit Cloud restarts, just like it does on your local machine.**