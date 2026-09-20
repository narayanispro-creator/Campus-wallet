# Campus Wallet: Student Expense Tracking System

**Project type:** BTech Computer Science mini project  
**Technology:** Python, Flask, SQLite, HTML5, CSS3, JavaScript  
**Student / Roll number / Institution / Guide:** Fill in before submission

## 1. Abstract

Campus Wallet helps students record daily expenses and understand monthly spending. It replaces scattered notes with structured entries containing an amount, date, category and optional notes. A dashboard displays totals, budget utilisation, daily spending and category distribution. The implementation combines a Flask JSON API with a responsive browser interface and a local SQLite database. It is intended for demonstrating CRUD operations, client–server communication, relational storage, validation and data visualisation in an understandable, runnable project.

## 2. Problem statement and objectives

Students make frequent small purchases across food, travel, books and entertainment. Without a consistent record, it is difficult to identify spending patterns or compare expenses with an allowance.

The objectives are to provide simple entry and correction of expenses; retain data between sessions; organise purchases by category and month; compare actual spending against a monthly budget; and present understandable charts. A further learning objective is to show the complete path from an HTML form through a backend API to a database and back to the screen.

## 3. Scope and requirements

The application serves one student on one local computer, with INR as the fixed currency. It runs on Python 3.10+ and a modern browser. Flask is the only direct third-party Python dependency; SQLite, unittest, Decimal and calendar are standard-library modules. No Node.js, frontend build tools, database server, paid API or chart CDN is required.

Functional requirements include creating, reading, updating and deleting expenses; seven predefined categories; month selection; description/notes search; category filtering; independent monthly budgets; daily and category charts; and optional fictional demonstration records.

Nonfunctional requirements include a responsive layout, clear validation errors, exact currency storage, persistence, safe parameterised SQL, accessible form labels, keyboard-operable controls and tests isolated from real records.

## 4. Architecture

```text
Student
   │ browser actions
   ▼
HTML + CSS + JavaScript
   │ same-origin fetch / JSON; CSRF header on writes
   ▼
Flask routes → validation → parameterised SQL
   │
   ▼
SQLite database on local disk
   │ rows and monthly budget
   ▼
Flask aggregation → JSON response → DOM and CSS charts
```

The application factory `create_app()` creates the Flask app, loads configuration and ensures the schema exists. A database connection is opened only when a request needs it, stored in Flask's request context, and closed after that context ends. Successful writes are committed before returning success. Tests can supply a separate database path through configuration.

The root route renders the Jinja template and issues a session-bound CSRF token. JavaScript retrieves the monthly dashboard, fills summary cards and creates chart elements. Forms submit JSON and refresh the selected month after a successful write. User text is placed into the DOM using `textContent`, avoiding interpretation as executable HTML.

## 5. Database design

### Expense entity (`expenses`)

| Field | SQLite type | Purpose / constraints |
|---|---|---|
| id | INTEGER | Autoincrement primary key |
| title | TEXT | Required description; 1–100 trimmed characters |
| amount | INTEGER | Positive amount in paise |
| category | TEXT | One of seven categories, validated by Flask |
| spent_on | TEXT | Valid calendar date in ISO `YYYY-MM-DD` format |
| notes | TEXT | Optional text, default empty; maximum 500 characters via API |

An index on `spent_on` supports selection by date range. The database constrains positive amounts and title length. Category, date validity, maximum amounts and notes length are enforced in application code, so direct database edits can bypass those application rules.

### Budget entity (`budgets`)

| Field | SQLite type | Purpose / constraints |
|---|---|---|
| month | TEXT | Primary key in `YYYY-MM` format, validated by Flask |
| amount | INTEGER | Positive monthly limit in paise |

There is no foreign key between the entities: a month may have expenses without a budget, or a budget without expenses. The dashboard associates them by month. Budget updates use SQLite's conflict-update clause, preserving exactly one budget row for each month.

### Why integer paise?

Binary floating-point cannot represent many decimal fractions exactly. A value such as ₹120.50 is validated with Python's `Decimal` and stored as `12050`. Monthly sums therefore remain exact. The UI divides paise by 100 only for formatting. The API permits ₹0.01 through ₹1,00,00,000, with no more than two decimal places.

## 6. API design

| Method | Endpoint | Behaviour |
|---|---|---|
| GET | `/` | Dashboard HTML and CSRF session |
| GET | `/api/dashboard?month=2026-09` | Expenses, total, daily array, category totals and budget |
| POST | `/api/expenses` | Validate and create expense; return ID with 201 |
| PUT | `/api/expenses/<id>` | Validate and update existing expense |
| DELETE | `/api/expenses/<id>` | Delete existing expense |
| PUT | `/api/budget` | Create or replace budget for a month |

An expense write accepts `title`, `amount` in rupees, `category`, `spent_on` and optional `notes`. A budget write accepts `month` and `amount` in rupees. Dashboard amounts are returned in **paise**, documented here to avoid unit confusion. All writes require the `X-CSRF-Token` header from the page's meta tag and the matching session cookie. Invalid values return 400, invalid CSRF returns 403 and missing expense IDs return 404. Oversized requests are limited to 16 KiB.

## 7. Algorithms and interface behaviour

For the selected month, Python's calendar module determines the last day. SQL retrieves records between the first and last ISO dates, newest first. A single pass sums amounts into an array indexed by day and a dictionary indexed by category. The total is the sum of the daily array. This naturally handles leap years and December–January boundaries.

Budget remaining equals budget minus total. When this becomes negative, the UI labels the absolute difference “Over budget” and highlights it in red. The progress bar is capped at 100%; the percentage text can exceed 100%, preserving the true ratio.

Daily bar height is each day's amount divided by the maximum daily amount. Empty days have a small visual baseline and a ₹0 label. Exact values are available through labelled buttons and click feedback. Category bar width is the category's share of the monthly total. Categories are sorted by spending.

Search and category filters operate on the already loaded month's rows. Cards and charts continue to show the entire month; a separate footer describes the filtered list subtotal. Rendering a month is linear in that month's record count, apart from SQL sorting and the fixed seven-category sort. A request-version counter avoids an older successful month response overwriting a newer selection.

## 8. Features implemented

- Expense creation, editing, confirmed deletion, dates and notes
- Seven predefined student-friendly categories
- Monthly spending summaries and independent budget updates
- Daily spending and category charts without external dependencies
- Month picker, live search and category filtering
- Empty states, no-match states and visible API errors
- Responsive sidebar, stacked mobile cards and horizontally scrollable transaction table
- Session-based CSRF protection, parameterised SQL and safe DOM text rendering
- Repeat-safe optional demo command and automated tests

## 9. Testing and validation

Run `python -m unittest discover -s tests -v` from the project directory. All **12 automated tests passed** during delivery verification. Each test creates a temporary database.

| Test area | Expected result |
|---|---|
| Empty month | Zero spending, correct day count, no budget |
| Expense CRUD | Create/edit/delete reflected in persisted rows and aggregates |
| Currency | ₹0.10 plus ₹0.20 totals exactly 30 paise |
| Invalid input | Negative, zero, nonfinite, excessive precision, invalid dates and long text rejected |
| Month boundaries | Leap day and December/January kept in correct months |
| Budgets | Updates replace same month and do not alter another month |
| Persistence | A new app instance reads existing records |
| CSRF | Missing and incorrect tokens rejected |
| Missing IDs | Edit/delete return 404 |
| SQL/markup strings | Stored as data without dropping tables |
| Demo seeding | First run succeeds; second refuses without overwriting |
| Malformed JSON shape | Arrays rejected with a validation response |

Browser verification checks the visible interface separately from these backend tests. It confirms that the page loads with demo values, chart labels are present, and creating an expense updates the transaction list and totals. Detailed delivery verification notes are recorded in `VERIFICATION.md`.

## 10. Limitations

This is a local educational system, not a production financial platform. It has no authentication or separation between users, no encryption at rest, no cloud backup and no concurrent-user design. The development server must remain local. SQLite may lock under heavy simultaneous writes. The full month's records are returned at once, without pagination. Categories are predefined; changing them requires coordinated code and data updates. Budgets cannot currently be removed, though their amounts can be changed. There is no undo for deletion, recurring expense scheduling, receipt attachment, export or multi-currency support. Future-dated entries are permitted and counted. Automated tests cover API behaviour, while broad cross-browser and assistive-technology testing remains future work.

## 11. Future scope

Useful extensions include CSV export and import, soft deletion, recurring expenses, category management, category-level budgets, user accounts, PostgreSQL for multi-user deployment, encrypted backups and receipt uploads. Authentication and ownership checks should be added before any public deployment. Additional UI tests could cover keyboard navigation, errors, filtering, mobile layouts and full CRUD in several browsers.

## 12. Presentation and viva guide

Suggested five-minute demonstration:

1. Explain the student budgeting problem and the Flask–SQLite architecture.
2. Seed a clean database and show ₹8,959 spending against ₹15,000.
3. Add an expense and point out the immediate changes to the table and charts.
4. Edit its amount and category, then search for its description.
5. Set a smaller budget to demonstrate the over-budget state.
6. Change months to show that both expenses and budgets are month-specific.
7. Delete the demonstration entry and explain the confirmation step.
8. Run the automated tests and describe integer paise storage.

**Why Flask?** Its small routing and request-handling model keeps the code easy to explain.  
**Why SQLite?** It provides persistent relational storage without installing a database service.  
**What is CRUD?** Create, Read, Update and Delete: the four core operations supported for expenses.  
**Why validate twice?** Browser validation offers immediate feedback; backend validation protects the database even when clients bypass the form.  
**How is SQL injection avoided?** SQL values use placeholders and parameter binding rather than string concatenation.  
**What does CSRF protection do?** It rejects write requests without a token associated with the current browser session.  
**Is CSRF the same as login?** No. This app has no user identity; CSRF only protects the session's write requests.  
**Why not floating-point amounts?** Integer paise preserve exact totals.  
**How are charts built?** JavaScript creates CSS bars from aggregated JSON; there is no external chart library.  
**What would change for production?** Add authentication, record ownership, deployment configuration, HTTPS, operational backups, monitoring and appropriate database scaling.

## 13. Conclusion

Campus Wallet demonstrates a complete local web application with persistent expense management, budgeting and visual summaries. Its compact separation between Python routes, a relational database and browser rendering makes it suitable for a student to study, modify and present.
