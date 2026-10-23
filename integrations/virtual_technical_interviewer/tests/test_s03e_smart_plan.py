"""E3-D: source-bound SMART planner and host-persisted self-reported practice.

No test or UI should interpret user-entered practice as independent evidence of
an improved skill score, a new SQL execution receipt, or a model assessment.
"""
import copy
import tempfile
import unittest
from unittest.mock import patch

from tia_runtime.app_host import HostError, TutorialHost
from tia_runtime.smart_plan import (SmartPlanError, build_smart_plan,
    start_smart_progress, record_smart_activity, smart_progress_summary)
import test_s03e_grounded_trainer as fixtures
import test_s03e_evidence_scorecard as host_support


def synthetic_plan():
    return fixtures.plan(fixtures.rec(fixtures.candidate('c1', text='SELECT customer_id FROM customers')),
                         fixtures.rec(), fixtures.rec(), status='COMPLETE')


class SmartPlanUnitTests(unittest.TestCase):
    def setUp(self):
        self.source = synthetic_plan()
        self.plan = build_smart_plan(self.source)
        self.progress = start_smart_progress(self.plan, 1_780_000_000)
        self.task = self.plan['goals'][0]['id']

    def test_locked_plan_is_deterministic_and_no_model_score(self):
        self.assertEqual(self.plan, build_smart_plan(copy.deepcopy(self.source)))
        self.assertEqual(self.plan['schema'], 'tia-smart-improvement-plan/v1')
        self.assertEqual(self.plan['status'], 'READY_TO_START')
        self.assertEqual(self.plan['numeric_competency_score'], 'NOT_SCORED')
        self.assertEqual(self.plan['improvement_certification'], 'NOT_ESTABLISHED')

    def test_incomplete_rehearsal_cannot_start_plan(self):
        source = fixtures.plan(fixtures.rec(fixtures.candidate('c1')), status='ACTIVE')
        p = build_smart_plan(source)
        self.assertEqual(p['status'], 'AWAITING_LOCKED_INTERVIEW')
        self.assertEqual(p['goals'], [])
        with self.assertRaisesRegex(SmartPlanError, 'SMART_PLAN_NOT_READY'):
            start_smart_progress(p, 100)

    def test_all_five_smart_fields_tether_to_original_drill(self):
        goals = self.plan['goals']
        self.assertGreater(len(goals), 0)
        self.assertLessEqual(len(goals), 3)
        for goal in goals:
            self.assertTrue(all(goal[k] for k in ('specific', 'measurable', 'achievable', 'relevant', 'time_bound', 'source')))
            self.assertEqual(goal['source']['trainer_sha256'], self.plan['trainer_sha256'])
            self.assertEqual(goal['verification']['improvement'], 'NOT_ESTABLISHED')

    def test_deadlines_only_after_explicit_host_start(self):
        self.assertNotIn('started_wall_seconds', self.plan)
        for goal in self.plan['goals']:
            self.assertEqual(self.progress['deadlines'][goal['id']],
                             self.progress['started_wall_seconds'] + 86400 * goal['time_bound']['days_after_explicit_start'])
        self.assertEqual(self.progress['entries'], [])

    def test_self_report_only_not_verified_improvement(self):
        p = record_smart_activity(self.plan, self.progress, task_id=self.task,
                kind='PRACTICED', note='Reviewed null and tie cases', artifact_sha256=None,
                host_wall_seconds=1_780_000_100)
        s = smart_progress_summary(self.plan, p)
        self.assertEqual(s['goals'][0]['latest_activity'], 'PRACTICED')
        self.assertEqual(s['recorded_attempts'], 1)
        self.assertEqual(s['independently_verified_improvements'], 0)
        self.assertEqual(p['entries'][0]['verification'], 'SELF_REPORTED_UNVERIFIED')
        self.assertEqual(p['ability_improved'], 'NOT_ESTABLISHED')

    def test_external_retest_hash_remains_an_unverified_user_claim(self):
        p = record_smart_activity(self.plan, self.progress, task_id=self.task,
                kind='RETEST_RECORDED', note='External retest claimed by candidate',
                artifact_sha256='c'*64, host_wall_seconds=1_780_000_500)
        self.assertEqual(p['entries'][0]['artifact_sha256'], 'c'*64)
        self.assertEqual(p['entries'][0]['verification'], 'SELF_REPORTED_UNVERIFIED')
        self.assertFalse(smart_progress_summary(self.plan, p)['goals'][0]['independently_verified_improvement'])

    def test_forged_task_and_status_are_rejected(self):
        for task, kind in (('SMART-Q9-FORGED','PRACTICED'),(self.task,'PASTED_SCORE_100')):
            with self.subTest(task=task, kind=kind), self.assertRaises(SmartPlanError):
                record_smart_activity(self.plan, self.progress, task_id=task,
                    kind=kind, note='Completed 100 percent', artifact_sha256=None,
                    host_wall_seconds=1_780_000_500)

    def test_missing_retest_hash_and_fake_hash_rejected(self):
        for digest in (None, 'A'*64, 'not-a-hash', 42):
            with self.subTest(digest=digest), self.assertRaises(SmartPlanError):
                record_smart_activity(self.plan, self.progress, task_id=self.task,
                    kind='RETEST_RECORDED', note='External SQL retest',
                    artifact_sha256=digest, host_wall_seconds=1_780_000_500)

    def test_no_hash_allowed_for_general_practice(self):
        with self.assertRaises(SmartPlanError):
            record_smart_activity(self.plan, self.progress, task_id=self.task,
                kind='PRACTICED', note='SQL local review', artifact_sha256='a'*64,
                host_wall_seconds=1_780_000_500)

    def test_changed_interview_source_invalidates_plan(self):
        changed = copy.deepcopy(self.source)
        changed['results'][0]['session']['events'][0]['payload']['text'] = 'SELECT now()'
        new = build_smart_plan(changed)
        with self.assertRaisesRegex(SmartPlanError, 'SMART_PLAN_SOURCE_CHANGED'):
            record_smart_activity(new, self.progress, task_id=self.task,
                kind='PRACTICED', note='New version', artifact_sha256=None,
                host_wall_seconds=1_780_000_500)

    def test_tampered_progress_digest_is_rejected(self):
        altered = copy.deepcopy(self.progress)
        altered['completion_authority'] = 'AI_CERTIFIED'
        with self.assertRaisesRegex(SmartPlanError, 'SMART_PROGRESS_CORRUPTED'):
            smart_progress_summary(self.plan, altered)

    def test_note_utf8_limits(self):
        for note in (' ', 'x', '中' * 167, 'text\x00injected', 7):
            with self.subTest(note=str(note)[:20]), self.assertRaises(SmartPlanError):
                record_smart_activity(self.plan, self.progress, task_id=self.task,
                    kind='PRACTICED', note=note, artifact_sha256=None,
                    host_wall_seconds=1_780_000_500)

    def test_wall_clock_source_and_rollback_rejected(self):
        for time in (True, float('nan'), -1, 1_779_999_900):
            with self.subTest(time=time), self.assertRaises(SmartPlanError):
                record_smart_activity(self.plan, self.progress, task_id=self.task,
                    kind='PRACTICED', note='Practised once', artifact_sha256=None,
                    host_wall_seconds=time)

    def test_progress_log_is_immutable_and_bounded(self):
        old = copy.deepcopy(self.progress)
        current = self.progress
        for i in range(8):
            current = record_smart_activity(self.plan, current, task_id=self.task,
                kind='PRACTICED', note='Practised scenario %s' % i,
                artifact_sha256=None, host_wall_seconds=1_780_000_100 + i)
        self.assertEqual(self.progress, old)
        self.assertEqual(len(current['entries']), 8)
        with self.assertRaisesRegex(SmartPlanError, 'SMART_HISTORY_LIMIT'):
            record_smart_activity(self.plan, current, task_id=self.task,
                kind='PRACTICED', note='Ninth attempt', artifact_sha256=None,
                host_wall_seconds=1_780_000_900)

    def test_skipped_question_is_not_diagnosed_as_zero_ability(self):
        self.assertIn('NOT_ESTABLISHED', self.plan['improvement_certification'])
        self.assertTrue(all(goal['verification']['fresh_retest'] == 'NEW_INDEPENDENT_TEST_REQUIRED'
                            for goal in self.plan['goals']))


class SmartPlanHostTests(unittest.IsolatedAsyncioTestCase):
    asyncSetUp = host_support.ScorecardHostIntegrationTests.asyncSetUp
    asyncTearDown = host_support.ScorecardHostIntegrationTests.asyncTearDown
    async def cmd(self, action, params=None, expected=True, **kwargs):
        return await host_support.ScorecardHostIntegrationTests.cmd(self, action,
            params if params is not None else kwargs, expected=expected)
    inspected = host_support.ScorecardHostIntegrationTests.inspected
    setup_three = host_support.ScorecardHostIntegrationTests.setup_three
    grade = host_support.ScorecardHostIntegrationTests.grade
    model = host_support.ScorecardHostIntegrationTests.model
    configure_sql = host_support.ScorecardHostIntegrationTests.configure_sql
    start = host_support.ScorecardHostIntegrationTests.start

    async def close_interview(self):
        await self.inspected()
        await self.cmd('rehearsal_submit')
        await self.cmd('rehearsal_skip')
        await self.cmd('rehearsal_skip')

    async def test_start_only_after_locked_rehearsal(self):
        with self.assertRaisesRegex(HostError, 'SMART_REQUIRES_LOCKED_REHEARSAL'):
            await self.host.command('smart_start', {})
        await self.inspected()
        with self.assertRaisesRegex(HostError, 'SMART_REQUIRES_LOCKED_REHEARSAL'):
            await self.host.command('smart_start', {})

    async def test_start_record_export_and_reopen_exact(self):
        await self.close_interview()
        before = self.host.state()['evidence_scorecard']
        before_record = self.host._state_digest()
        await self.cmd('smart_start')
        s = self.host.state();task = s['smart_plan']['goals'][0]['id']
        self.assertTrue(s['smart_progress']['started_wall_seconds'] > 0)
        self.assertNotEqual(self.host._state_digest(), before_record)
        await self.cmd('smart_record', task_id=task, kind='PRACTICED', note='Tried a new tie edge case', artifact_sha256=None)
        current = self.host.state()
        self.assertEqual(current['smart_progress_summary']['recorded_attempts'], 1)
        self.assertEqual(current['evidence_scorecard'], before)
        self.assertEqual(self.host.export()['smart_progress'], current['smart_progress'])
        self.host.close()
        with patch('tia_runtime.app_host.grade_fixture', side_effect=AssertionError('SQL rerun')):
            self.host = await TutorialHost.open(self.directory.name)
        self.assertIsNone(self.host.state()['recovery_error'])
        self.assertEqual(self.host.state()['smart_progress'], current['smart_progress'])
        self.assertEqual(self.host.state()['evidence_scorecard'], before)

    async def test_old_rehearsal_digest_unchanged_until_explicit_start(self):
        await self.close_interview()
        original = self.host._state_digest()
        self.assertEqual(self.host.state()['smart_progress'], None)
        self.assertEqual(self.host.state()['smart_progress_summary']['status'], 'NOT_STARTED')
        self.assertEqual(self.host._state_digest(), original)
        self.host.close();self.host = await TutorialHost.open(self.directory.name)
        self.assertIsNone(self.host.state()['recovery_error'])
        self.assertEqual(self.host._state_digest(), original)

    async def test_user_cannot_set_clock_or_external_grade(self):
        await self.close_interview()
        for action, params in (
            ('smart_start', {'start_time': 0}),
            ('smart_record', {'task_id': 'x', 'kind':'PRACTICED', 'note':'ok', 'artifact_sha256': None, 'competency':100}),
        ):
            with self.subTest(action=action), self.assertRaises(HostError):
                await self.host.command(action, params)

    async def test_double_start_and_wrong_task_do_not_append_event(self):
        await self.close_interview();await self.cmd('smart_start')
        before = len(self.host._journal)
        with self.assertRaisesRegex(HostError, 'SMART_ALREADY_STARTED'):
            await self.host.command('smart_start', {})
        self.assertEqual(len(self.host._journal), before)
        with self.assertRaisesRegex(HostError, 'UNKNOWN_SMART_TASK'):
            await self.host.command('smart_record', {'task_id':'SMART-forged','kind':'PRACTICED',
                                                        'note':'Should fail','artifact_sha256':None})
        self.assertEqual(len(self.host._journal), before)

    async def test_retest_is_user_reported_without_changing_local_sql(self):
        await self.close_interview();await self.cmd('smart_start')
        s = self.host.state();grade=s['evidence_scorecard']
        task=s['smart_plan']['goals'][0]['id']
        await self.cmd('smart_record', task_id=task, kind='RETEST_RECORDED',
                       note='External retest attempt on second fixture', artifact_sha256='d'*64)
        self.assertEqual(self.host.state()['evidence_scorecard'], grade)
        self.assertEqual(self.host.state()['smart_progress_summary']['independently_verified_improvements'], 0)
        self.assertEqual(self.host.state()['smart_progress']['entries'][-1]['verification'],'SELF_REPORTED_UNVERIFIED')

    async def test_new_activity_survives_host_reset_only_until_explicit_reset(self):
        await self.close_interview();await self.cmd('smart_start')
        await self.cmd('reset')
        self.assertNotIn('smart_progress', self.host.state())

    async def test_pending_paid_trainer_prevents_parallel_activity(self):
        await self.close_interview()
        await self.cmd('native_prepare_trainer', request_id='req-1', generation='gen-1')
        with self.assertRaisesRegex(HostError, 'NATIVE_TRAINER_PENDING'):
            await self.host.command('smart_start', {})
