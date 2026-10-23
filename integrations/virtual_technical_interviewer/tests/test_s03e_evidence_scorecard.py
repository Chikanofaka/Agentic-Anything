"""E3-A: evidence-only scorecard, source binding, historical save compatibility.

All network/model and PostgreSQL backends in this file are mocked. Existing
Mac E25B tests separately prove the native PostgreSQL integration.
"""
import copy
import hashlib
import unittest
from unittest.mock import patch

from tia_runtime.evidence_scorecard import build_scorecard
from tia_runtime.app_host import TutorialHost
import test_s03e_app_grading as grading_tests
import test_s03e_rehearsal as rehearsal_tests


SQL = 'SELECT person_name FROM Queue'
QHASHES = ['a' * 64, 'b' * 64, 'c' * 64]


def event(event_id='candidate-1', kind='implement', text=SQL):
    return {'id': event_id, 'actor': 'candidate', 'kind': kind, 'payload': {'text': text}}


def score_record(index=0, *, verdict='PASSED', extra_events=(), skip=False):
    code = event()
    grade = {
        'source': 'EPHEMERAL_POSTGRESQL_LOCAL',
        'approval_kind': 'NATIVE_HUMAN_CONFIRMATION',
        'official_hidden_tests': False,
        'correctness': 'VERIFIED_LOCAL_FIXTURE',
        'candidate_event_id': code['id'],
        'candidate_sql_sha256': hashlib.sha256(SQL.encode()).hexdigest(),
        'fixture_sha256': 'e' * 64, 'question_sha256': QHASHES[index],
        'passed_fixtures': int(verdict == 'PASSED'), 'total_approved_fixtures': 1,
        'result': {'status': verdict, 'reason': 'PASS' if verdict == 'PASSED' else 'ROWS_MISMATCH'},
    }
    return {
        'index': index, 'outcome': 'SKIPPED' if skip else 'SUBMITTED_UNVERIFIED',
        'sql_accuracy': grade,
        'time_metrics': {'elapsed_seconds': 95.0, 'model_wait_seconds': 15.0},
        'session': {'events': [event('clarify-1', 'clarify', 'Why?'), code, *extra_events],
                    'receipt': {'sha256': 'f' * 64}},
    }


def plan(*records):
    return {
        'questions': [{'title': 'Q' + str(i + 1), 'content_sha256': QHASHES[i]} for i in range(3)],
        'results': list(records), 'status': 'ACTIVE' if len(records) < 3 else 'COMPLETE',
        'current_index': len(records),
        'timing': {'elapsed_seconds': 100., 'model_wait_seconds': 15., 'integrity': 'LOCAL_UNATTESTED'},
    }


class ScorecardUnitTests(unittest.TestCase):
    def test_empty_rehearsal_has_no_invented_zero_grade(self):
        card = build_scorecard(plan())
        self.assertEqual(card['status'], 'IN_PROGRESS')
        self.assertEqual(card['summary']['latest_sql_locally_verified_questions'], 0)
        self.assertEqual(card['questions'][0]['accuracy']['fixture_passed'], None)
        self.assertEqual(card['summary']['technical_capability'], 'NOT_SCORED')
        self.assertEqual(card['summary']['communication_competency'], 'NOT_SCORED')
        self.assertEqual(card['summary']['overall_grade'], 'NOT_SCORED')
        self.assertNotIn('pass_percentage', card['summary'])

    def test_one_approved_fixture_pass_is_not_an_overall_grade(self):
        card = build_scorecard(plan(score_record()))
        self.assertEqual(card['summary']['latest_sql_locally_verified_questions'], 1)
        self.assertEqual(card['summary']['latest_sql_passed_local_fixtures'], 1)
        self.assertEqual(card['summary']['questions_without_current_sql_verification'], 2)
        self.assertEqual(card['questions'][0]['accuracy']['status'], 'PASSED')
        self.assertEqual(card['questions'][0]['accuracy']['fixture_total'], 1)
        self.assertEqual(card['summary']['overall_grade'], 'NOT_SCORED')

    def test_failed_fixture_is_evidence_not_zero_competency(self):
        card = build_scorecard(plan(score_record(verdict='FAILED')))
        self.assertEqual(card['summary']['latest_sql_failed_local_fixtures'], 1)
        self.assertEqual(card['questions'][0]['accuracy']['status'], 'FAILED')
        self.assertEqual(card['summary']['technical_capability'], 'NOT_SCORED')

    def test_query_error_not_misclassified_as_failing_comparison(self):
        card = build_scorecard(plan(score_record(verdict='EXECUTION_ERROR')))
        self.assertEqual(card['summary']['latest_sql_execution_errors'], 1)
        self.assertEqual(card['summary']['latest_sql_failed_local_fixtures'], 0)

    def test_code_change_after_pass_invalidates_latest_submission_verdict(self):
        card = build_scorecard(plan(score_record(extra_events=(event('candidate-2', 'implement', 'SELECT 0'),))))
        q = card['questions'][0]
        self.assertEqual(q['accuracy']['status'], 'NOT_VERIFIED')
        self.assertEqual(q['accuracy']['reason'], 'TESTED_PRIOR_SQL_VERSION')
        self.assertEqual(card['summary']['latest_sql_passed_local_fixtures'], 0)
        self.assertEqual(q['behavior']['sql_submissions'], 2)

    def test_wrong_sql_hash_or_event_id_never_promoted(self):
        source = score_record()
        source['sql_accuracy']['candidate_sql_sha256'] = '0' * 64
        card = build_scorecard(plan(source))
        self.assertEqual(card['questions'][0]['accuracy']['reason'], 'GRADE_SQL_HASH_MISMATCH')
        source['sql_accuracy']['candidate_sql_sha256'] = hashlib.sha256(SQL.encode()).hexdigest()
        source['sql_accuracy']['candidate_event_id'] = 'imaginary'
        card = build_scorecard(plan(source))
        self.assertEqual(card['questions'][0]['accuracy']['reason'], 'GRADE_SUBMISSION_NOT_FOUND')

    def test_wrong_question_or_fixture_provenance_not_counted(self):
        source = score_record()
        source['sql_accuracy']['question_sha256'] = QHASHES[2]
        self.assertEqual(build_scorecard(plan(source))['questions'][0]['accuracy']['reason'], 'GRADE_EVIDENCE_MISMATCH')
        source = score_record()
        source['sql_accuracy']['official_hidden_tests'] = True
        self.assertEqual(build_scorecard(plan(source))['summary']['latest_sql_locally_verified_questions'], 0)

    def test_skipped_question_keeps_historical_observation_without_credit(self):
        card = build_scorecard(plan(score_record(skip=True)))
        self.assertEqual(card['questions'][0]['accuracy']['reason'], 'QUESTION_SKIPPED_AFTER_TEST')
        self.assertEqual(card['questions'][0]['accuracy']['fixture_passed'], 1)
        self.assertEqual(card['summary']['latest_sql_passed_local_fixtures'], 0)

    def test_unavailable_fixture_retains_unknown_denominator(self):
        record = score_record()
        record['sql_accuracy'] = {
            'correctness': 'NOT_VERIFIED', 'result': {'status': 'NOT_VERIFIED'},
            'passed_fixtures': 0, 'total_approved_fixtures': 0,
        }
        card = build_scorecard(plan(record))
        self.assertIsNone(card['questions'][0]['accuracy']['fixture_total'])
        self.assertEqual(card['questions'][0]['accuracy']['reason'], 'LOCAL_EXECUTION_NOT_VERIFIED')

    def test_behavior_counts_trace_to_event_ids_not_model_text(self):
        record = score_record(extra_events=(event('help-1', 'help', 'Need help'),))
        card = build_scorecard(plan(record))
        self.assertEqual(card['summary']['observed_closed_question_actions'], {
            'candidate_turns': 3, 'clarifications': 1, 'help_requests': 1, 'sql_submissions': 1,
        })
        self.assertEqual(card['questions'][0]['behavior']['evidence_event_ids'],
                         ['clarify-1', 'candidate-1', 'help-1'])

    def test_three_completed_questions_and_elapsed_time(self):
        card = build_scorecard(plan(score_record(0), score_record(1, verdict='FAILED'), {'outcome': 'NOT_REACHED'}))
        self.assertEqual(card['status'], 'FINAL')
        self.assertEqual(card['summary']['closed_questions'], 3)
        self.assertEqual(card['summary']['latest_sql_passed_local_fixtures'], 1)
        self.assertEqual(card['summary']['latest_sql_failed_local_fixtures'], 1)
        self.assertEqual(card['summary']['elapsed_seconds'], 100.0)
        self.assertFalse(card['summary']['clock_certified'])

    def test_scorecard_is_deterministic_and_does_not_echo_sql(self):
        one = build_scorecard(plan(score_record()))
        self.assertEqual(one, build_scorecard(copy.deepcopy(plan(score_record()))))
        self.assertNotIn(SQL, str(one))
        self.assertEqual(len(one['sha256']), 64)

    def test_legacy_e1_without_timing_or_grade(self):
        old = plan({'outcome': 'DISCUSSION_ONLY', 'session': {'events': [event('x', 'plan', 'plan')]}})
        old.pop('timing')
        card = build_scorecard(old)
        self.assertIsNone(card['summary']['elapsed_seconds'])
        self.assertEqual(card['summary']['time_integrity'], 'NOT_AVAILABLE')
        self.assertEqual(card['questions'][0]['accuracy']['status'], 'NOT_VERIFIED')

    def test_invalid_question_count_rejected(self):
        with self.assertRaisesRegex(ValueError, 'INVALID_REHEARSAL_SCORECARD_SOURCE'):
            build_scorecard({'questions': [], 'results': []})


class ScorecardHostIntegrationTests(unittest.IsolatedAsyncioTestCase):
    asyncSetUp = rehearsal_tests.RehearsalE1Tests.asyncSetUp
    asyncTearDown = rehearsal_tests.RehearsalE1Tests.asyncTearDown
    cmd = rehearsal_tests.RehearsalE1Tests.cmd
    setup_three = rehearsal_tests.RehearsalE1Tests.setup_three
    start = rehearsal_tests.RehearsalE1Tests.start
    model = rehearsal_tests.RehearsalE1Tests.model
    inspected = grading_tests.AppGradingTests.inspected
    configure_sql = grading_tests.AppGradingTests.configure_sql
    grade = grading_tests.AppGradingTests.grade

    async def test_host_state_and_export_have_same_observation(self):
        await self.inspected()
        await self.grade()
        await self.cmd('rehearsal_submit')
        await self.cmd('rehearsal_skip')
        await self.cmd('rehearsal_skip')
        scorecard = self.host.state()['evidence_scorecard']
        self.assertEqual(scorecard['summary']['latest_sql_locally_verified_questions'], 1)
        self.assertEqual(scorecard['summary']['latest_sql_passed_local_fixtures'], 1)
        self.assertEqual(scorecard['summary']['overall_grade'], 'NOT_SCORED')
        exported = (await self.cmd('export'))['export']
        self.assertEqual(exported['evidence_scorecard'], scorecard)
        self.assertEqual(exported['evidence_scorecard']['sha256'], scorecard['sha256'])

    async def test_reopen_never_executes_sql_for_scorecard(self):
        await self.inspected()
        await self.grade()
        before = self.host.state()['evidence_scorecard']
        self.host.close()
        with patch('tia_runtime.app_host.grade_fixture', side_effect=AssertionError('SQL replay forbidden')):
            self.host = await TutorialHost.open(self.directory.name)
        self.assertIsNone(self.host.state()['recovery_error'])
        self.assertEqual(self.host.state()['evidence_scorecard'], before)

    async def test_additive_projection_does_not_change_saved_digest(self):
        await self.start()
        original_digest = self.host._state_digest()
        with patch('tia_runtime.app_host.build_scorecard', return_value={'different': 'data'}):
            self.assertEqual(self.host._state_digest(), original_digest)


if __name__ == '__main__':
    unittest.main()
