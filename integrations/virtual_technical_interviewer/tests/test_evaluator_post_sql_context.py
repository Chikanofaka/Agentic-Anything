"""Only aggregate supplemental SQL observations enter an evaluator request."""
import unittest
from tia_runtime import native_evaluator as ev
from test_native_evaluator import source


class EvaluatorPostSQLContextTests(unittest.TestCase):
    def test_post_interview_cases_are_named_and_source_data_is_not_exposed(self):
        plan = source(); plan['continuity_policy'] = 'tia-continuity/v3'
        plan['questions'][0]['reference_answer'] = 'PRIVATE_ORACLE_SQL'
        card = ev._card(plan)
        card['questions'][0]['accuracy'].update(
            reason='POST_INTERVIEW_REVIEWED_CASES_ONLY', fixture_passed=2, fixture_total=3)
        packet = ev._context(plan, 0, 'en', ev._effective_profile(plan), card)
        self.assertEqual(packet['local_execution']['fixture_passed'], 2)
        self.assertEqual(packet['local_execution']['fixture_total'], 3)
        self.assertEqual(packet['local_execution']['execution_time'], 'AFTER_INTERVIEW')
        self.assertNotIn('PRIVATE_ORACLE_SQL', ev._canonical(packet))
        self.assertEqual(set(packet['local_execution']), {
            'status', 'reason', 'candidate_alias', 'fixture_passed', 'fixture_total', 'execution_time'})

    def test_original_execution_packet_unchanged_without_post_interview_receipt(self):
        for continuity in (None, 'tia-continuity/v2', 'tia-continuity/v3'):
            plan = source()
            if continuity:
                plan['continuity_policy'] = continuity
            packet = ev._context(plan, 0, 'en', ev._effective_profile(plan), ev._card(plan))
            self.assertEqual(set(packet['local_execution']), {'status', 'reason', 'candidate_alias'})


if __name__ == '__main__': unittest.main()
