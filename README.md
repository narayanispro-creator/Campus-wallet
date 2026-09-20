# Campus Wallet — College Expense Tracker

A complete BTech Computer Science mini project using **Python Flask, SQLite, HTML, CSS and JavaScript**. Track expenses, set a monthly budget, and see where your money goes. Currency: INR (₹).

## Requirements

- Python **3.10 or newer**, with pip and venv
- A current Chrome, Edge, Firefox or Safari browser
- Internet only for the initial dependency installation; the running app uses no external services

## Setup and run

Extract the ZIP and open a terminal inside the `campus-wallet` folder containing `app.py`.

### Windows (Command Prompt)

```bat
py -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
python app.py
```

### macOS / Linux

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python app.py
```

Open **http://127.0.0.1:5000** in your browser. Stop the server with **Ctrl+C**. The database and tables are created automatically on first launch. Start it again with the same command; your entries remain saved.

If port 5000 is occupied (including by AirPlay on some Macs), use:

```sh
python -m flask --app app run --host 127.0.0.1 --port 5050
```

Then open **http://127.0.0.1:5050**.

## Optional demo data

With the virtual environment activated, run this before or after starting the app:

```sh
python -m flask --app app seed-demo
```

This adds **10 fictional expenses totalling ₹8,959** and a **₹15,000 budget** for the current calendar month. Refresh the browser. The seed command refuses to run if either table already contains data, so it cannot overwrite your work. Demo dates use days 1–18 of the current month, even if some dates are in the future.

The ZIP intentionally contains no database; it starts empty unless you choose to seed it.

## Using the app

1. Choose a month in the overview.
2. Click **Add expense**, enter a description, amount, date and category, then save.
3. Use **Edit** or **Delete** next to an expense. Deletion asks for confirmation and has no undo.
4. Click **Edit ↗** on the monthly budget card to set or replace that month's budget.
5. Inspect total spending, budget remaining (or amount over budget), daily bars and category shares.
6. Search descriptions/notes and filter the transaction list by category. Summary cards and charts always describe the **whole selected month**; the list footer shows the filtered subtotal.
7. Click a daily bar to see its exact amount. Hover and keyboard focus also expose labelled values.

Adding or moving an expense to a different month automatically selects that expense's month. Future-dated entries are allowed and counted in their chosen month. Budgets must be positive; a missing budget is shown as “Not set”.

## Run automated tests

```sh
python -m unittest discover -s tests -v
```

Twelve tests cover CRUD, totals, precision, persistence, leap years, year boundaries, budgets, validation, missing records, CSRF, malformed JSON and safe demo seeding. They use temporary databases and do not change your data.

## Project files

```text
campus-wallet/
├── app.py                  # Application factory, schema, API, demo command
├── requirements.txt        # Flask (SQLite is included with Python)
├── templates/index.html    # Dashboard and accessible forms
├── static/style.css        # Responsive layout and chart styles
├── static/app.js           # Fetch requests, rendering, charts, filters
├── tests/test_app.py       # Standard-library unittest integration tests
├── README.md               # Setup and user guide
├── PROJECT_REPORT.md       # Academic report and viva notes
└── instance/wallet.sqlite3 # Created locally at runtime, not in ZIP
```

## Data, backup and scope

All records are in `instance/wallet.sqlite3` on the computer running Flask. Stop the server before copying this file for a consistent backup. Restore by replacing it with your backup while the server is stopped. To start fresh, move the existing database to a backup location and restart; do not delete your only copy.

This is a **single-user local educational app**. There is no login, cloud sync, encryption at rest, currency conversion or payment integration. Do not expose the development server publicly. The default launch binds only to `127.0.0.1` with debug disabled.

A random session secret is generated each startup; refreshing the page after restarting restores a valid CSRF session. You may set a stable `SECRET_KEY` environment variable if needed; do not commit it. No secret is required to run the project.

## Troubleshooting

- **No module named flask:** activate `.venv`, then run `python -m pip install -r requirements.txt`.
- **Browser cannot connect:** keep the server terminal open and use the exact printed URL.
- **Session expired:** refresh after restarting Flask, then submit again.
- **No expenses visible:** check the selected month, search text and category filter.
- **Permission error on database:** extract into a writable folder rather than running inside the ZIP.
- **Windows PowerShell blocks activation:** use Command Prompt and the commands above, or run `.venv\Scripts\python.exe app.py` directly after installing requirements with that interpreter.

See `PROJECT_REPORT.md` for objectives, architecture, database design, testing, limitations, future scope and a presentation walkthrough.
