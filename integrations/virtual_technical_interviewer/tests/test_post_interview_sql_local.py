"""Opt-in actual temporary PostgreSQL comparisons; no provider or user data."""
import os
import unittest
from tia_runtime.post_interview_sql import fixtures, canonical
from tia_runtime.sql_accuracy import grade_fixture
from tia_runtime.grading_binding import find_approved_pg_config

# These are developer-authored test inputs, not private runtime reference answers.
QUERIES = {
    'delivery_first_orders': (
        'WITH firsts AS (SELECT customer_id, min(order_date) AS d FROM Delivery GROUP BY customer_id) '
        'SELECT round(100.0 * sum(CASE WHEN d.order_date = d.customer_pref_delivery_date THEN 1 ELSE 0 END) / count(*), 2) AS immediate_percentage '
        'FROM Delivery d JOIN firsts f ON d.customer_id=f.customer_id AND d.order_date=f.d',
        'SELECT 99.99 AS immediate_percentage'),
    'monthly_transactions': (
        "SELECT to_char(trans_date, 'YYYY-MM') AS month, country, count(*) AS trans_count, "
        "sum(CASE WHEN state='approved' THEN 1 ELSE 0 END) AS approved_count, sum(amount) AS trans_total_amount, "
        "sum(CASE WHEN state='approved' THEN amount ELSE 0 END) AS approved_total_amount FROM Transactions GROUP BY to_char(trans_date, 'YYYY-MM'), country",
        "SELECT to_char(trans_date, 'YYYY-MM') AS month, country, count(*) AS trans_count, 0 AS approved_count, sum(amount) AS trans_total_amount, 0 AS approved_total_amount FROM Transactions GROUP BY to_char(trans_date, 'YYYY-MM'), country"),
    'bus_last_person': (
        'WITH ordered AS (SELECT person_name, turn, sum(weight) OVER (ORDER BY turn) AS total FROM Queue) SELECT person_name FROM ordered WHERE total <= 1000 ORDER BY turn DESC LIMIT 1',
        "SELECT 'No such person' AS person_name")}

@unittest.skipUnless(os.environ.get('TIA_RUN_LOCAL_POSTGRES_TESTS') == '1', 'explicit local PostgreSQL test opt-in required')
class ActualPostgreSQLCaseTests(unittest.TestCase):
    def test_all_three_suites_detect_correct_and_wrong_sql(self):
        config=find_approved_pg_config()
        for suite,queries in QUERIES.items():
            for case in fixtures(suite,'a'*64):
                for expected,query in zip(('PASSED','FAILED'),queries):
                    with self.subTest(suite=suite,case=case['label'],expected=expected):
                        receipt=grade_fixture(canonical(case['fixture']).encode(),query,case['fixture_sha256'],pg_config=config,private_query=True)
                        self.assertEqual(receipt['result']['status'],expected)
