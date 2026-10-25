import copy
import hashlib
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tia_runtime.evaluator_v1_semantic_contract import (
    DIMENSIONS, PROPOSAL_SCHEMA, SemanticContractError,
    build_review_packet, compile_source, strict_load, validate_proposal,
    validate_source)


def digest(x):
    return hashlib.sha256(x.encode('utf-8')).hexdigest()


def fixture(scenario='COMMON_PATH', transcript='Plan uses a window function'):
    source = compile_source('1'*64, 0, [{
        'id': 'session-q1:3', 'question_index': 0, 'actor': 'candidate',
        'kind': 'plan', 'excerpt': transcript, 'excerpt_sha256': digest(transcript)}],
        scenario, '2'*64)
    proposal = {'schema': PROPOSAL_SCHEMA, 'role': 'evaluator',
                'source_sha256': source['source_sha256'], 'dimensions': [
                    {'id': d, 'anchor': 3 if d == 'T2' else None,
                     'evidence_ids': ['session-q1:3'] if d == 'T2' else [],
                     'reason': 'A candidate described a reasoned SQL strategy.' if d == 'T2' else 'No direct evidence in this example.',
                     'confidence': 'LOW' if d == 'T2' else 'NOT_ASSESSED'}
                    for d in DIMENSIONS],
                'summary': 'One low-confidence cited proposal; no executable test proof.'}
    return source, proposal


class EventBoundSemanticTests(unittest.TestCase):
    def denied(self, code, fn, *args):
        with self.assertRaises(SemanticContractError) as ctx:
            fn(*args)
        self.assertEqual(ctx.exception.code, code)

    def test_twelve_dimensions_exact(self):
        self.assertEqual(DIMENSIONS, ('T1','T2','T3','T4','C1','C2','C3','C4','P1','P2','P3','P4'))

    def test_valid_source_and_proposal(self):
        source, proposal = fixture()
        self.assertTrue(validate_source(source))
        self.assertTrue(validate_proposal(source, proposal))

    def test_review_never_assigns_points_or_pass(self):
        s, p = fixture()
        r = build_review_packet(s, p)
        self.assertIsNone(r['overall_score'])
        self.assertFalse(r['eligible_for_host_scoring'])
        self.assertFalse(r['verified_code_execution'])
        self.assertEqual(r['status'], 'HUMAN_REVIEW_REQUIRED')

    def test_citations_are_bound_to_exact_event_hash(self):
        s, p = fixture()
        e = build_review_packet(s, p)['dimensions'][1]['evidence'][0]
        self.assertEqual(e['excerpt_sha256'], digest('Plan uses a window function'))
        self.assertEqual(e['event_id'], 'session-q1:3')

    def test_event_excerpt_mutation_rejected(self):
        s, _ = fixture()
        s['evidence'][0]['excerpt'] = 'different'
        self.denied('SOURCE_DIGEST_MISMATCH', validate_source, s)

    def test_digest_mutation_rejected(self):
        s, _ = fixture()
        s['source_sha256'] = '0'*64
        self.denied('SOURCE_DIGEST_MISMATCH', validate_source, s)

    def test_question_cross_binding_rejected(self):
        s, _ = fixture()
        self.denied('INVALID_OR_CROSS_QUESTION_EVENT', compile_source, '1'*64, 1, s['evidence'], 'COMMON_PATH', '2'*64)

    def test_not_closed_rejected(self):
        s, _ = fixture()
        self.denied('SOURCE_NOT_FROZEN_OR_BOUND', compile_source, '1'*64, 0, s['evidence'], 'COMMON_PATH', '2'*64, False)

    def test_invalid_sha_rejected(self):
        s, _ = fixture()
        self.denied('SOURCE_NOT_FROZEN_OR_BOUND', compile_source, 'bad', 0, s['evidence'], 'COMMON_PATH', '2'*64)

    def test_bool_question_index_rejected(self):
        s, _ = fixture()
        self.denied('SOURCE_NOT_FROZEN_OR_BOUND', compile_source, '1'*64, True, s['evidence'], 'COMMON_PATH', '2'*64)

    def test_duplicate_event_rejected(self):
        s, _ = fixture()
        self.denied('INVALID_OR_CROSS_QUESTION_EVENT', compile_source, '1'*64, 0, s['evidence']*2, 'COMMON_PATH', '2'*64)

    def test_too_many_source_events_rejected(self):
        s, _ = fixture()
        self.denied('INVALID_SOURCE_EVENTS', compile_source, '1'*64, 0, s['evidence']*33, 'COMMON_PATH', '2'*64)

    def test_overlong_excerpt_rejected(self):
        s, _ = fixture()
        x = '😀'*151
        s['evidence'][0]['excerpt'] = x
        s['evidence'][0]['excerpt_sha256'] = digest(x)
        self.denied('INVALID_OR_CROSS_QUESTION_EVENT', compile_source, '1'*64, 0, s['evidence'], 'COMMON_PATH', '2'*64)

    def test_source_extra_authority_rejected(self):
        s, _ = fixture()
        s['host_admin'] = True
        self.denied('INVALID_SOURCE_SHAPE', validate_source, s)

    def test_proposal_extra_score_rejected(self):
        s, p = fixture()
        p['overall_grade'] = 100
        self.denied('INVALID_PROPOSAL_SHAPE', validate_proposal, s, p)

    def test_dimension_extra_authority_rejected(self):
        s, p = fixture()
        p['dimensions'][0]['score_authority'] = 'model'
        self.denied('INVALID_DIMENSION_SHAPE', validate_proposal, s, p)

    def test_no_unauthorized_role(self):
        s, p = fixture()
        p['role'] = 'trainer'
        self.denied('STALE_OR_UNAUTHORIZED_PROPOSAL', validate_proposal, s, p)

    def test_stale_source_fails(self):
        s, p = fixture()
        p['source_sha256'] = '0'*64
        self.denied('STALE_OR_UNAUTHORIZED_PROPOSAL', validate_proposal, s, p)

    def test_duplicate_dimension_rejected(self):
        s, p = fixture()
        p['dimensions'][1]['id'] = 'T1'
        self.denied('INVALID_DIMENSION_ID', validate_proposal, s, p)

    def test_dimension_missing_rejected(self):
        s, p = fixture()
        p['dimensions'].pop()
        self.denied('INCOMPLETE_12_DIMENSION_PROPOSAL', validate_proposal, s, p)

    def test_forged_citation_rejected(self):
        s, p = fixture()
        p['dimensions'][1]['evidence_ids'] = ['fake-q1:999']
        self.denied('CROSS_QUESTION_OR_NONCANDIDATE_CITATION', validate_proposal, s, p)

    def test_uncited_anchor_rejected(self):
        s, p = fixture()
        p['dimensions'][1]['evidence_ids'] = []
        self.denied('UNCITED_OR_UNCALIBRATED_ANCHOR', validate_proposal, s, p)

    def test_missing_is_not_zero(self):
        s, p = fixture()
        p['dimensions'][1]['anchor'] = None
        self.denied('MISSING_EVIDENCE_NOT_ZERO', validate_proposal, s, p)

    def test_bool_anchor_rejected(self):
        s, p = fixture()
        p['dimensions'][1]['anchor'] = True
        self.denied('INVALID_ANCHOR', validate_proposal, s, p)

    def test_excessive_anchor_rejected(self):
        s, p = fixture()
        p['dimensions'][1]['anchor'] = 5
        self.denied('INVALID_ANCHOR', validate_proposal, s, p)

    def test_high_confidence_without_verifier_not_allowed(self):
        s, p = fixture()
        p['dimensions'][1]['confidence'] = 'HIGH'
        self.denied('UNCITED_OR_UNCALIBRATED_ANCHOR', validate_proposal, s, p)

    def test_empty_session_has_no_score(self):
        s = compile_source('1'*64,0,[],'UNKNOWN','2'*64)
        p = {'schema': PROPOSAL_SCHEMA, 'role': 'evaluator', 'source_sha256':s['source_sha256'],
             'dimensions': [{'id':d,'anchor':None,'evidence_ids':[],
                             'reason':'Not observed in the session.','confidence':'NOT_ASSESSED'} for d in DIMENSIONS],
             'summary':'No observed evidence and no assessment.'}
        review = build_review_packet(s, p)
        self.assertTrue(all(x['proposed_anchor'] is None for x in review['dimensions']))

    def test_interviewer_cannot_be_scoring_evidence(self):
        x='Try a window function'
        event={'id':'interviewer-q1:4','question_index':0,'actor':'interviewer','kind':'reply',
               'excerpt':x,'excerpt_sha256':digest(x)}
        s=compile_source('1'*64,0,[event],'UNKNOWN','2'*64)
        p={'schema':PROPOSAL_SCHEMA,'role':'evaluator','source_sha256':s['source_sha256'],
           'dimensions':[{'id':d,'anchor':1 if d=='T1' else None,
                          'evidence_ids':['interviewer-q1:4'] if d=='T1' else [],
                          'reason':'Only interviewer advice; no candidate work.' if d=='T1' else 'No observed candidate action.',
                          'confidence':'LOW' if d=='T1' else 'NOT_ASSESSED'} for d in DIMENSIONS],
           'summary':'Not a valid independent score.'}
        self.denied('CROSS_QUESTION_OR_NONCANDIDATE_CITATION',validate_proposal,s,p)

    def test_all_four_scenarios_are_supported(self):
        for scenario in ('COMMON_PATH','VALID_ALTERNATIVE_UNVERIFIED','ONE_SHOT_CODE','STUCK_DIAGNOSTIC'):
            s, p=fixture(scenario)
            self.assertEqual(build_review_packet(s,p)['scenario'],scenario)

    def test_same_candidate_different_mode_not_scored(self):
        s, p = fixture()
        self.assertNotIn('interviewer_mode', build_review_packet(s,p))

    def test_strict_json_duplicate_keys(self):
        self.denied('DUPLICATE_JSON_KEY', strict_load, '{"a":1,"a":2}')

    def test_strict_json_nonfinite(self):
        self.denied('NONFINITE_JSON_VALUE',strict_load,'{"score":NaN}')

    def test_no_input_mutation(self):
        s, p=fixture()
        before=copy.deepcopy((s,p))
        build_review_packet(s,p)
        self.assertEqual((s,p),before)

    def test_deterministic(self):
        s,p=fixture()
        self.assertEqual(build_review_packet(s,p),build_review_packet(s,p))

if __name__=='__main__':
    unittest.main()
