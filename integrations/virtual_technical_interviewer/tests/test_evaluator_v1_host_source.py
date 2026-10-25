"""E4D-02C1A: frozen real-shape rehearsal -> 12D semantic evidence test gates."""
import copy
import hashlib
import json
import unittest
from tia_runtime.evaluator_v1_semantic_contract import DIMENSIONS, PROPOSAL_SCHEMA
from tia_runtime.evaluator_v1_host_source import (
    HostSourceError, compile_host_source, verify_source_still_current,
    review_untrusted_proposal_json, prepare_host_only_packet,
)


def event(identifier, kind, text, actor='candidate', provenance=None):
    item = {'id': identifier, 'kind': kind, 'actor': actor,
            'payload': {'text': text}}
    if provenance is not None:
        item['provenance'] = provenance
        item['payload']['operation'] = 'reply'
    return item


def sample():
    questions = [{'title': f'Synthetic Question {i+1}', 'content_sha256': str(i+1)*64}
                 for i in range(3)]
    results = []
    for i, question in enumerate(questions):
        events = [event(f'fake-q{i+1}:3', 'clarify', 'Can the date repeat?'),
                  event(f'fake-q{i+1}:4', 'reply', 'Use the earliest event.', 'interviewer', 'LIVE_MODEL'),
                  event(f'fake-q{i+1}:5', 'implement', 'SELECT 1;')]
        results.append({'index': i, 'outcome': 'SUBMITTED_UNVERIFIED',
                        'question_sha256': question['content_sha256'],
                        'session': {'events': events}})
    return {'status': 'COMPLETE', 'questions': questions, 'results': results}, [{'action': 'rehearsal_submit', 'seq': 1}]


def proposal_for(source):
    return {'schema': PROPOSAL_SCHEMA, 'role': 'evaluator',
            'source_sha256': source['source_sha256'],
            'dimensions': [{'id': dim, 'anchor': 2 if dim == 'T2' else None,
                            'evidence_ids': [source['evidence'][2]['id']] if dim == 'T2' else [],
                            'reason': 'Demonstration annotation only; semantic quality not established.'
                            if dim == 'T2' else 'No demonstrated independent result in this sample.',
                            'confidence': 'LOW' if dim == 'T2' else 'NOT_ASSESSED'}
                           for dim in DIMENSIONS],
            'summary': 'Illustrative frozen-record protocol demonstration, not an actual model call.'}


class HostAdapterTests(unittest.TestCase):
    def setUp(self):
        self.plan, self.journal = sample()

    def bad(self, code, fn, *args, **kwargs):
        with self.assertRaises(HostSourceError) as ctx:
            fn(*args, **kwargs)
        self.assertEqual(ctx.exception.code, code)

    def test_real_shape_events_read_and_private_context(self):
        packet = compile_host_source(self.plan, self.journal, 0)
        self.assertEqual(len(packet['evidence']), 3)
        self.assertEqual(packet['evidence'][0]['id'], 'fake-q1:3')
        self.assertEqual(packet['evidence'][1]['actor'], 'interviewer')
        self.assertEqual(packet['evidence'][2]['kind'], 'implement')

    def test_three_sources_each_isolated(self):
        for i in range(3):
            s = compile_host_source(self.plan, self.journal, i)
            self.assertEqual(s['question_index'], i)
            self.assertTrue(all(e['question_index'] == i for e in s['evidence']))
            self.assertTrue(all(f'q{i+1}:' in e['id'] for e in s['evidence']))

    def test_source_deterministic_and_non_mutating(self):
        frozen = copy.deepcopy((self.plan, self.journal))
        a = compile_host_source(self.plan, self.journal, 0)
        b = compile_host_source(self.plan, self.journal, 0)
        self.assertEqual(a, b)
        self.assertEqual((self.plan, self.journal), frozen)

    def test_validate_source_success(self):
        src = compile_host_source(self.plan, self.journal, 0)
        self.assertTrue(verify_source_still_current(self.plan, self.journal, src))

    def test_open_rehearsal_rejected(self):
        self.plan['status'] = 'ACTIVE'
        self.bad('REHEARSAL_NOT_FROZEN_COMPLETE', compile_host_source, self.plan, self.journal, 0)

    def test_expired_session_not_evaluated_as_completed(self):
        self.plan['status'] = 'TIMED_OUT'
        self.bad('REHEARSAL_NOT_FROZEN_COMPLETE', compile_host_source, self.plan, self.journal, 0)

    def test_boolean_question_index_rejected(self):
        self.bad('INVALID_QUESTION_INDEX', compile_host_source, self.plan, self.journal, True)

    def test_unknown_scenario_rejected(self):
        self.bad('INVALID_INTERVIEW_SCENARIO', compile_host_source, self.plan, self.journal, 0, scenario='UNTRUSTED_ROLE')

    def test_missing_journal_is_rejected(self):
        self.bad('TRUSTED_JOURNAL_REQUIRED', compile_host_source, self.plan, [], 0)

    def test_changed_journal_invalidates_source(self):
        src = compile_host_source(self.plan, self.journal, 0)
        self.journal.append({'seq': 2, 'action': 'new'})
        self.bad('STALE_SEMANTIC_SOURCE', verify_source_still_current, self.plan, self.journal, src)

    def test_changed_candidate_code_invalidates(self):
        src = compile_host_source(self.plan, self.journal, 0)
        self.plan['results'][0]['session']['events'][2]['payload']['text'] = 'SELECT 999;'
        self.bad('STALE_SEMANTIC_SOURCE', verify_source_still_current, self.plan, self.journal, src)

    def test_changed_question_invalidates(self):
        src = compile_host_source(self.plan, self.journal, 0)
        self.plan['questions'][0]['title'] = 'Different'
        self.bad('STALE_SEMANTIC_SOURCE', verify_source_still_current, self.plan, self.journal, src)

    def test_cross_question_result_slot_rejected(self):
        self.plan['results'][0]['index'] = 2
        self.bad('CROSS_QUESTION_RESULT_INDEX', compile_host_source, self.plan, self.journal, 0)

    def test_cross_question_source_digest_rejected(self):
        self.plan['results'][0]['question_sha256'] = 'a'*64
        self.bad('CROSS_QUESTION_SOURCE_HASH', compile_host_source, self.plan, self.journal, 0)

    def test_wrong_candidate_kind_rejected(self):
        self.plan['results'][0]['session']['events'][0]['kind'] = 'score'
        self.bad('UNKNOWN_CANDIDATE_ACTION', compile_host_source, self.plan, self.journal, 0)

    def test_duplicate_event_rejected(self):
        self.plan['results'][0]['session']['events'].append(copy.deepcopy(self.plan['results'][0]['session']['events'][0]))
        self.bad('DUPLICATE_OR_INVALID_EVENT_ID', compile_host_source, self.plan, self.journal, 0)

    def test_oversize_history_rejected_not_silently_truncated(self):
        e = self.plan['results'][0]['session']['events']
        for i in range(32):
            e.append(event(f'extra:{i}', 'test', 'Test case'))
        self.bad('EVIDENCE_TRUNCATION_NOT_ALLOWED', compile_host_source, self.plan, self.journal, 0)

    def test_short_utf8_excerpt_with_sha(self):
        self.plan['results'][0]['session']['events'][2]['payload']['text'] = '😀'*190
        src = compile_host_source(self.plan, self.journal, 0)
        evidence = src['evidence'][2]
        self.assertLessEqual(len(evidence['excerpt'].encode('utf-8')), 600)
        self.assertEqual(evidence['excerpt_sha256'], hashlib.sha256(evidence['excerpt'].encode()).hexdigest())

    def test_no_claim_that_hash_is_a_signature(self):
        result = prepare_host_only_packet(self.plan, self.journal, 0)
        self.assertFalse(result['can_submit_provider_request'])
        self.assertIsNone(result['score'])
        self.assertEqual(result['paid_calls'], 0)
        self.assertEqual(result['status'], 'HOST_ONLY_NOT_NATIVE_AUTHORIZED')

    def test_model_json_review_passes_with_manual_flag(self):
        src = compile_host_source(self.plan, self.journal, 0)
        r = review_untrusted_proposal_json(self.plan, self.journal, src,
                                           json.dumps(proposal_for(src)))
        self.assertEqual(r['status'], 'HUMAN_REVIEW_REQUIRED')
        self.assertIsNone(r['overall_score'])
        self.assertEqual(len(r['dimensions']), 12)
        self.assertFalse(r['eligible_for_host_scoring'])

    def test_forged_event_cannot_be_cited(self):
        src = compile_host_source(self.plan, self.journal, 0)
        p = proposal_for(src)
        p['dimensions'][1]['evidence_ids'] = ['fake-q2:5']
        self.bad('UNTRUSTED_PROPOSAL_REJECTED_CROSS_QUESTION_OR_NONCANDIDATE_CITATION',
                 review_untrusted_proposal_json, self.plan, self.journal, src, json.dumps(p))

    def test_interviewer_reply_cannot_be_scoring_evidence(self):
        src = compile_host_source(self.plan, self.journal, 0)
        p = proposal_for(src)
        p['dimensions'][1]['evidence_ids'] = ['fake-q1:4']
        self.bad('UNTRUSTED_PROPOSAL_REJECTED_CROSS_QUESTION_OR_NONCANDIDATE_CITATION',
                 review_untrusted_proposal_json, self.plan, self.journal, src, json.dumps(p))

    def test_unauthorized_grade_field_rejected(self):
        src = compile_host_source(self.plan, self.journal, 0)
        p = proposal_for(src); p['overall_score'] = 100
        self.bad('UNTRUSTED_PROPOSAL_REJECTED_INVALID_PROPOSAL_SHAPE',
                 review_untrusted_proposal_json, self.plan, self.journal, src, json.dumps(p))

    def test_duplicate_json_keys_rejected(self):
        src = compile_host_source(self.plan, self.journal, 0)
        self.bad('UNTRUSTED_PROPOSAL_REJECTED_DUPLICATE_JSON_KEY',
                 review_untrusted_proposal_json, self.plan, self.journal, src, '{"schema":1,"schema":2}')

    def test_skipped_question_has_zero_rated_dimensions(self):
        self.plan['results'][1]['outcome'] = 'SKIPPED'
        self.plan['results'][1]['session'] = None
        src = compile_host_source(self.plan, self.journal, 1)
        self.assertEqual(src['evidence'], [])

    def test_none_session_without_skip_is_rejected(self):
        self.plan['results'][1]['session'] = None
        self.bad('QUESTION_SESSION_NOT_FROZEN', compile_host_source, self.plan, self.journal, 1)

    def test_renderer_authority_never_granted(self):
        p = prepare_host_only_packet(self.plan, self.journal, 0)
        self.assertEqual(set(p), {'schema', 'role', 'source_sha256', 'proposal_schema',
                                  'source', 'status', 'paid_calls', 'score', 'can_submit_provider_request'})

if __name__ == '__main__':
    unittest.main()
