"""Campus Wallet: a small, single-user Flask/SQLite expense tracker."""
import calendar
import os
import re
import secrets
import sqlite3
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

import click
from flask import Flask, abort, g, jsonify, render_template, request, session

CATEGORIES = ['Food & drinks', 'Transport', 'Study', 'Shopping', 'Rent & bills', 'Entertainment', 'Other']


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(SECRET_KEY=os.environ.get('SECRET_KEY') or secrets.token_hex(32),
                            DATABASE=os.environ.get('DATABASE_PATH') or str(Path(app.instance_path) / 'wallet.sqlite3'),
                            MAX_CONTENT_LENGTH=16 * 1024,
                            SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Lax')
    if test_config:
        app.config.update(test_config)
    Path(app.config['DATABASE']).parent.mkdir(parents=True, exist_ok=True)

    def db():
        if 'db' not in g:
            g.db = sqlite3.connect(app.config['DATABASE'])
            g.db.row_factory = sqlite3.Row
        return g.db

    @app.teardown_appcontext
    def close_db(error=None):
        connection = g.pop('db', None)
        if connection:
            connection.close()

    with app.app_context():
        db().executescript('''
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL CHECK(length(title) BETWEEN 1 AND 100),
                amount INTEGER NOT NULL CHECK(amount > 0),
                category TEXT NOT NULL,
                spent_on TEXT NOT NULL,
                notes TEXT NOT NULL DEFAULT ''
            );
            CREATE INDEX IF NOT EXISTS expenses_date ON expenses(spent_on);
            CREATE TABLE IF NOT EXISTS budgets (
                month TEXT PRIMARY KEY,
                amount INTEGER NOT NULL CHECK(amount > 0)
            );
        ''')
        db().commit()

    def month_value(value):
        if not isinstance(value, str) or not re.fullmatch(r'\d{4}-\d{2}', value):
            raise ValueError('Choose a valid month.')
        date.fromisoformat(value + '-01')
        return value

    def money(value):
        try:
            result = Decimal(str(value))
            if not result.is_finite() or result <= 0 or result > 10000000 or result.as_tuple().exponent < -2:
                raise ValueError()
            return int(result * 100)
        except (InvalidOperation, ValueError):
            raise ValueError('Enter an amount from ₹0.01 to ₹1,00,00,000 with at most two decimal places.')

    def payload():
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            raise ValueError('Send a JSON object.')
        return data

    def expense_values(data):
        title, notes = data.get('title', ''), data.get('notes', '')
        if not isinstance(title, str) or not 1 <= len(title.strip()) <= 100:
            raise ValueError('Description must contain 1–100 characters.')
        if not isinstance(notes, str) or len(notes) > 500:
            raise ValueError('Notes must be 500 characters or fewer.')
        category = data.get('category')
        if category not in CATEGORIES:
            raise ValueError('Choose a valid category.')
        spent_on = data.get('spent_on', '')
        if not isinstance(spent_on, str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}', spent_on):
            raise ValueError('Choose a valid expense date.')
        date.fromisoformat(spent_on)
        return title.strip(), money(data.get('amount')), category, spent_on, notes.strip()

    @app.before_request
    def csrf_check():
        if request.method in {'POST', 'PUT', 'DELETE'}:
            token = request.headers.get('X-CSRF-Token', '')
            if not token or not secrets.compare_digest(token, session.get('csrf_token', '')):
                abort(403, description='Session expired. Refresh the page and try again.')

    @app.errorhandler(ValueError)
    def validation_error(error):
        return jsonify(error=str(error)), 400

    @app.errorhandler(403)
    @app.errorhandler(404)
    @app.errorhandler(413)
    def http_error(error):
        return jsonify(error=error.description), error.code

    @app.get('/')
    def index():
        session.setdefault('csrf_token', secrets.token_hex(32))
        return render_template('index.html', categories=CATEGORIES, token=session['csrf_token'],
                               today=date.today().isoformat())

    @app.get('/api/dashboard')
    def dashboard():
        month = month_value(request.args.get('month', date.today().strftime('%Y-%m')))
        # ISO date strings sort chronologically, including December and leap years.
        year, number = map(int, month.split('-'))
        days = calendar.monthrange(year, number)[1]
        rows = [dict(row) for row in db().execute(
            'SELECT * FROM expenses WHERE spent_on BETWEEN ? AND ? ORDER BY spent_on DESC, id DESC',
            (month + '-01', f'{month}-{days:02d}'))]
        category_totals = {category: 0 for category in CATEGORIES}
        daily = [0] * days
        for row in rows:
            category_totals[row['category']] += row['amount']
            daily[int(row['spent_on'][-2:]) - 1] += row['amount']
        budget = db().execute('SELECT amount FROM budgets WHERE month = ?', (month,)).fetchone()
        return jsonify(month=month, expenses=rows, total=sum(daily), daily=daily,
                       categories=category_totals, budget=budget['amount'] if budget else None)

    @app.post('/api/expenses')
    def add_expense():
        values = expense_values(payload())
        cursor = db().execute('INSERT INTO expenses(title,amount,category,spent_on,notes) VALUES(?,?,?,?,?)', values)
        db().commit()
        return jsonify(id=cursor.lastrowid), 201

    @app.put('/api/expenses/<int:expense_id>')
    def edit_expense(expense_id):
        values = expense_values(payload())
        cursor = db().execute('UPDATE expenses SET title=?,amount=?,category=?,spent_on=?,notes=? WHERE id=?',
                              (*values, expense_id))
        if not cursor.rowcount:
            abort(404, description='Expense not found.')
        db().commit()
        return jsonify(ok=True)

    @app.delete('/api/expenses/<int:expense_id>')
    def delete_expense(expense_id):
        cursor = db().execute('DELETE FROM expenses WHERE id=?', (expense_id,))
        if not cursor.rowcount:
            abort(404, description='Expense not found.')
        db().commit()
        return jsonify(ok=True)

    @app.put('/api/budget')
    def set_budget():
        data = payload()
        month, amount = month_value(data.get('month')), money(data.get('amount'))
        db().execute('INSERT INTO budgets(month, amount) VALUES(?,?) ON CONFLICT(month) DO UPDATE SET amount=excluded.amount',
                     (month, amount))
        db().commit()
        return jsonify(ok=True)

    @app.cli.command('seed-demo')
    def seed_demo():
        """Add optional fictional data only when the database is empty."""
        if db().execute('SELECT count(*) FROM expenses').fetchone()[0] or db().execute('SELECT count(*) FROM budgets').fetchone()[0]:
            raise click.ClickException('Database is not empty; demo data was not added.')
        month = date.today().strftime('%Y-%m')
        samples = [('Monthly room rent', 550000, 'Rent & bills', 1), ('Campus canteen', 12000, 'Food & drinks', 3),
                   ('Bus pass', 65000, 'Transport', 4), ('Python reference book', 48000, 'Study', 6),
                   ('Coffee with friends', 18000, 'Food & drinks', 8), ('Movie night', 32000, 'Entertainment', 10),
                   ('Groceries', 74000, 'Food & drinks', 12), ('Notebook & stationery', 22000, 'Study', 14),
                   ('New T-shirt', 59900, 'Shopping', 16), ('Lunch at the canteen', 15000, 'Food & drinks', 18)]
        db().executemany('INSERT INTO expenses(title,amount,category,spent_on,notes) VALUES(?,?,?,?,?)',
                        [(t,a,c,f'{month}-{d:02d}','Fictional demo expense') for t,a,c,d in samples])
        db().execute('INSERT INTO budgets VALUES(?,?)', (month, 1500000))
        db().commit()
        click.echo(f'Added 10 fictional expenses and a ₹15,000 budget for {month}.')

    return app


if __name__ == '__main__':
    create_app().run(host='127.0.0.1', port=5000, debug=False)
