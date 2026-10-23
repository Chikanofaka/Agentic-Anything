"""S03-E3D-P1: three pasted Pandas tasks are live-rehearsal eligible, unscored.

No network, API key, or Pandas code execution is involved in this contract test.
"""
import copy
import tempfile
import unittest

from tia_runtime.app_host import TutorialHost


PASTES = [
    """1393. Capital Gain/Loss
Solved
Medium
Pandas Schema
Table: Stocks
| stock_name | operation | operation_day | price |
| A | Buy | 1 | 10 |
Each record describes a stock transaction.
Write a solution to calculate the capital gain/loss for each stock.
Example 1:
Input:
Stocks table:
| A | Buy | 1 | 10 |
Output:
| stock_name | capital_gain_loss |
| A | 5 |
""",
    """1204. Last Person to Fit in the Bus
Attempted
Easy
Pandas Schema
Table: Queue
| person_id | person_name | weight | turn |
| 1 | Alice | 200 | 1 |
The bus carries at most 1000 kg.
Write a solution to find the last passenger who fits.
Example 1:
Input:
Queue table:
| 1 | Alice | 200 | 1 |
Output:
| person_name |
| Alice |
""",
    """1174. Immediate Food Delivery II
Solved
Topics
Companies
Table: Delivery
| delivery_id | customer_id | order_date | customer_pref_delivery_date |
| 1 | 1 | 2019-08-01 | 2019-08-02 |
Each customer has one first order.
Write a solution to calculate the percentage of immediate first orders.
Example 1:
Input:
Delivery table:
| 1 | 1 | 2019-08-01 | 2019-08-02 |
Output:
| immediate_percentage |
| 50.00 |
""",
]


class PandasPracticeGateTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.host = await TutorialHost.open(self.temp.name)
        self.serial = 0

    async def asyncTearDown(self):
        self.host.close()
        self.temp.cleanup()

    async def cmd(self, action, params=None):
        self.serial += 1
        reply = await self.host.handle({'id': f'pandas-e4-{self.serial}',
                                        'action': action, 'params': params or {}})
        self.assertTrue(reply['ok'], reply.get('error'))
        return reply['state']

    async def test_mixed_difficulty_pandas_three_question_practice(self):
        await self.cmd('choose_real')
        await self.cmd('setup_continue')
        await self.cmd('setup_config', {'config': {
            'technical_environment': 'PANDAS', 'duration_minutes': 45,
            'difficulty': 'HARD', 'question_source': 'BYOQ',
            'interviewer_mechanism': 'STRICT_CHALLENGING'}})
        for index, raw in enumerate(PASTES):
            state = await self.cmd('setup_question_set', {
                'index': index, 'source': 'LEETCODE', 'raw_text': raw})
            item = state['setup_questions'][index]
            self.assertIn('PANDAS', item['fields']['environment'])
            self.assertIn('Table:', item['fields']['schema'])
            self.assertTrue(item['fields']['task'])
            state = await self.cmd('setup_question_confirm', {
                'index': index, 'raw_sha256': item['raw_sha256'],
                'fields': copy.deepcopy(item['fields'])})
            self.assertTrue(state['setup_questions'][index]['practice_eligible'])
        # No Hard-only gate on practice progression, even though the legacy
        # formal-exam configuration still truthfully carries HARD.
        state = await self.cmd('setup_questions_finish')
        self.assertEqual(state['screen'], 'MECHANISM')
        state = await self.cmd('setup_mechanism', {'mechanism': 'STRICT_CHALLENGING'})
        self.assertEqual(state['screen'], 'REVIEW')
        state = await self.cmd('rehearsal_start')
        self.assertEqual(state['screen'], 'API_PORTAL')
        self.assertEqual(state['rehearsal']['question_count'], 3)
        self.assertFalse(state['rehearsal']['formal_exam_authorized'])
        self.assertEqual(state['rehearsal']['technical'], 'NOT_SCORED')
        self.assertEqual(state['rehearsal']['communication'], 'NOT_SCORED')
        self.assertEqual(state['rehearsal']['execution'], 'NOT_RUN')
        self.assertEqual(state['api_requests'], 0)

    async def test_formal_launch_cannot_be_silently_unlocked(self):
        await self.cmd('choose_real')
        await self.cmd('setup_continue')
        self.serial += 1
        reply = await self.host.handle({'id': f'pandas-e4-{self.serial}',
            'action': 'setup_launch', 'params': {}})
        self.assertFalse(reply['ok'])
        self.assertIn(reply['error'], ('INVALID_TRANSITION', 'LAUNCH_BLOCKED'))
