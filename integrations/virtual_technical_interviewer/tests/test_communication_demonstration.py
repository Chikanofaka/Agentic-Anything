import copy
import unittest
from tia_runtime.communication_demonstration import recorded_communication


def plan(text='SELECT person_name FROM Queue ORDER BY turn DESC LIMIT 1;', kind='implement'):
    return {'continuity_policy': 'tia-continuity/v3', 'status': 'COMPLETE', 'results': [
        {'outcome': 'SUBMITTED_UNVERIFIED', 'session': {'events': [
            {'id': 'i1', 'actor': 'interviewer', 'kind': 'reply', 'payload': {'text': 'Explain your plan.'}},
            {'id': 'c1', 'actor': 'candidate', 'kind': kind, 'payload': {'text': text}},
        ]}}]}


class CommunicationDemonstrationTests(unittest.TestCase):
    def test_code_only_is_zero_demonstration_across_six_dimensions_not_ability(self):
        p = plan(); before = copy.deepcopy(p)
        result = recorded_communication(p, 0)
        self.assertEqual((result['points'], result['maximum_points']), (0, 40))
        self.assertEqual(len(result['dimensions']), 6)
        self.assertEqual(sum(d['points'] for d in result['dimensions']), 0)
        self.assertEqual(result['formal_grade'], 'NOT_SCORED')
        self.assertEqual(result['recording_health'], 'NOT_ATTESTED')
        self.assertEqual(p, before)

    def test_mislabeled_code_not_communication(self):
        self.assertEqual(recorded_communication(plan(kind='clarify'), 0)['points'], 0)

    def test_pure_help_request_does_not_award_communication_or_mentality_bonus(self):
        for text in ('Help me please', 'Can you help me?', '请帮我', 'Give me a hint.', 'Help, please.'):
            with self.subTest(text=text):
                self.assertEqual(recorded_communication(plan(text, 'help'), 0)['points'], 0)

    def test_noncanonical_help_stays_reviewable(self):
        for text in ('I could use some help', 'Help me choose between grouping and a window function',
                     'Can you help me check whether the denominator includes repeat customers?'):
            with self.subTest(text=text):
                result = recorded_communication(plan(text, 'help'), 0)
                self.assertEqual(result['status'], 'SEMANTIC_REVIEW_REQUIRED')
                self.assertIsNone(result['points'])

    def test_select_with_prose_cannot_zero_a_recorded_plan(self):
        for text in ('SELECT is how I would choose the relevant rows and then join on customer_id.',
                     'WITH a ranked CTE I can order each customer’s rows by date, then keep row one.',
                     'SELECT the first order for each customer',
                     'WITH the earliest dates established, the next step is filtering.',
                     'SELECT customer_id FROM Orders\nThis keeps the customer identity for grouping',
                     'SELECT 1; That is a small example before the real query.',
                     '```sql\nSELECT is how the rows are retrieved\n```'):
            for kind in ('plan', 'clarify', 'implement'):
                with self.subTest(text=text, kind=kind):
                    result = recorded_communication(plan(text, kind), 0)
                    self.assertEqual(result['status'], 'SEMANTIC_REVIEW_REQUIRED')
                    self.assertIsNone(result['points'])

    def test_nested_window_and_chained_cte_submissions_remain_code_only(self):
        queries = (
            'SELECT person_name FROM (SELECT person_name, turn, SUM(weight) OVER (ORDER BY turn) AS total '
            'FROM Queue) q WHERE total <= 1000 ORDER BY turn DESC LIMIT 1;',
            'SELECT person_name FROM (SELECT person_name, turn, SUM(weight) OVER '
            '(ORDER BY turn ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS total '
            'FROM Queue) q WHERE total <= 1000 ORDER BY turn DESC LIMIT 1;',
            'WITH a AS (SELECT customer_id, MIN(order_date) AS first_date FROM Delivery GROUP BY customer_id), '
            'b AS (SELECT d.customer_id, CASE WHEN d.order_date=d.customer_pref_delivery_date '
            'THEN 1 ELSE 0 END AS immediate FROM Delivery d JOIN a '
            'ON d.customer_id=a.customer_id AND d.order_date=a.first_date) '
            'SELECT ROUND(100.0 * SUM(immediate) / COUNT(*), 2) AS immediate_percentage FROM b;',
            "SELECT TO_CHAR(trans_date, 'YYYY-MM') AS month, country, COUNT(*) AS trans_count, "
            "SUM(CASE WHEN state='approved' THEN 1 ELSE 0 END) AS approved_count, "
            'SUM(amount) AS trans_total_amount, '
            "SUM(CASE WHEN state='approved' THEN amount ELSE 0 END) AS approved_total_amount "
            "FROM Transactions GROUP BY TO_CHAR(trans_date, 'YYYY-MM'), country;",
            'WITH ranked AS (SELECT *, ROW_NUMBER() OVER (PARTITION BY customer_id '
            'ORDER BY order_date, order_id) AS rn FROM Orders WHERE order_date IS NOT NULL) '
            'SELECT order_id, customer_id, order_date FROM ranked WHERE rn = 1;')
        for query in queries:
            with self.subTest(query=query):
                result = recorded_communication(plan(query), 0)
                self.assertEqual(result['status'], 'NO_RECORDED_DEMONSTRATION')
                self.assertEqual(result['points'], 0)

    def test_uncertain_or_unrecognized_sql_requires_review_not_execution(self):
        for text in ('SELECT', 'WITH a AS (SELECT 1)', 'SELECT 1; SELECT 2;',
                     'SELECT 1; ;', 'SELECT (1', 'SELECT * FROM t QUALIFY row_number() OVER ()=1',
                     'SELECT /* this is why I group */ customer_id FROM Orders',
                     'SELECT ' + '(' * 2000 + '1' + ')' * 2000):
            with self.subTest(text=text[:80]):
                self.assertIsNone(recorded_communication(plan(text), 0)['points'])

    def test_reasoned_help_or_plan_remains_reviewable_regardless_of_kind(self):
        for text in ('My plan is to group first, then join.', 'I am stuck on cardinality because duplicates change the denominator.',
                     '我先解释计划，然后验证边界条件。', '-- Explain the tie break\nSELECT 1;',
                     'SELECT 1;\nMy plan is to test it.', '```sql\nSELECT 1;\n```\nI will test it.'):
            self.assertEqual(recorded_communication(plan(text), 0)['status'], 'SEMANTIC_REVIEW_REQUIRED')

    def test_fenced_sql_only_zero(self):
        self.assertEqual(recorded_communication(plan('```sql\nSELECT 1;\n```'), 0)['points'], 0)

    def test_missing_malformed_or_interrupted_record_is_not_zero(self):
        for events in (None, [], [None], [{'actor': 'candidate', 'id': 'a', 'payload': {}}]):
            p = plan(); p['results'][0]['session']['events'] = events
            self.assertIsNone(recorded_communication(p, 0)['points'])
        p = plan(); p['results'][0]['session']['events'].append(
            {'actor': 'native', 'kind': 'transcription_failed'})
        self.assertEqual(recorded_communication(p, 0)['status'], 'CAPTURE_INCOMPLETE')
        self.assertIsNone(recorded_communication(p, 0)['points'])

    def test_skipped_timeout_active_legacy_not_defaulted(self):
        for outcome in ('SKIPPED', 'NOT_REACHED', 'TIMED_OUT'):
            p = plan(); p['results'][0]['outcome'] = outcome
            self.assertIsNone(recorded_communication(p, 0)['points'])
        for key,value in (('status','ACTIVE'), ('continuity_policy','tia-continuity/v2')):
            p = plan(); p[key] = value
            self.assertIsNone(recorded_communication(p, 0)['points'])

    def test_hash_binds_original_question_record(self):
        a = recorded_communication(plan('SELECT 1;'), 0)
        b = recorded_communication(plan('SELECT 2;'), 0)
        self.assertNotEqual(a['record_sha256'], b['record_sha256'])
        self.assertNotEqual(a['sha256'], b['sha256'])


if __name__ == '__main__':
    unittest.main()
