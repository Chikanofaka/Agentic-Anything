"""Synthetic source binding, execution boundary, replay and evaluator integration."""
import copy
import json
import unittest
from unittest.mock import patch
from tia_runtime import post_interview_sql as sql
from tia_runtime.app_host import TutorialHost, HostError
from tia_runtime.evidence_scorecard import build_scorecard
from tia_runtime.sql_accuracy import AccuracyError
import test_evaluator_host as helpers


def synthetic_runner(blob, code, digest, **kwargs):
    assert kwargs['private_query'] is True
    return {'result':{'status':'PASSED','reason':'PASS'}}


class PostSQLTests(unittest.IsolatedAsyncioTestCase):
    asyncSetUp=helpers.EvaluatorHostTests.asyncSetUp
    asyncTearDown=helpers.EvaluatorHostTests.asyncTearDown
    cmd=helpers.EvaluatorHostTests.cmd
    inspected=helpers.EvaluatorHostTests.inspected
    grade=helpers.EvaluatorHostTests.grade
    configure_sql=helpers.EvaluatorHostTests.configure_sql
    start=helpers.EvaluatorHostTests.start
    model=helpers.EvaluatorHostTests.model
    setup_three=helpers.EvaluatorHostTests.setup_three
    closed=helpers.EvaluatorHostTests.closed

    async def prepared(self):
        await self.cmd('post_sql_review',{'question_index':0,'suite_id':'bus_last_person'})
        reviewed=self.host.state()['post_interview_sql']['review']
        return (await self.cmd('native_prepare_post_sql',{'request_id':'synthetic-sql','generation':'synthetic-generation','review_sha256':reviewed['review_sha256']}))['prepared']

    async def test_review_prepare_never_runs_sql_or_model(self):
        await self.closed()
        original=copy.deepcopy(self.host._rehearsal)
        with patch('subprocess.Popen', side_effect=AssertionError('no external work')):
            packet=await self.prepared()
        self.assertEqual(self.host._rehearsal,original)
        self.assertEqual(len(packet['cases']),3)
        self.assertNotIn('candidate_sql',self.host.state()['post_interview_sql']['review'])
        self.assertTrue(self.host.state()['post_interview_sql']['pending'])

    async def test_malformed_nested_fields_fail_before_execution(self):
        await self.closed(); packet=await self.prepared()
        mutations=[('pending',None),('pending',[]),('candidate_sql',{}),('candidate_sql',''),('cases',[None])]
        for key,value in mutations:
            bad=copy.deepcopy(packet);bad[key]=value
            with self.subTest(key=key,value=value),self.assertRaises(sql.PostSQLError):
                sql.execute(bad,runner=lambda *a,**k:self.fail('must not execute'),pg_config='synthetic')
        for key,value in [('question_index',True),('suite_id',[]),('candidate_event_id',None),('generation','bad\nvalue'),('record_sha256','x')]:
            bad=copy.deepcopy(packet);bad['pending'][key]=value
            with self.subTest(key=key),self.assertRaises(sql.PostSQLError):
                sql.execute(bad,runner=lambda *a,**k:self.fail('must not execute'),pg_config='synthetic')
        result=sql.execute(packet,runner=synthetic_runner,pg_config='synthetic')
        for cases in ([None],[{'status':'PASSED'}],[],{}):
            bad=copy.deepcopy(result);bad['cases']=cases;bad['sha256']=sql.sha({k:v for k,v in bad.items() if k!='sha256'})
            with self.subTest(cases=cases),self.assertRaises(sql.PostSQLError):
                sql.commit(self.host._rehearsal,packet['pending'],bad)

    async def test_case_pack_mutation_and_wrong_code_rejected_before_runner(self):
        await self.closed(); packet=await self.prepared()
        for field in ('candidate_sql','cases'):
            bad=copy.deepcopy(packet)
            if field=='candidate_sql': bad[field]+=' changed'
            else: bad['cases'][0]['fixture']['expected']['rows']=[['wrong']]
            with self.subTest(field=field),self.assertRaises(sql.PostSQLError):
                sql.execute(bad,runner=lambda *a,**k:self.fail('must not execute'),pg_config='synthetic')

    async def test_commit_adds_retrospective_evidence_without_changing_interview(self):
        await self.closed(); original=copy.deepcopy(self.host._rehearsal); packet=await self.prepared()
        result=sql.execute(packet,runner=synthetic_runner,pg_config='synthetic')
        await self.cmd('native_commit_post_sql',{'result':result})
        self.assertEqual(self.host._rehearsal,original)
        state=self.host.state(); record=state['post_interview_sql']['results']['0']
        self.assertEqual((record['status'],record['passed'],record['total']),('PASSED',3,3))
        self.assertEqual(state['evidence_scorecard']['questions'][0]['accuracy']['status'],'NOT_VERIFIED')
        evaluator=state['evaluator_report']['questions'][0]
        self.assertEqual(evaluator['raw_metrics']['accuracy']['status'],'PASSED')
        self.assertEqual(evaluator['dimensions'][0]['status'],'NOT_EVALUATED')
        spec=(await self.cmd('native_prepare_evaluator',{'request_id':'new-review','generation':'g1','question_index':0}))['prepared']
        context=json.loads(spec['input'])
        self.assertEqual(context['local_execution']['status'],'PASSED')
        self.assertTrue(context['criteria'][0]['can_propose_anchor'])
        self.assertNotIn('tables',context['local_execution'])

    async def test_late_duplicate_and_cross_generation_replies_rejected(self):
        await self.closed(); packet=await self.prepared(); result=sql.execute(packet,runner=synthetic_runner,pg_config='synthetic')
        await self.cmd('native_cancel_post_sql')
        with self.assertRaisesRegex(HostError,'POST_SQL_NOT_PENDING'):
            await self.host.command('native_commit_post_sql',{'result':result})
        new=(await self.cmd('native_prepare_post_sql',{'request_id':'new-request','generation':'new-generation','review_sha256':packet['pending']['review_sha256']}))['prepared']
        with self.assertRaisesRegex(HostError,'POST_SQL_BINDING_MISMATCH'):
            await self.host.command('native_commit_post_sql',{'result':result})
        current=sql.execute(new,runner=synthetic_runner,pg_config='synthetic')
        await self.cmd('native_commit_post_sql',{'result':current})
        with self.assertRaisesRegex(HostError,'POST_SQL_NOT_PENDING'):
            await self.host.command('native_commit_post_sql',{'result':current})

    async def test_unavailable_runner_is_not_wrong_answer(self):
        await self.closed(); packet=await self.prepared()
        def unavailable(*a,**k): raise AccuracyError('POSTGRES_SERVER_NOT_AVAILABLE')
        result=sql.execute(packet,runner=unavailable,pg_config='synthetic')
        await self.cmd('native_commit_post_sql',{'result':result})
        self.assertEqual(self.host.state()['post_interview_sql']['results']['0']['status'],'NOT_VERIFIED')
        self.assertEqual(self.host.state()['evaluator_report']['questions'][0]['raw_metrics']['accuracy']['status'],'NOT_VERIFIED')

    async def test_failed_case_cannot_be_aggregated_as_pass(self):
        await self.closed(); packet=await self.prepared()
        result=sql.execute(packet,runner=lambda *a,**k:{'result':{'status':'FAILED','reason':'ROWS_MISMATCH'}},pg_config='synthetic')
        await self.cmd('native_commit_post_sql',{'result':result})
        record=self.host.state()['post_interview_sql']['results']['0']
        self.assertEqual((record['status'],record['passed']),('FAILED',0))
        self.assertEqual(self.host.state()['evaluator_report']['questions'][0]['raw_metrics']['accuracy']['status'],'FAILED')

    async def test_old_assessment_is_archived_and_explicit_reevaluation_enabled(self):
        await self.closed()
        spec=(await self.cmd('native_prepare_evaluator',{'request_id':'eval-before','generation':'eval-generation','question_index':0}))['prepared']
        await self.cmd('native_commit_evaluator',helpers.commitment(spec))
        original=copy.deepcopy(self.host._evaluator_assessments['0'])
        packet=await self.prepared()
        await self.cmd('native_commit_post_sql',{'result':sql.execute(packet,runner=synthetic_runner,pg_config='synthetic')})
        readout=self.host.state()['post_interview_sql']
        self.assertEqual(readout['assessment_archive'][0]['assessment'],original)
        self.assertIsNone(self.host.state()['evaluator_report']['questions'][0]['assessment'])
        self.assertTrue(self.host.state()['evaluator_report']['questions'][0]['eligible'])

    async def test_recovery_uses_observation_without_running_database(self):
        await self.closed(); packet=await self.prepared()
        await self.cmd('native_commit_post_sql',{'result':sql.execute(packet,runner=synthetic_runner,pg_config='synthetic')})
        expected=copy.deepcopy(self.host.state()['post_interview_sql'])
        data_dir=self.host.store.root if hasattr(self.host.store,'root') else self.directory.name
        self.host.close()
        with patch('subprocess.Popen',side_effect=AssertionError('replay may not execute')):
            self.host=await TutorialHost.open(data_dir)
        self.assertIsNone(self.host.state()['recovery_error'])
        self.assertEqual(self.host.state()['post_interview_sql'],expected)

    async def test_pending_restart_cancels_instead_of_relaunching(self):
        await self.closed(); await self.prepared()
        data_dir=self.host.store.root if hasattr(self.host.store,'root') else self.directory.name
        self.host.close()
        with patch('subprocess.Popen',side_effect=AssertionError('no restart execution')):
            self.host=await TutorialHost.open(data_dir)
        self.assertIsNone(self.host.state()['recovery_error'])
        self.assertFalse(self.host.state()['post_interview_sql']['pending'])


    async def test_rerun_keeps_observations_and_archives_prior_assessment(self):
        await self.closed(); packet=await self.prepared()
        await self.cmd('native_commit_post_sql',{'result':sql.execute(packet,runner=synthetic_runner,pg_config='synthetic')})
        spec=(await self.cmd('native_prepare_evaluator',{'request_id':'eval-after','generation':'eval-generation','question_index':0}))['prepared']
        await self.cmd('native_commit_evaluator',helpers.commitment(spec))
        packet=await self.prepared()
        def unavailable(*a,**k): raise AccuracyError('POSTGRES_SERVER_NOT_AVAILABLE')
        await self.cmd('native_commit_post_sql',{'result':sql.execute(packet,runner=unavailable,pg_config='synthetic')})
        state=self.host.state()['post_interview_sql']
        self.assertEqual([v['status'] for v in state['observations']],['PASSED','NOT_VERIFIED'])
        self.assertEqual(len(state['assessment_archive']),1)
        self.assertIsNone(self.host.state()['evaluator_report']['questions'][0]['assessment'])

    async def test_rejection_diagnosis_survives_reload_and_clears_on_explicit_request(self):
        await self.closed()
        await self.cmd('native_prepare_evaluator',{'request_id':'eval-reject','generation':'g','question_index':0})
        await self.cmd('native_reject_evaluator',{'code':'EVALUATOR_UNCITED_OR_CROSS_QUESTION_EVIDENCE'})
        state=self.host.state()
        self.assertFalse(state['native_evaluator_interrupted'])
        self.assertEqual(state['native_evaluator_error_code'],'EVALUATOR_UNCITED_OR_CROSS_QUESTION_EVIDENCE')
        self.host.close(); self.host=await TutorialHost.open(self.directory.name)
        self.assertIsNone(self.host.state()['recovery_error'])
        self.assertEqual(self.host.state()['native_evaluator_error_code'],state['native_evaluator_error_code'])
        await self.cmd('native_prepare_evaluator',{'request_id':'eval-again','generation':'g2','question_index':0})
        self.assertIsNone(self.host.state()['native_evaluator_error_code'])


class CasePackTests(unittest.TestCase):
    def test_all_reviewed_case_packs_are_valid_distinct_and_not_official(self):
        for suite in sql.SUITES:
            fixtures=sql.fixtures(suite,'a'*64)
            self.assertEqual(len(fixtures),3)
            self.assertEqual(len({x['fixture_sha256'] for x in fixtures}),3)
            for row in fixtures:
                fixture,checksum=sql.validate_fixture(sql.canonical(row['fixture']).encode())
                self.assertEqual(checksum,row['fixture_sha256'])
                self.assertEqual(fixture['question_sha256'],'a'*64)
