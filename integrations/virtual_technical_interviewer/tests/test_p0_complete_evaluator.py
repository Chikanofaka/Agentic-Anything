"""Complete chronological evidence for new continuity policy; no provider calls."""
import copy
import hashlib
import json
import unittest
from tia_runtime import native_evaluator as ev
from tia_runtime import evaluator_p0_guards_v2 as gates
from test_native_evaluator import source, proposal, commitment, RID, GEN
from test_evaluator_p0_criterion_gates import event


class CompleteEvaluatorTests(unittest.TestCase):
    def plan(self):
        p = source(); p['continuity_policy'] = 'tia-continuity/v3'
        return p

    def test_many_turns_all_chronological_without_replacement_count_cap(self):
        p = self.plan()
        turns = []
        for n in range(70):
            turns += [event('candidate', 'clarify', f'c{n}', f'My plan is to filter dates then group. Turn {n}.'),
                      event('interviewer', 'reply', f'i{n}', f'Explain the filter requirement. Turn {n}.')]
        p['results'][0]['session']['events'] = turns
        _, spec = ev.prepare_native_evaluator(p, RID, GEN, 'en', 0)
        packet = json.loads(spec['input'])
        self.assertEqual(packet['evidence_policy'], 'tia-evaluator-evidence/v2')
        self.assertEqual(packet['continuity_policy'], 'tia-continuity/v3')
        self.assertEqual([e['event_id'] for e in packet['conversation']], [e['id'] for e in turns])
        self.assertEqual(len(packet['conversation']), 140)
        self.assertTrue(packet['evidence_limits']['conversation_complete'])
        self.assertFalse(any(e['excerpt_truncated'] for e in packet['conversation']))
        self.assertGreater(len(spec['input'].encode()), 16000)
        self.assertLessEqual(len(spec['input'].encode()), ev.COMPLETE_CONTEXT_LIMIT)

    def test_long_public_source_and_long_utterance_retained(self):
        p = self.plan()
        p['questions'][0]['statement'] = '需求文本' * 800
        p['results'][0]['session']['events'][0]['payload']['text'] = '我先确认需求和约束。' * 600
        _, spec = ev.prepare_native_evaluator(p, RID, GEN, 'zh', 0)
        packet = json.loads(spec['input'])
        self.assertEqual(packet['question']['statement'], p['questions'][0]['statement'])
        first = packet['conversation'][0]
        self.assertEqual(first['excerpt'], p['results'][0]['session']['events'][0]['payload']['text'])
        self.assertEqual(first['text_sha256'], hashlib.sha256(first['excerpt'].encode()).hexdigest())

    def test_capacity_failure_never_truncates_or_mutates_closed_record(self):
        p = self.plan()
        p['results'][0]['session']['events'] = [event('candidate', 'plan', f'c{n}', 'My plan is ' + 'x' * 10000) for n in range(40)]
        original = copy.deepcopy(p)
        with self.assertRaisesRegex(ev.NativeEvaluatorError, 'EVALUATOR_CONTEXT_INCOMPLETE'):
            ev.prepare_native_evaluator(p, RID, GEN, 'en', 0)
        self.assertEqual(p, original)

    def test_legacy_count_policy_and_identity_unchanged(self):
        p = source()
        self.assertEqual(ev._p0_code_sources(p), ev.P0_V5_CODE_SOURCES)
        p['results'][0]['session']['events'] = [event('candidate', 'plan', f'c{n}', 'My plan is to group.') for n in range(17)]
        with self.assertRaisesRegex(ev.NativeEvaluatorError, 'EVALUATOR_CONTEXT_INCOMPLETE'):
            ev.prepare_native_evaluator(p, RID, GEN, 'en', 0)

    def test_existing_v2_prepares_and_commits_exact_shipped_evaluator_context(self):
        # Golden values independently generated from git d3b7f8c's evaluator
        # against this synthetic source. Existing v2 is not new policy v3.
        for policy in (None, 'tia-continuity/v2'):
            p = source()
            if policy:
                p['continuity_policy'] = policy
            pending, spec = ev.prepare_native_evaluator(p, RID, GEN, 'en', 0)
            self.assertEqual(hashlib.sha256(spec['input'].encode()).hexdigest(),
                             '84d67a447cc363932d1faba8219ab78d4bf9c309c80582f77b525a62ba81f58d')
            packet = json.loads(spec['input'])
            self.assertNotIn('conversation', packet)
            self.assertNotIn('continuity_policy', packet)
            value = proposal(spec, {'T01': 2, 'C01': 2})
            artifact = ev.commit_native_evaluator(p, pending, commitment(pending, value))
            self.assertEqual(artifact['sha256'],
                             '8f13cfe056252aa72f0530521f8b1e9a541e9011417f8c74ebe35f0811e4325a')
            report = ev.build_evaluator_report(p, {'0': artifact})
            self.assertEqual(report['questions'][0]['assessment'], artifact)
            self.assertEqual(ev._p0_code_sources(p), ev.P0_V5_CODE_SOURCES)

    def test_existing_v2_keeps_legacy_capacity_contract(self):
        p = source(); p['continuity_policy'] = 'tia-continuity/v2'
        p['results'][0]['session']['events'] = [
            event('candidate', 'plan', f'c{n}', 'My plan is to group.') for n in range(17)]
        with self.assertRaisesRegex(ev.NativeEvaluatorError, 'EVALUATOR_CONTEXT_INCOMPLETE'):
            ev.prepare_native_evaluator(p, RID, GEN, 'en', 0)

    def test_v3_commit_binds_complete_packet_and_all_eleven_criteria(self):
        p = self.plan()
        pending, spec = ev.prepare_native_evaluator(p, RID, GEN, 'en', 0)
        value = proposal(spec, {'T02': 2, 'T03': 2})
        artifact = ev.commit_native_evaluator(p, pending, commitment(pending, value))
        report = ev.build_evaluator_report(p, {'0': artifact})
        self.assertEqual(len(report['questions'][0]['dimensions']), 11)
        self.assertEqual(artifact['overall_grade'], 'NOT_SCORED')
        self.assertEqual(artifact['decision_trace']['input_excerpt_truncated_count'], 0)
        self.assertEqual(report['questions'][0]['assessment']['sha256'], artifact['sha256'])

    def test_v3_bilingual_clarify_voice_labels_support_relevant_evidence(self):
        rows = [dict(alias='e1', event_id='a', kind='clarify', position=1, excerpt='我先确认需求和约束，然后按日期分组。'),
                dict(alias='e2', event_id='c', kind='clarify', position=3, excerpt='我现在修改日期分组，按你的建议检查日期。')]
        replies = [dict(event_id='b', position=2, excerpt='你的日期分组需要修改，请检查日期。')]
        self.assertEqual(gates.eligible_aliases('C01', rows, replies, {}), ['e1'])
        self.assertEqual(gates.eligible_aliases('C05', rows, replies, {}), ['e2'])

    def test_no_testing_statement_or_code_only_cannot_earn_voice_points(self):
        code = dict(alias='e1', event_id='c', kind='implement', position=1, excerpt='```sql\nSELECT person_name FROM Queue\n```')
        for criterion in ('C01', 'C02', 'C03', 'C04', 'T04'):
            self.assertEqual(gates.eligible_aliases(criterion, [code], [], {}), [])
        denial = dict(code, kind='clarify', excerpt='I have not yet tested or run this query.')
        self.assertEqual(gates.eligible_aliases('T04', [denial], [], {}), [])
        self.assertTrue(gates.reason_self_contradicts('Some debugging hints implied but no explicit repair or testing details'))
        self.assertTrue(gates.reason_self_contradicts('没有明确测试证据。'))

if __name__ == '__main__': unittest.main()
