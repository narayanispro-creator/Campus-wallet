# Delivery verification

Verified on 20 September 2026 with Python 3.14.6 and Flask 3.1.3 on macOS.

## Automated integration tests

Command: `python3 -m unittest discover -s tests -v`

Result: **12 tests passed**. Tests use temporary SQLite databases. Coverage includes CRUD, aggregation, precise currency, validation, month boundaries, leap years, budget upsert/isolation, persistence across app instances, CSRF, missing IDs, injection-like input, demo seeding and malformed payloads.

## Browser checks

The `agent-browser` executable was unavailable, so the Codex in-app browser was used as a fallback against a loopback Flask server. No external deployment was created.

- Dashboard loaded with 10 demo expenses totalling ₹8,959 and a ₹15,000 budget.
- Added “Browser test lunch” for ₹99.50: total became ₹9,058.50 and the daily/category charts reflected the entry.
- Edited that entry to ₹125.25: total became ₹9,084.25.
- Set budget to ₹8,000: screen showed **OVER BUDGET ₹1,084.25** and 114% utilisation.
- Searching for the test description returned **1 of 11 expenses · ₹125.25 shown**.
- Desktop screenshot at 1440px showed the sidebar, summary cards, both charts and transaction section. Page scroll width matched viewport width.
- A narrower 766px layout rendered without page overflow. A requested 390px viewport was not reflected by the browser at that check, so phone-width verification is not claimed. CSS includes a dedicated layout below 600px, but this needs a real-phone check.
- Browser error log returned an empty list during the checked flows.

Deletion, missing records, month isolation and validation were tested through Flask's test client. Deletion was not separately exercised in the browser. Cross-browser compatibility, comprehensive screen-reader testing and load testing were not performed.

The distributed ZIP excludes runtime databases, caches and virtual environments. Demo data is optional via the documented CLI command.
