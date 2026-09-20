import re
import tempfile
import unittest
from pathlib import Path
from app import create_app

class WalletTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.config = {'TESTING': True, 'DATABASE': str(Path(self.temp.name) / 'test.sqlite3'), 'SECRET_KEY': 'test-only'}
        self.app = create_app(self.config)
        self.client = self.app.test_client()
        page = self.client.get('/')
        token = re.search(rb'name="csrf-token" content="([^"]+)"', page.data).group(1).decode()
        self.headers = {'X-CSRF-Token': token}
    def tearDown(self):
        self.temp.cleanup()
    def send(self, path, method='POST', data=None):
        return self.client.open(path, method=method, json=data, headers=self.headers)
    def expense(self, **updates):
        value = {'title': 'Lunch', 'amount': '120.50', 'category': 'Food & drinks', 'spent_on': '2026-09-20', 'notes': 'Campus'}
        value.update(updates)
        return value
    def dashboard(self, month='2026-09'):
        response = self.client.get('/api/dashboard', query_string={'month': month})
        self.assertEqual(response.status_code, 200)
        return response.json
    def test_empty_dashboard(self):
        data = self.dashboard()
        self.assertEqual(data['total'], 0)
        self.assertIsNone(data['budget'])
        self.assertEqual(len(data['daily']), 30)
    def test_crud_and_aggregation(self):
        response = self.send('/api/expenses', data=self.expense())
        self.assertEqual(response.status_code, 201)
        expense_id = response.json['id']
        data = self.dashboard()
        self.assertEqual(data['total'], 12050)
        self.assertEqual(data['daily'][19], 12050)
        self.assertEqual(data['categories']['Food & drinks'], 12050)
        self.assertEqual(self.send(f'/api/expenses/{expense_id}', 'PUT', self.expense(amount='200', category='Study')).status_code, 200)
        self.assertEqual(self.dashboard()['total'], 20000)
        self.assertEqual(self.dashboard()['categories']['Study'], 20000)
        self.assertEqual(self.send(f'/api/expenses/{expense_id}', 'DELETE').status_code, 200)
        self.assertEqual(self.dashboard()['expenses'], [])
    def test_exact_currency(self):
        for amount in ['0.10', '0.20']:
            self.assertEqual(self.send('/api/expenses', data=self.expense(amount=amount)).status_code, 201)
        self.assertEqual(self.dashboard()['total'], 30)
    def test_invalid_inputs_do_not_write(self):
        changes = [{'amount': x} for x in ['0', '-1', 'NaN', 'Infinity', '1.001', '10000001', 'abc', None]]
        changes += [{'title': ''}, {'title': 'a'*101}, {'title': []}, {'category': 'Invalid'}, {'spent_on': '2026-02-30'}, {'spent_on': '2026-9-1'}, {'notes': 'a'*501}]
        for change in changes:
            with self.subTest(change=change):
                self.assertEqual(self.send('/api/expenses', data=self.expense(**change)).status_code, 400)
        self.assertEqual(self.dashboard()['total'], 0)
    def test_month_boundaries_and_leap_year(self):
        for day in ['2024-02-29', '2024-03-01', '2026-12-31', '2027-01-01']:
            self.send('/api/expenses', data=self.expense(spent_on=day))
        self.assertEqual(len(self.dashboard('2024-02')['daily']), 29)
        for month in ['2024-02', '2024-03', '2026-12', '2027-01']:
            self.assertEqual(len(self.dashboard(month)['expenses']), 1)
        for month in ['bad', '2026-13', '0000-01']:
            self.assertEqual(self.client.get('/api/dashboard?month='+month).status_code, 400)
    def test_budget_upsert_and_isolation(self):
        for amount in ['100', '200.50']:
            self.assertEqual(self.send('/api/budget', 'PUT', {'month':'2026-09', 'amount':amount}).status_code, 200)
        self.assertEqual(self.dashboard()['budget'], 20050)
        self.assertIsNone(self.dashboard('2026-10')['budget'])
        self.assertEqual(self.send('/api/budget', 'PUT', {'month':'2026-09', 'amount':0}).status_code, 400)
    def test_persistence(self):
        self.send('/api/expenses', data=self.expense())
        fresh = create_app(self.config).test_client()
        self.assertEqual(fresh.get('/api/dashboard?month=2026-09').json['total'], 12050)
    def test_csrf(self):
        self.assertEqual(self.client.post('/api/expenses', json=self.expense()).status_code, 403)
        self.assertEqual(self.client.post('/api/expenses', json=self.expense(), headers={'X-CSRF-Token':'wrong'}).status_code, 403)
    def test_missing_records(self):
        self.assertEqual(self.send('/api/expenses/999', 'DELETE').status_code, 404)
        self.assertEqual(self.send('/api/expenses/999', 'PUT', self.expense()).status_code, 404)
    def test_sql_and_markup_are_data(self):
        title = "<script>alert(1)</script>'; DROP TABLE expenses; --"
        self.send('/api/expenses', data=self.expense(title=title))
        self.assertEqual(self.dashboard()['expenses'][0]['title'], title)
        self.assertEqual(self.send('/api/expenses', data=self.expense()).status_code, 201)
    def test_demo_seed_is_safe(self):
        runner = self.app.test_cli_runner()
        self.assertEqual(runner.invoke(args=['seed-demo']).exit_code, 0)
        self.assertNotEqual(runner.invoke(args=['seed-demo']).exit_code, 0)
    def test_malformed_payload(self):
        self.assertEqual(self.send('/api/expenses', data=['invalid']).status_code, 400)

if __name__ == '__main__':
    unittest.main()
