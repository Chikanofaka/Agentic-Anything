"""E4-C0: preflight readiness, source fidelity and no-reference-leak gates."""
import copy
import hashlib
import unittest

from tia_runtime.setup import InterviewConfig, review_question
from tia_runtime.preflight_preparer import (
    SCHEMA, build_preflight_readiness, public_role_view, authorize_private_reference,
)


def config(count=3, environment='POSTGRESQL'):
    return InterviewConfig(technical_environment=environment,
        duration_minutes=45 if count == 3 else 60, difficulty='HARD',
        question_source='BYOQ', interviewer_mechanism='STRICT_CHALLENGING')


def reviewed(n, environment='POSTGRESQL'):
    fields = dict(problem_statement=f'Solve this query for group {n}.',
        task='Return matching rows', schema='Orders(id INTEGER)',
        example_input='id=1', expected_output='id=1',
        source='OWNER', environment=environment, constraints='No extra constraints',
        source_reference=f'test://problem/{n}')
    r = review_question(fields, environment)
    assert not r['issues']
    r.update(human_confirmed=True, practice_eligible=True)
    return r


class PreflightC0Tests(unittest.TestCase):
    def test_no_config_is_safe(self):
        x=build_preflight_readiness(None, [])
        self.assertEqual(x['status'], 'CONFIG_REQUIRED')
        self.assertEqual(x['paid_requests_by_preflight'], 0)

    def test_three_confirmed_and_bound(self):
        x=build_preflight_readiness(config(), [reviewed(i) for i in range(3)])
        self.assertEqual(x['status'], 'READY_FOR_FUTURE_PRIVATE_PREPARATION')
        self.assertEqual(x['confirmed_count'], 3)
        self.assertTrue(all(q['status']=='SOURCE_BOUND_CONFIRMED' for q in x['questions']))

    def test_four_questions_not_four_live_launch(self):
        x=build_preflight_readiness(config(4), [reviewed(i) for i in range(4)])
        self.assertEqual(x['confirmed_count'],4)
        self.assertFalse(x['live_four_question_supported'])
        self.assertFalse(x['native_preparer_available'])

    def test_partial_keeps_review_required(self):
        x=build_preflight_readiness(config(), [reviewed(1),reviewed(2)])
        self.assertEqual(x['status'],'QUESTION_REVIEW_REQUIRED')

    def test_missing_confirmation(self):
        a=reviewed(1); a['human_confirmed']=False
        x=build_preflight_readiness(config(),[a,reviewed(2),reviewed(3)])
        self.assertEqual(x['confirmed_count'],2)

    def test_forged_question_digest_cannot_confirm(self):
        a=reviewed(1); a['content_sha256']='a'*64
        x=build_preflight_readiness(config(),[a,reviewed(2),reviewed(3)])
        self.assertEqual(x['questions'][0]['status'],'REVIEW_REQUIRED')

    def test_changed_fields_stale_hash_cannot_confirm(self):
        a=reviewed(1); a['fields']['task']='NEW QUESTION'
        x=build_preflight_readiness(config(),[a,reviewed(2),reviewed(3)])
        self.assertEqual(x['questions'][0]['status'],'REVIEW_REQUIRED')

    def test_duplicate_question_digest(self):
        a=reviewed(1)
        x=build_preflight_readiness(config(),[a,copy.deepcopy(a),reviewed(3)])
        self.assertEqual(x['status'],'QUESTION_REVIEW_REQUIRED')

    def test_cross_language_question_rejected(self):
        x=build_preflight_readiness(config(environment='POSTGRESQL'),
              [reviewed(i,environment='PANDAS') for i in range(3)])
        self.assertEqual(x['confirmed_count'],0)

    def test_untrusted_review_type_rejected(self):
        x=build_preflight_readiness(config(),['not-review', {}, reviewed(3)])
        self.assertEqual(x['confirmed_count'],1)

    def test_no_reference_code_or_raw_problem_in_projection(self):
        rs=[reviewed(i) for i in range(3)]
        x=build_preflight_readiness(config(),rs)
        for role in ('renderer','interviewer','trainer'):
            v=public_role_view(x,role)
            s=repr(v)
            self.assertNotIn('Orders(id INTEGER)', s)
            self.assertNotIn('Solve this query',s)
            self.assertNotIn("'reference_solution':",s)
            self.assertFalse(v['interviewer_reference_access'])

    def test_ignore_forged_reference_fields(self):
        x=build_preflight_readiness(config(), [reviewed(i) for i in range(3)])
        x['reference_solution']='SELECT hidden_secret FROM vault'
        x['questions'][0]['reference_code']='SELECT hidden_secret'
        self.assertNotIn('hidden_secret',repr(public_role_view(x,'interviewer')))

    def test_denied_role_fails_closed(self):
        x=build_preflight_readiness(config(),[])
        with self.assertRaises(ValueError): public_role_view(x,'oracle')

    def test_private_oracle_authorization_not_fake_enabled(self):
        for role in ('oracle','preparer','interviewer','evaluator','trainer'):
            d=authorize_private_reference(role,'PREPARING',True,capability_ready=True)
            self.assertFalse(d['granted'])
            self.assertFalse(d['network_authorized'])

    def test_never_generate_or_execute_for_any_setup(self):
        for n in (3,4):
            x=build_preflight_readiness(config(n),[reviewed(i) for i in range(n)])
            self.assertEqual(x['reference_solutions_generated'],0)
            self.assertEqual(x['code_executions_by_preflight'],0)
            self.assertEqual(x['technical_score'],'NOT_SCORED')
            self.assertFalse(x['official_hidden_tests'])

    def test_read_only_source_records(self):
        rs=[reviewed(i) for i in range(3)]; before=copy.deepcopy(rs)
        build_preflight_readiness(config(),rs)
        self.assertEqual(rs,before)

    def test_host_readonly_projection_and_legacy_digest_contract(self):
        from pathlib import Path
        root=Path(__file__).resolve().parents[1]
        host=(root/'tia_runtime'/'app_host.py').read_text(encoding='utf-8')
        self.assertIn("result['preflight_readiness'] = build_preflight_readiness(",host)
        self.assertIn('public.pop("preflight_readiness", None)',host)
        self.assertNotIn("result['private_reference_code']",host)

    def test_legacy_tutorial_host_does_not_expose_new_preflight_projection(self):
        # Protect pre-S03-B tutorial state and its saved journal digest without
        # weakening the existing legacy SHA acceptance test in test_app_host.
        import asyncio
        import tempfile
        from tia_runtime.app_host import TutorialHost

        async def run():
            with tempfile.TemporaryDirectory() as directory:
                host = await TutorialHost.open(directory)
                try:
                    self.assertNotIn('preflight_readiness', host.state())
                    await host.command('tutorial_start', {})
                    self.assertNotIn('preflight_readiness', host.state())
                finally:
                    host.close()

        asyncio.run(run())

    def test_review_ui_is_render_only_not_native_request(self):
        from pathlib import Path
        ui=(Path(__file__).resolve().parents[1]/'ui'/'app.js').read_text(encoding='utf-8')
        self.assertIn('section.id = "preflightReadiness"',ui)
        self.assertIn('No solutions generated, code run or paid model calls.',ui)
        self.assertNotIn('act("preflight_prepare"',ui)


if __name__=='__main__': unittest.main()
