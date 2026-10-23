"""E4-B1 security and accuracy contracts: read-only language evidence."""
import copy
import hashlib
import unittest

from tia_runtime.submission_language import (
    classify_source, review_session, project_language_reviews,
)


def session(text, kind='implement', event_id='rehearsal-01-q1:3'):
    return {'events': [{'actor': 'candidate', 'kind': kind, 'id': event_id,
                        'payload': {'text': text}},
                       {'actor': 'interviewer', 'kind': 'reply',
                        'payload': {'text': 'That query is correct!'}}]}


class E4B1LanguageIntegrityTests(unittest.TestCase):
    def test_sql_with_leading_comment(self):
        self.assertEqual(classify_source('-- PostgreSQL query\nwith a as (select 1) select * from a'),
                         'SQL_LIKE_UNVERIFIED')

    def test_sql_select(self):
        self.assertEqual(classify_source('  SELECT * FROM Queue'), 'SQL_LIKE_UNVERIFIED')

    def test_python_pandas(self):
        self.assertEqual(classify_source('import pandas as pd\ndef solve(df):\n    return df'),
                         'PYTHON_LIKE_UNVERIFIED')

    def test_python_def(self):
        self.assertEqual(classify_source('def monthly_transactions(transactions: pd.DataFrame):\n    pass'),
                         'PYTHON_LIKE_UNVERIFIED')

    def test_unknown_not_confident(self):
        self.assertEqual(classify_source('I think a groupby would help'), 'UNKNOWN')
        self.assertEqual(classify_source(''), 'UNKNOWN')

    def test_sql_pandas_mismatch_is_unscored(self):
        value = 'with a as (select 1) select * from a'
        r = review_session('PANDAS', session(value), 0)
        self.assertEqual(r['status'], 'LANGUAGE_MISMATCH_REVIEW_REQUIRED')
        self.assertEqual(r['candidate_text_sha256'], hashlib.sha256(value.encode()).hexdigest())
        self.assertEqual(r['candidate_event_id'], 'rehearsal-01-q1:3')
        self.assertNotIn('text', r)
        self.assertFalse(r['correctness_assessed'])
        self.assertFalse(r['code_execution_performed_by_review'])

    def test_postgres_sql_consistent_not_correctness_proof(self):
        r = review_session('POSTGRESQL', session('select 1'), 0)
        self.assertEqual(r['status'], 'CONSISTENT_BY_HEURISTIC_NOT_EXECUTED')
        self.assertFalse(r['correctness_assessed'])

    def test_postgres_python_mismatch(self):
        r = review_session('POSTGRESQL', session('def solve(df): return df'), 0)
        self.assertEqual(r['status'], 'LANGUAGE_MISMATCH_REVIEW_REQUIRED')

    def test_no_submission_stays_unknown_not_zero(self):
        r = review_session('PANDAS', session('any question?', kind='clarify'), 0)
        self.assertEqual(r['status'], 'NO_SUBMISSION')

    def test_last_implementation_not_last_interviewer(self):
        ss = session('select 1')
        ss['events'].append({'actor': 'candidate', 'kind': 'clarify',
                             'payload': {'text': 'Is that okay?'}})
        r = review_session('PANDAS', ss, 0)
        self.assertEqual(r['status'], 'LANGUAGE_MISMATCH_REVIEW_REQUIRED')

    def test_frozen_3_question_projection_non_mutating(self):
        plan = {'status': 'COMPLETE', 'questions': [
                    {'environment': 'PANDAS'}, {'environment': 'PANDAS'},
                    {'environment': 'PANDAS'}],
                'results': [{'session': session('with a as (select 1) select * from a')},
                            {'session': session('select 2')},
                            {'session': session('select 3')}]}
        old = copy.deepcopy(plan)
        r = project_language_reviews(plan)
        self.assertEqual(len(r['completed']), 3)
        self.assertEqual([x['status'] for x in r['completed']],
                         ['LANGUAGE_MISMATCH_REVIEW_REQUIRED'] * 3)
        self.assertEqual(plan, old)
        self.assertFalse(r['correctness_assessed'])

    def test_active_projection(self):
        plan = {'status': 'ACTIVE', 'current_index': 1,
                'questions': [{'environment': 'POSTGRESQL'}, {'environment': 'PANDAS'}],
                'results': [{'session': session('select 1')}]}
        r = project_language_reviews(plan, session('select 2'))
        self.assertEqual(r['active']['question_index'], 1)
        self.assertEqual(r['active']['status'], 'LANGUAGE_MISMATCH_REVIEW_REQUIRED')
        self.assertEqual(len(r['completed']), 1)

    def test_other_actor_cannot_spoof_candidate(self):
        r = review_session('PANDAS', {'events': [{'actor': 'interviewer', 'kind': 'implement',
                   'id': 'bad', 'payload': {'text': 'select 1'}}]}, 0)
        self.assertEqual(r['status'], 'NO_SUBMISSION')


if __name__ == '__main__':
    unittest.main()
