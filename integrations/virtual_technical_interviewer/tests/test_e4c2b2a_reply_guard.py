"""C2B2A nonprovider model-reply safety gates and static integration invariants."""
import unittest
from pathlib import Path
from tia_runtime.adaptive_reply_guard import guard_adaptive_reply, ReplyGuardError, GUARD_VERSION

POLICY = {
    'rule_id':'E4C2B1_HOST_DECISION', 'action':'REQUEST_TEST',
    'candidate_event_ids':['candidate-001'], 'question_sha256':'a'*64,
    'max_hint_level':'H0', 'disclosure_scope':'PUBLIC_TASK_ONLY',
    'technical':'NOT_SCORED', 'receipt_status':'NOT_VERIFIED',
    'execution_receipt_ref':None,
}

class HostReplyGuardTests(unittest.TestCase):
    def test_allows_bounded_evidence_request(self):
        self.assertIsNone(guard_adaptive_reply(POLICY, 'What edge case would you propose to test?'))
    def test_b05_clarification_is_allowed(self):
        policy=dict(POLICY, action='CLARIFY')
        self.assertIsNone(guard_adaptive_reply(policy,'How should ties on the timestamp be handled?'))
    def test_strict_decline_is_allowed(self):
        policy=dict(POLICY, action='DECLINE')
        self.assertIsNone(guard_adaptive_reply(policy, 'Please explain your independent debugging approach first.'))
    def test_supportive_diagnostic_is_allowed(self):
        policy=dict(POLICY, action='DIAGNOSTIC_QUESTION')
        self.assertIsNone(guard_adaptive_reply(policy, 'Where does your current assumption stop matching the example?'))
    def test_rejects_code_fence(self):
        with self.assertRaises(ReplyGuardError): guard_adaptive_reply(POLICY, '```sql\nSELECT * FROM x\n```')
    def test_rejects_direct_sql(self):
        with self.assertRaises(ReplyGuardError): guard_adaptive_reply(POLICY,'SELECT id FROM x')
    def test_rejects_claimed_test_success(self):
        with self.assertRaises(ReplyGuardError): guard_adaptive_reply(POLICY,'Your SQL passed all tests.')
    def test_rejects_fabricated_execution(self):
        with self.assertRaises(ReplyGuardError): guard_adaptive_reply(POLICY,'I executed your SQL and got the right answer.')
    def test_rejects_scoring(self):
        with self.assertRaises(ReplyGuardError): guard_adaptive_reply(POLICY,'You scored 100% on the SQL.')
    def test_rejects_answer_disclosure(self):
        with self.assertRaises(ReplyGuardError): guard_adaptive_reply(POLICY,'Here is the solution:')
    def test_rejects_unapproved_hint(self):
        with self.assertRaises(ReplyGuardError): guard_adaptive_reply(POLICY,'Use ROW_NUMBER() to solve it.')
    def test_chinese_fabricated_pass_denied(self):
        with self.assertRaises(ReplyGuardError): guard_adaptive_reply(POLICY, '你的SQL已经全部通过')
    def test_chinese_answer_and_grade_denied(self):
        for phrase in ['标准答案是：', '你得分100分']:
            with self.subTest(phrase=phrase), self.assertRaises(ReplyGuardError): guard_adaptive_reply(POLICY, phrase)
    def test_model_json_score_authority_denied(self):
        with self.assertRaises(ReplyGuardError): guard_adaptive_reply(POLICY, '{"technical_score": 100}')
    def test_false_authority_denied(self):
        for change in [{'max_hint_level':'H2'},{'technical':'PASSED'}, {'receipt_status':'PASSED'}, {'execution_receipt_ref':'receipt-a'}, {'rule_id':'S03C_EVIDENCE_ONLY'}]:
            with self.subTest(change=change), self.assertRaises(ReplyGuardError):
                guard_adaptive_reply(dict(POLICY, **change), 'What else would you test?')
    def test_question_sha_bound(self):
        with self.assertRaises(ReplyGuardError): guard_adaptive_reply(dict(POLICY,question_sha256='bad'), 'Question?')
    def test_empty_and_oversized_denied(self):
        for reply in ['', 'x'*2001, 'h'*8001, 'bad\x00']:
            with self.subTest(reply=repr(reply[:12])), self.assertRaises(ReplyGuardError): guard_adaptive_reply(POLICY, reply)
    def test_legacy_policy_skipped_at_host_callsite(self):
        path=Path(__file__).resolve().parents[1]/'tia_runtime/app_host.py'
        source=path.read_text()
        self.assertIn("self._adaptive_replay_mode in (None, REPLY_GUARD_VERSION)",source)
        self.assertIn("pending.get('policy', {}).get('rule_id') == 'E4C2B1_HOST_DECISION'", source)
        self.assertIn("entry['reply_guard_version'] = REPLY_GUARD_VERSION",source)
        self.assertIn("item['action'] != 'native_commit_preview'",source)
        self.assertIn('self._live_controller.commit_native_reply(**params)',source)
    def test_native_cancel_after_rejected_commit(self):
        path=Path(__file__).resolve().parents[1]/'native/main.swift'
        source=path.read_text()
        self.assertIn('ADAPTIVE_REPLY_NOT_AUTHORIZED',source)
        self.assertIn('self.cancelPrepared(error:',source)
    def test_guard_version(self): self.assertEqual(GUARD_VERSION, 'E4C2B2A')


class NativeCommitIntegrationTests(unittest.IsolatedAsyncioTestCase):
    """Exercise actual trusted Host commands; requires the full macOS worktree.

    These do not open WebKit, activate a provider, run SQL or use credentials.
    """
    async def asyncSetUp(self):
        import tempfile
        from tia_runtime.app_host import TutorialHost
        self.temp = tempfile.TemporaryDirectory()
        self.tick = 100.0
        self.counter = 0
        self.host = await TutorialHost.open(self.temp.name, clock=lambda: self.tick)

    async def asyncTearDown(self):
        self.host.close()
        self.temp.cleanup()

    async def call(self, action, params=None, *, ok=True):
        self.counter += 1
        response = await self.host.handle({'id': 'c2b2-' + str(self.counter),
                                           'action': action, 'params': params or {}})
        self.assertEqual(response['ok'], ok, response)
        self.tick += 1
        return response

    @staticmethod
    def commitment(prepared, reply):
        return {k: prepared[k] for k in ('transaction_id', 'request_id', 'generation')} | {
            'reply': {'reply': reply}, 'model': 'synthetic-test-model',
            'usage': {'input_tokens': 15, 'output_tokens': 8, 'total_tokens': 23}}

    async def verify_and_prepare_reply(self):
        await self.call('choose_real')
        first = await self.call('native_prepare_preview', {'request_id': 'initial',
            'generation': 'offline-generation', 'operation': 'verify', 'kind': 'clarify',
            'text': '', 'mechanism': 'STRICT_CHALLENGING'})
        await self.call('native_commit_preview', self.commitment(first['prepared'],
            'Please describe how you interpret the original task.'))
        second = await self.call('native_prepare_preview', {'request_id': 'second',
            'generation': 'offline-generation', 'operation': 'reply', 'kind': 'plan',
            'text': 'I would filter the rows first.', 'mechanism': 'STRICT_CHALLENGING'})
        return second['prepared']

    async def test_rejected_native_commit_keeps_candidate_and_no_model_reply(self):
        prepared = await self.verify_and_prepare_reply()
        response = await self.call('native_commit_preview',
            self.commitment(prepared, 'Your SQL passed all tests.'), ok=False)
        self.assertEqual(response['error'], 'ADAPTIVE_REPLY_NOT_AUTHORIZED')
        preview = self.host.state()['live_preview']
        self.assertEqual(preview['candidate_turns_used'], 1)
        self.assertEqual(preview['verified_response_count'], 1)
        self.assertTrue(preview['pending'])
        await self.call('native_cancel_preview')
        self.assertFalse(self.host.state()['live_preview']['pending'])
        self.assertFalse(any('reply_guard_version' in entry for entry in self.host._journal))

    async def test_safe_commit_is_versioned_and_survives_restart(self):
        prepared = await self.verify_and_prepare_reply()
        await self.call('native_commit_preview',
            self.commitment(prepared, 'What boundary case would you test first?'))
        records = [x for x in self.host._journal if x['action'] == 'native_commit_preview']
        self.assertEqual(records[-1]['reply_guard_version'], GUARD_VERSION)
        self.host.close()
        from tia_runtime.app_host import TutorialHost
        self.host = await TutorialHost.open(self.temp.name, clock=lambda: self.tick)
        self.assertIsNone(self.host.state()['recovery_error'])
        self.assertEqual(self.host.state()['live_preview']['verified_response_count'], 2)

    async def test_pre_upgrade_reply_without_guard_marker_still_replays(self):
        prepared = await self.verify_and_prepare_reply()
        await self.call('native_commit_preview',
            self.commitment(prepared, 'What boundary case would you test first?'))
        document = self.host.store.read()
        changed = False
        for entry in document['journal']:
            if entry['action'] == 'native_commit_preview' and 'reply_guard_version' in entry:
                del entry['reply_guard_version']
                changed = True
        self.assertTrue(changed)
        from tia_runtime.app_host import digest, TutorialHost
        document['document_sha256'] = digest({k:v for k,v in document.items() if k != 'document_sha256'})
        self.host.store.write(document)
        self.host.close()
        self.host = await TutorialHost.open(self.temp.name, clock=lambda: self.tick)
        self.assertIsNone(self.host.state()['recovery_error'])
        self.assertEqual(self.host.state()['live_preview']['verified_response_count'], 2)
