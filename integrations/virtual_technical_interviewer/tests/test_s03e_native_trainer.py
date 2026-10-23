"""E3-C-B: native-only BYOK Trainer draft, evidence binding, replay, abstention."""
import asyncio
import copy
import json
import tempfile
import unittest
from unittest.mock import patch

from tia_runtime.native_trainer import (NativeTrainerError, prepare_native_trainer,
                                        commit_native_trainer)
from tia_runtime.grounded_trainer import build_grounded_trainer
from tia_runtime.app_host import TutorialHost, HostError
import test_s03e_grounded_trainer as t3
import test_s03e_evidence_scorecard as e3a

RID='native-trainer-request-1'
GEN='native-generation-1'
MODEL='gpt-4.1-mini'


def plan():
    return t3.plan(t3.rec(t3.candidate('c1', text='SELECT private_value FROM sensitive_table')),t3.rec(),t3.rec(),status='COMPLETE')


def proposal_from(plan_value):
    trainer=build_grounded_trainer(plan_value)
    return t3.proposal(trainer)


def commitment(pending, proposal=None, plan_value=None):
    return {'transaction_id':pending['transaction_id'],'request_id':pending['request_id'],
            'generation':pending['generation'],
            'reply':{'reply':json.dumps(proposal if proposal is not None else proposal_from(plan_value or plan()))},
            'model':MODEL,'usage':{'input_tokens':200,'output_tokens':100,'total_tokens':300}}


class NativeTrainerContracts(unittest.TestCase):
    def setUp(self):
        self.source=plan()
        self.pending,self.spec=prepare_native_trainer(self.source,RID,GEN,'en')

    def test_native_model_spec_is_role_bound_and_bounded(self):
        s=self.spec
        self.assertEqual(s['role'],'trainer')
        self.assertEqual(s['schema_name'],'tia_trainer_reply')
        self.assertEqual(s['max_output_tokens'],600)
        self.assertEqual(s['source_sha256']['evidence/trainer'],build_grounded_trainer(self.source)['sha256'])
        self.assertLess(len(s['input'].encode()),16000)

    def test_input_contains_only_approved_bounded_citation_excerpt(self):
        packet=json.loads(self.spec['input'])
        self.assertEqual(packet['candidate_excerpts'][0]['event_id'],'c1')
        self.assertEqual(packet['candidate_excerpts'][0]['kind'],'implement')
        self.assertEqual(packet['known_limits']['technical_grade'],'NOT_SCORED')
        self.assertNotIn('api_key', self.spec['input'].lower())
        self.assertNotIn('official hidden tests passed',self.spec['input'].lower())

    def test_4000_character_sql_not_fully_sent(self):
        source=t3.plan(t3.rec(t3.candidate('c1',text='SELECT ' + 'A'*4000)),t3.rec(),t3.rec(),status='COMPLETE')
        _,spec=prepare_native_trainer(source,RID,GEN,'zh')
        events=json.loads(spec['input'])['candidate_excerpts']
        self.assertEqual(len(events[0]['excerpt']),280)
        self.assertTrue(events[0]['excerpt_truncated'])
        self.assertNotIn('A'*400,self.spec['input'])

    def test_in_progress_cannot_generate_paid_request(self):
        source=t3.plan(t3.rec(t3.candidate('c1')),status='ACTIVE')
        with self.assertRaisesRegex(NativeTrainerError,'TRAINER_EVIDENCE_NOT_READY'):
            prepare_native_trainer(source,RID,GEN,'en')

    def test_ids_must_be_host_native_shape(self):
        for rid, gen in (('',GEN),(RID,'bad token'),('x'*100,GEN),(RID,42)):
            with self.subTest(rid=rid,gen=gen), self.assertRaises(NativeTrainerError):
                prepare_native_trainer(self.source,rid,gen,'en')

    def test_commit_yields_pending_review_not_score(self):
        p=commit_native_trainer(self.source,self.pending,commitment(self.pending,plan_value=self.source))
        self.assertEqual(p['status'],'PENDING_HUMAN_REVIEW')
        self.assertEqual(p['authority'],'NONE')
        self.assertEqual(p['technical_score'],'NOT_SCORED')
        self.assertFalse(p['validation']['validated_semantic_quality'])
        self.assertEqual(len(p['sha256']),64)

    def test_stale_native_generation_and_transaction_rejected(self):
        for k in ('request_id','generation','transaction_id'):
            c=commitment(self.pending,plan_value=self.source);c[k]='forged'
            with self.subTest(field=k),self.assertRaisesRegex(NativeTrainerError,'STALE_TRAINER_REQUEST'):
                commit_native_trainer(self.source,self.pending,c)

    def test_forged_citations_and_wrong_hash_fail_closed(self):
        for item in ({'cited_candidate_events':['forged']}, {'trainer_sha256':'a'*64},
                     {'cited_fixture_sha256':'b'*64}, {'technical_score':100}):
            p=proposal_from(self.source);p.update(item)
            with self.subTest(item=item),self.assertRaisesRegex(NativeTrainerError,'INVALID_GROUNDED_TRAINER_REPLY'):
                commit_native_trainer(self.source,self.pending,commitment(self.pending,proposal=p))

    def test_invalid_json_duplicate_keys_and_nan_rejected(self):
        for raw in ('{}', '{"x":1,"x":2}', '{"x":NaN}', '[]', 'not json'):
            c=commitment(self.pending,plan_value=self.source);c['reply']={'reply':raw}
            with self.subTest(raw=raw),self.assertRaisesRegex(NativeTrainerError,'INVALID_GROUNDED_TRAINER_REPLY'):
                commit_native_trainer(self.source,self.pending,c)

    def test_changed_source_prohibits_stale_feedback(self):
        changed=copy.deepcopy(self.source)
        changed['results'][0]['session']['events'][0]['payload']['text']='SELECT now()'
        with self.assertRaisesRegex(NativeTrainerError,'TRAINER_SOURCE_CHANGED'):
            commit_native_trainer(changed,self.pending,commitment(self.pending,plan_value=self.source))

    def test_model_instruction_does_not_grant_authority(self):
        self.assertIn('PENDING_HUMAN_REVIEW',self.spec['instructions'])
        self.assertIn('untrusted',self.spec['instructions'].lower())
        self.assertNotIn('You may award a score',self.spec['instructions'])


class NativeTrainerHost(unittest.IsolatedAsyncioTestCase):
    asyncSetUp=e3a.ScorecardHostIntegrationTests.asyncSetUp
    asyncTearDown=e3a.ScorecardHostIntegrationTests.asyncTearDown
    async def cmd(self, action, params=None, expected=True, **kwargs):
        return await e3a.ScorecardHostIntegrationTests.cmd(self, action, params if params is not None else kwargs, expected=expected)
    inspected=e3a.ScorecardHostIntegrationTests.inspected
    grade=e3a.ScorecardHostIntegrationTests.grade
    configure_sql=e3a.ScorecardHostIntegrationTests.configure_sql
    start=e3a.ScorecardHostIntegrationTests.start
    model=e3a.ScorecardHostIntegrationTests.model
    setup_three=e3a.ScorecardHostIntegrationTests.setup_three

    async def closed(self):
        await self.inspected()
        await self.cmd('rehearsal_submit');await self.cmd('rehearsal_skip');await self.cmd('rehearsal_skip')

    async def prepared(self):
        result=await self.host.handle({'id':'request-0','action':'native_prepare_trainer',
                  'params':{'request_id':RID,'generation':GEN}})
        self.assertTrue(result['ok'],result.get('error'))
        return result['prepared'],self.host._trainer_pending

    async def test_requires_completed_interview(self):
        await self.inspected()
        with self.assertRaisesRegex(HostError,'TRAINER_REQUIRES_LOCKED_REHEARSAL'):
            await self.host.command('native_prepare_trainer',{'request_id':RID,'generation':GEN})

    async def test_paid_trainer_persists_validated_proposal_and_keeps_score(self):
        await self.closed()
        state=self.host.state()
        digest0=self.host._state_digest()
        spec,pending=await self.prepared()
        self.assertEqual(spec['role'],'trainer')
        self.assertTrue(self.host.state()['native_trainer_pending'])
        c=commitment(pending,plan_value=self.host._rehearsal)
        await self.cmd('native_commit_trainer',**c)
        current=self.host.state()
        self.assertFalse(current['native_trainer_pending'])
        self.assertEqual(current['native_trainer_feedback']['status'],'PENDING_HUMAN_REVIEW')
        self.assertEqual(current['evidence_scorecard'],state['evidence_scorecard'])
        self.assertEqual(current['communication_evidence'],state['communication_evidence'])
        self.assertEqual(current['grounded_trainer'],state['grounded_trainer'])
        self.assertEqual(self.host._state_digest(),digest0)
        self.assertEqual(self.host.export()['native_trainer_feedback'],current['native_trainer_feedback'])

    async def test_reopen_is_read_only_no_sql_or_paid_requests(self):
        await self.closed()
        _,pending=await self.prepared()
        await self.cmd('native_commit_trainer',**commitment(pending,plan_value=self.host._rehearsal))
        original=self.host.state()['native_trainer_feedback']
        self.host.close()
        with patch('tia_runtime.app_host.grade_fixture',side_effect=AssertionError('SQL execution on reopen')):
            self.host=await TutorialHost.open(self.directory.name)
            self.assertIsNone(self.host.state()['recovery_error'])
            self.assertEqual(self.host.state()['native_trainer_feedback'],original)
            self.assertFalse(self.host.state()['native_trainer_pending'])
        # No request/commit to a model is even possible in this Python replay.

    async def test_crash_after_prepare_is_marked_interrupted_not_auto_retried(self):
        await self.closed();await self.prepared()
        self.host.close()
        self.host=await TutorialHost.open(self.directory.name)
        s=self.host.state()
        self.assertFalse(s['native_trainer_pending'])
        self.assertTrue(s['native_trainer_interrupted'])
        self.assertIsNone(s['native_trainer_feedback'])
        self.assertEqual(self.host._journal[-1]['action'],'native_cancel_trainer')

    async def test_duplicate_call_blocked_and_no_second_charge(self):
        await self.closed();await self.prepared()
        with self.assertRaisesRegex(HostError,'TRAINER_ALREADY_REQUESTED'):
            await self.host.command('native_prepare_trainer',{'request_id':'next','generation':GEN})

    async def test_invalid_model_reply_not_saved_as_feedback(self):
        await self.closed();_,pending=await self.prepared()
        params=commitment(pending,plan_value=self.host._rehearsal)
        params['reply']={'reply':'invalid'}
        with self.assertRaisesRegex(HostError,'INVALID_GROUNDED_TRAINER_REPLY'):
            await self.host.command('native_commit_trainer',params)
        self.assertTrue(self.host.state()['native_trainer_pending'])
        await self.cmd('native_cancel_trainer')
        self.assertTrue(self.host.state()['native_trainer_interrupted'])
        self.assertIsNone(self.host.state()['native_trainer_feedback'])

    async def test_feedback_rejects_second_paid_request(self):
        await self.closed();_,pending=await self.prepared()
        await self.cmd('native_commit_trainer',**commitment(pending,plan_value=self.host._rehearsal))
        with self.assertRaisesRegex(HostError,'TRAINER_ALREADY_REQUESTED'):
            await self.host.command('native_prepare_trainer',{'request_id':'fresh','generation':GEN})

    async def test_host_command_rejects_renderer_style_authority(self):
        await self.closed()
        for p in ({'request_id':RID,'generation':GEN,'api_key':'forged'},
                  {'request_id':RID,'generation':GEN,'role':'trainer'},
                  {'request_id':RID,'generation':{'credential':'hidden'}}):
            with self.subTest(params=p),self.assertRaises(HostError):
                await self.host.command('native_prepare_trainer',p)

    async def test_replay_saved_feedback_validation_does_not_forge_historical_grade(self):
        await self.closed();_,pending=await self.prepared()
        await self.cmd('native_commit_trainer',**commitment(pending,plan_value=self.host._rehearsal))
        self.host.close();self.host=await TutorialHost.open(self.directory.name)
        self.assertEqual(self.host.state()['rehearsal']['technical'],'NOT_SCORED')
        self.assertEqual(self.host.state()['native_trainer_feedback']['semantic_truth'],'HUMAN_REVIEW_REQUIRED')


if __name__=='__main__':unittest.main()
