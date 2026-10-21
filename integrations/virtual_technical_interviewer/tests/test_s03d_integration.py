"""S03-D end-to-end host + preview contracts with synthetic content and no HTTP."""
import copy
import hashlib
import json
import tempfile
import unittest

from tia_runtime.app_host import TutorialHost
from test_freeform_import import LC, HR

class SmartBYOQTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.host = await TutorialHost.open(self.dir.name)
        self.counter = 0

    async def asyncTearDown(self):
        self.host.close()
        self.dir.cleanup()

    async def call(self, action, params=None, ok=True):
        self.counter += 1
        reply = await self.host.handle({'id': 's03d-' + str(self.counter),
                                        'action': action, 'params': params or {}})
        self.assertEqual(reply['ok'], ok, reply.get('error'))
        return reply

    async def enter_byoq(self):
        await self.call('choose_real')
        await self.call('setup_continue')
        await self.call('setup_config', {'config': {'technical_environment': 'POSTGRESQL',
                      'duration_minutes': 45, 'difficulty': 'HARD', 'question_source': 'BYOQ',
                      'interviewer_mechanism': 'STRICT_CHALLENGING'}})

    async def set_question(self, text=LC, index=0, source='LEETCODE'):
        return await self.call('setup_question_set', {'index': index, 'raw_text': text, 'source': source})

    async def confirmed(self, text=LC, index=0):
        r = (await self.set_question(text, index))['state']['setup_questions'][index]
        return await self.call('setup_question_confirm', {'index': index, 'raw_sha256': r['raw_sha256'],
                    'fields': copy.deepcopy(r['fields'])})

    async def test_import_and_confirm_preserves_drafts_and_does_not_unlock_formal(self):
        await self.enter_byoq()
        s = (await self.confirmed())['state']
        review = s['setup_questions'][0]
        self.assertEqual(review['extraction']['title']['id'], '3521')
        self.assertTrue(review['human_confirmed'])
        self.assertTrue(review['practice_eligible'])
        self.assertFalse(review['grading_authorized'])
        self.assertIn('QUESTION_COUNT_MISMATCH', s['setup_blockers'])
        self.assertIn('QUESTION_DIFFICULTY_NOT_HARD', s['setup_blockers'])
        self.assertEqual(s['screen'], 'QUESTION_SOURCE')
        await self.call('setup_questions_finish', ok=False)

    async def test_raw_8192_exact_bound_and_worker_safe(self):
        await self.enter_byoq()
        # Test actual UTF-8 byte bound without bypassing host validation.
        value = '字' * 2730
        await self.set_question(value)
        await self.call('setup_question_set', {'index': 0, 'raw_text': '字' * 2731, 'source': 'LEETCODE'}, ok=False)
        self.assertEqual(self.host.state()['setup_questions'][0]['raw_input'], value)

    async def test_stale_confirmation_rejected_without_state_change(self):
        await self.enter_byoq()
        review = (await self.set_question())['state']['setup_questions'][0]
        edited = copy.deepcopy(review['fields'])
        await self.call('setup_question_set', {'index': 0, 'raw_text': LC + '\nNew constraint', 'source': 'LEETCODE'})
        await self.call('setup_question_confirm', {'index': 0, 'fields': edited,
                        'raw_sha256': review['raw_sha256']}, ok=False)
        self.assertFalse(self.host.state()['setup_questions'][0]['human_confirmed'])

    async def test_image_only_text_blocks_practice_until_manual_schema(self):
        await self.enter_byoq()
        review = (await self.set_question(HR, source='HACKERRANK'))['state']['setup_questions'][0]
        self.assertTrue(any(i['code'] == 'IMAGE_SCHEMA_NOT_IMPORTED' for i in review['extraction_issues']))
        await self.call('setup_question_confirm', {'index': 0, 'raw_sha256': review['raw_sha256'],
                        'fields': review['fields']}, ok=False)
        self.assertFalse(self.host.state()['setup_questions'][0]['human_confirmed'])

    async def test_confirmed_question_used_by_real_model_prepare_and_frozen_on_restart(self):
        await self.enter_byoq()
        review = (await self.confirmed())['state']['setup_questions'][0]
        await self.call('practice_start', {'index': 0, 'content_sha256': review['content_sha256']})
        self.assertEqual(self.host.state()['screen'], 'API_PORTAL')
        prepared = await self.call('native_prepare_preview', {
            'request_id': 'req-d1', 'generation': 'gen-d1', 'operation': 'verify',
            'kind': 'clarify', 'text': '', 'mechanism': 'STRICT_CHALLENGING'})
        context = json.loads(prepared['prepared']['input'])
        self.assertIn('pairs purchased', context['question']['statement'])
        self.assertIn('ProductPurchases', context['question']['schema'])
        self.assertTrue(context['question']['practice_only'])
        self.assertNotIn('sk-', prepared['prepared']['input'])
        await self.call('native_commit_preview', {
            'transaction_id': prepared['prepared']['transaction_id'], 'request_id': 'req-d1',
            'generation': 'gen-d1', 'reply': {'reply': 'What would you clarify first?'},
            'model': 'synthetic-model', 'usage': None})
        self.assertEqual(self.host.state()['live_preview']['execution_status'], 'NOT_RUN')
        self.assertEqual(self.host.state()['live_preview']['technical'], 'NOT_SCORED')
        await self.call('preview_close')
        old = self.host.state()['live_preview']['session']['receipt']['sha256']
        self.host.close()
        self.host = await TutorialHost.open(self.dir.name)
        self.assertEqual(self.host.state()['live_preview']['session']['receipt']['sha256'], old)
        self.assertEqual(self.host.state()['live_preview']['question']['content_sha256'], review['content_sha256'])

    async def test_attempt_to_forge_formal_authority_rejected(self):
        await self.enter_byoq()
        r = (await self.set_question())['state']['setup_questions'][0]
        vals = copy.deepcopy(r['fields'])
        vals['grading_authorized'] = True
        await self.call('setup_question_confirm', {'index': 0, 'raw_sha256': r['raw_sha256'], 'fields': vals}, ok=False)

    async def test_per_slot_sequence_and_restore(self):
        await self.enter_byoq()
        await self.call('setup_question_set', {'index': 2, 'raw_text': LC, 'source': 'LEETCODE'}, ok=False)
        await self.confirmed()
        second = (await self.set_question(LC.replace('3521.', '3522.').replace('product pairs','different pairs'),index=1))['state']['setup_questions'][1]
        self.assertEqual(len(self.host.state()['setup_questions']), 2)
        self.host.close()
        self.host = await TutorialHost.open(self.dir.name)
        self.assertEqual(len(self.host.state()['setup_questions']), 2)
        self.assertTrue(self.host.state()['setup_questions'][0]['human_confirmed'])

if __name__ == '__main__': unittest.main()

class WorkerEnvelopeTests(unittest.TestCase):
    def test_exact_8192_byte_raw_per_slot_fits_original_32768_ipc(self):
        import pathlib
        import subprocess
        import sys
        root = pathlib.Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as data_dir:
            configs = {'technical_environment': 'POSTGRESQL', 'duration_minutes': 45,
                       'difficulty': 'HARD', 'question_source': 'BYOQ',
                       'interviewer_mechanism': 'STRICT_CHALLENGING'}
            commands = [
                ('choose_real', {}), ('setup_continue', {}), ('setup_config', {'config': configs}),
                ('setup_question_set', {'index': 0, 'source': 'LEETCODE', 'raw_text': '字'*2730}),
            ]
            payload = ''.join(json.dumps({'id': f'envelope-{i}', 'action': act, 'params': args},
                                         ensure_ascii=True)+'\n' for i, (act, args) in enumerate(commands))
            self.assertLess(max(len(s.encode()) for s in payload.splitlines()), 32768)
            proc = subprocess.run([sys.executable, '-B', '-u', '-m', 'tia_runtime.app_host',
                                   '--data-dir', data_dir], cwd=root, text=True, input=payload,
                                  capture_output=True, timeout=15)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            result = [json.loads(line) for line in proc.stdout.splitlines()]
            self.assertTrue(all(item['ok'] for item in result), [item.get('error') for item in result])
            self.assertEqual(result[-1]['state']['setup_questions'][0]['raw_input'], '字'*2730)
            self.assertEqual(result[-1]['state']['setup_questions'][0]['execution_status'], 'UNVERIFIED')
