"""No HTTP: model must receive truthful nonexecution provenance for all rehearsal turns."""
import hashlib
import json
import tempfile
import unittest

from tia_runtime.app_host import TutorialHost


class TruthfulInterviewPromptTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.host = await TutorialHost.open(self.folder.name)
        self.serial = 0

    async def asyncTearDown(self):
        self.host.close()
        self.folder.cleanup()

    async def call(self, action, params=None):
        self.serial += 1
        response = await self.host.handle({
            'id': 'truth-' + str(self.serial), 'action': action,
            'params': params or {},
        })
        self.assertTrue(response['ok'], response)
        return response

    async def prepare(self, operation, kind='clarify', text=''):
        return (await self.call('native_prepare_preview', {
            'mechanism': 'STRICT_CHALLENGING',
            'request_id': 'request-' + str(self.serial + 1),
            'generation': 'generation-1',
            'operation': operation, 'kind': kind, 'text': text,
        }))['prepared']

    def check(self, prepared):
        instruction = prepared['instructions']
        context = json.loads(prepared['input'])
        self.assertIn('NO_VERIFIED_OUTPUT', instruction)
        self.assertIn('Never ask for the *actual observed* output', instruction)
        self.assertIn('candidate-reported and unverified', instruction)
        self.assertIn('hypothetical and not an official test', instruction)
        self.assertEqual(context['execution_status'], 'NOT_RUN')
        self.assertEqual(context['verified_execution_results'], [])
        self.assertEqual(hashlib.sha256(instruction.encode()).hexdigest(),
                         prepared['prompt_sha256'])
        self.assertNotIn('api_key', prepared['input'])

    async def test_first_question_cannot_assume_execution(self):
        await self.call('choose_real')
        self.check(await self.prepare('verify'))

    async def test_candidate_sql_reply_cannot_assume_actual_output(self):
        await self.call('choose_real')
        first = await self.prepare('verify')
        await self.call('native_commit_preview', {
            'transaction_id': first['transaction_id'],
            'request_id': first['request_id'], 'generation': first['generation'],
            'reply': {'reply': 'Describe your approach.'},
            'model': 'test-model', 'usage': None,
        })
        second = await self.prepare('reply', 'implement',
                                    'SELECT person_name FROM Queue;')
        self.check(second)
        self.assertEqual(json.loads(second['input'])['candidate_events'][0]['kind'], 'implement')
        self.assertEqual(self.host.state()['live_preview']['execution_status'], 'NOT_RUN')


if __name__ == '__main__':
    unittest.main()
