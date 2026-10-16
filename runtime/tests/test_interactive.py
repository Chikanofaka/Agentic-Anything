"""Transaction and private-storage boundaries for the native HAL worker.

These tests exercise the same Session entry point used by the application. They
do not call a provider, read a credential, or substitute a second game engine.
"""
import copy
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from hal_core.contracts import ContractError
from hal_core.interactive import Session, SessionStore


RUNTIME = Path(__file__).resolve().parents[1]


class InteractiveSessionTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.data_dir = Path(self.temporary.name) / 'session'
        self.session = Session(self.data_dir)

    def snapshot(self):
        return self.session.handle('snapshot', {})

    def start(self):
        return self.session.handle('start', {'player': '顾遥', 'style': 'empathetic'})

    def turn(self, text, mode='SIMULATED'):
        prepared = self.session.handle('prepare_turn', {'text': text})
        return self.session.handle('commit_turn', {
            'transaction_id': prepared['transaction_id'],
            'reply': prepared['fallback_reply'],
            'mode': mode,
        })

    def assert_unchanged(self, before):
        self.assertEqual(self.snapshot()['state'], before['state'])

    def test_snapshot_names_domain_reality_and_receipt(self):
        snapshot = self.snapshot()
        for field in ('state', 'receipt', 'reality', 'package'):
            self.assertIn(field, snapshot)
        json.dumps(snapshot, allow_nan=False)

    def test_start_and_restore_preserve_exact_domain_state(self):
        started = self.start()
        self.assertIn('顾遥', json.dumps(started['state'], ensure_ascii=False))
        restored = Session(self.data_dir).handle('snapshot', {})
        self.assertEqual(restored['state'], started['state'])

    def test_promise_and_following_conversation_survive_restart(self):
        self.start()
        self.turn('我保证保护你。')
        committed = self.turn('你喜欢雨天吗？')
        restored = Session(self.data_dir).handle('snapshot', {})
        self.assertEqual(restored['state'], committed['state'])
        self.assertIn('保护', json.dumps(restored['state'], ensure_ascii=False))

    def test_persona_conversation_preserves_case_action_budget(self):
        before = self.start()
        for question in ('你喜欢雨天吗？', '你今天感觉怎么样？', '你平时听什么音乐？'):
            current = self.turn(question)
            self.assertEqual(current['state']['case_turns'], before['state']['case_turns'])
        self.assertGreater(len(current['state']['transcript']), len(before['state']['transcript']))

    def test_classification_context_does_not_mutate_or_save_state(self):
        before = self.start()
        saved = (self.data_dir / 'session.json').read_bytes()
        result = self.session.handle('classify_context', {'text': '你喜欢雨天吗？'})
        self.assertIn('instructions', result)
        self.assertIn('input', result)
        self.assert_unchanged(before)
        self.assertEqual(saved, (self.data_dir / 'session.json').read_bytes())

    def test_prepare_can_be_cancelled_without_committing_or_saving(self):
        before = self.start()
        saved = (self.data_dir / 'session.json').read_bytes()
        prepared = self.session.handle('prepare_turn', {'text': '红色雨衣是谁的？'})
        self.assertIsInstance(prepared['transaction_id'], str)
        self.assertIn('context', prepared)
        self.assertIn('fallback_reply', prepared)
        self.session.handle('cancel_turn', {})
        self.assert_unchanged(before)
        self.assertEqual(saved, (self.data_dir / 'session.json').read_bytes())

    def test_second_prepare_is_rejected_while_one_turn_is_pending(self):
        before = self.start()
        self.session.handle('prepare_turn', {'text': '红色雨衣是谁的？'})
        with self.assertRaises(ContractError):
            self.session.handle('prepare_turn', {'text': '我保证保护你。'})
        self.session.handle('cancel_turn', {})
        self.assert_unchanged(before)

    def test_cancelled_transaction_cannot_later_commit(self):
        before = self.start()
        prepared = self.session.handle('prepare_turn', {'text': '红色雨衣是谁的？'})
        self.session.handle('cancel_turn', {})
        with self.assertRaises(ContractError):
            self.session.handle('commit_turn', {
                'transaction_id': prepared['transaction_id'],
                'reply': prepared['fallback_reply'], 'mode': 'SIMULATED',
            })
        self.assert_unchanged(before)

    def test_committed_transaction_cannot_be_replayed(self):
        self.start()
        prepared = self.session.handle('prepare_turn', {'text': '红色雨衣是谁的？'})
        params = {'transaction_id': prepared['transaction_id'],
                  'reply': prepared['fallback_reply'], 'mode': 'SIMULATED'}
        committed = self.session.handle('commit_turn', params)
        with self.assertRaises(ContractError):
            self.session.handle('commit_turn', params)
        self.assert_unchanged(committed)

    def test_wrong_transaction_does_not_commit_pending_turn(self):
        before = self.start()
        prepared = self.session.handle('prepare_turn', {'text': '红色雨衣是谁的？'})
        with self.assertRaises(ContractError):
            self.session.handle('commit_turn', {
                'transaction_id': 'stale-transaction',
                'reply': prepared['fallback_reply'], 'mode': 'SIMULATED',
            })
        self.session.handle('cancel_turn', {})
        self.assert_unchanged(before)

    def test_malformed_reply_leaves_saved_and_authoritative_state_unchanged(self):
        before = self.start()
        saved = (self.data_dir / 'session.json').read_bytes()
        for reply in (None, {}, [], 1, '', 'x' * 100_000):
            with self.subTest(reply_type=type(reply).__name__, length=len(str(reply))):
                prepared = self.session.handle('prepare_turn', {'text': '红色雨衣是谁的？'})
                with self.assertRaises(ContractError):
                    self.session.handle('commit_turn', {
                        'transaction_id': prepared['transaction_id'],
                        'reply': reply, 'mode': 'SIMULATED',
                    })
                self.session.handle('cancel_turn', {})
                self.assert_unchanged(before)
                self.assertEqual(saved, (self.data_dir / 'session.json').read_bytes())

    def test_unrecognized_inference_mode_cannot_claim_activation(self):
        before = self.start()
        prepared = self.session.handle('prepare_turn', {'text': '红色雨衣是谁的？'})
        with self.assertRaises(ContractError):
            self.session.handle('commit_turn', {
                'transaction_id': prepared['transaction_id'],
                'reply': prepared['fallback_reply'], 'mode': 'TRUST_ME_LIVE',
            })
        self.session.handle('cancel_turn', {})
        self.assert_unchanged(before)

    def test_only_model_committed_turn_records_live_inference(self):
        self.start()
        # Exercise trusted-parent provenance with fixture text; this test calls no model.
        committed = self.turn('红色雨衣是谁的？', mode='LIVE_MODEL')
        self.assertEqual(committed['receipt']['action'], 'TURN_COMMITTED')
        self.assertTrue(committed['receipt']['live_model_used'])
        advanced = self.session.handle('advance', {})
        self.assertEqual(advanced['receipt']['action'], 'advance')
        self.assertFalse(advanced['receipt']['live_model_used'])
        self.assertEqual(advanced['reality'], 'REAL_STATE_LIVE_LANGUAGE')
        restored = Session(self.data_dir).handle('snapshot', {})
        self.assertFalse(restored['receipt']['live_model_used'])
        self.assertEqual(restored['reality'], 'REAL_STATE_LIVE_LANGUAGE')
        reset = self.session.handle('reset', {})
        self.assertFalse(reset['receipt']['live_model_used'])
        self.assertEqual(reset['receipt']['mode'], 'SIMULATED')
        self.assertEqual(reset['reality'], 'REAL_STATE_SIMULATED_LANGUAGE')

    def test_provider_failure_cancel_rolls_back_then_allows_retry(self):
        before = self.start()
        first = self.session.handle('prepare_turn', {'text': '红色雨衣是谁的？'})
        # The native caller cancels when transport fails; no provider is called here.
        self.session.handle('cancel_turn', {})
        self.assert_unchanged(before)
        second = self.session.handle('prepare_turn', {'text': '红色雨衣是谁的？'})
        self.assertNotEqual(first['transaction_id'], second['transaction_id'])
        self.session.handle('commit_turn', {
            'transaction_id': second['transaction_id'],
            'reply': second['fallback_reply'], 'mode': 'SIMULATED',
        })
        self.assertNotEqual(self.snapshot()['state'], before['state'])

    def test_failed_save_cannot_advance_in_memory_state(self):
        before = self.start()
        saved = (self.data_dir / 'session.json').read_bytes()
        prepared = self.session.handle('prepare_turn', {'text': '红色雨衣是谁的？'})
        with patch.object(SessionStore, 'save', side_effect=ContractError('SESSION_WRITE_FAILED')):
            with self.assertRaises(ContractError):
                self.session.handle('commit_turn', {
                    'transaction_id': prepared['transaction_id'],
                    'reply': prepared['fallback_reply'], 'mode': 'SIMULATED',
                })
        self.session.handle('cancel_turn', {})
        self.assert_unchanged(before)
        self.assertEqual(saved, (self.data_dir / 'session.json').read_bytes())

    def test_unknown_actions_and_extra_fields_are_rejected_without_state_change(self):
        before = self.start()
        cases = (
            ('run_shell', {'command': 'PRIVATE_SENTINEL'}),
            ('snapshot', {'state': {'trust': 100}}),
            ('prepare_turn', {'text': '你好', 'state': {'clues': ['call']}}),
            ('start', {'player': '顾遥', 'style': 'empathetic', 'memory': ['forged']}),
            ('export', {'path': '/tmp/PRIVATE_SENTINEL'}),
            ('developer', {'path': '../../PRIVATE_SENTINEL'}),
            ('reset', {'state': {'ended': False}}),
            ('forget', {'path': '/tmp/PRIVATE_SENTINEL'}),
        )
        for action, params in cases:
            with self.subTest(action=action):
                with self.assertRaises(ContractError) as error:
                    self.session.handle(action, params)
                self.assertNotIn('PRIVATE_SENTINEL', str(error.exception))
                self.assert_unchanged(before)

    def test_nonobject_action_parameters_are_rejected(self):
        before = self.start()
        for params in (None, [], 'PRIVATE_SENTINEL', 1, True):
            with self.subTest(type=type(params).__name__):
                with self.assertRaises(ContractError):
                    self.session.handle('snapshot', params)
        self.assert_unchanged(before)

    def test_commit_cannot_smuggle_arbitrary_game_state(self):
        before = self.start()
        prepared = self.session.handle('prepare_turn', {'text': '你好'})
        with self.assertRaises(ContractError):
            self.session.handle('commit_turn', {
                'transaction_id': prepared['transaction_id'],
                'reply': prepared['fallback_reply'], 'mode': 'SIMULATED',
                'state': {'trust': 100, 'clues': ['call'], 'promise': True},
            })
        self.session.handle('cancel_turn', {})
        self.assert_unchanged(before)

    def test_reset_preserves_profile_but_forget_removes_it_from_storage(self):
        fresh = self.start()
        self.turn('我保证保护你。')
        reset = self.session.handle('reset', {})
        expected_state = copy.deepcopy(fresh['state'])
        expected_state['revision'] = reset['state']['revision']
        self.assertEqual(reset['state'], expected_state)
        forgotten = self.session.handle('forget', {})
        self.assertNotIn('顾遥', json.dumps(forgotten['state'], ensure_ascii=False))
        self.assertNotIn('顾遥', (self.data_dir / 'session.json').read_text())
        self.assertEqual(Session(self.data_dir).handle('snapshot', {})['state'], forgotten['state'])

    def test_old_transaction_cannot_commit_after_reset_or_forget(self):
        self.start()
        for action in ('reset', 'forget'):
            with self.subTest(action=action):
                prepared = self.session.handle('prepare_turn', {'text': '我保证保护你。'})
                expected = self.session.handle(action, {})
                with self.assertRaises(ContractError):
                    self.session.handle('commit_turn', {
                        'transaction_id': prepared['transaction_id'],
                        'reply': prepared['fallback_reply'], 'mode': 'SIMULATED',
                    })
                self.assert_unchanged(expected)

    def test_export_is_data_only_and_contains_current_state(self):
        current = self.start()
        exports = self.session.handle('export', {})['export']
        self.assertEqual(set(exports), {'state_json', 'user_md', 'receipt_json'})
        self.assertEqual(json.loads(exports['state_json']), current['state'])
        self.assertIsInstance(json.loads(exports['receipt_json']), dict)
        self.assertIn('顾遥', exports['user_md'])

    def test_developer_assets_are_available_without_model_or_credentials(self):
        developer = self.session.handle('developer', {})['developer']
        self.assertEqual(set(developer), {'readme', 'skills', 'entrypoint', 'manifest'})
        for value in developer.values():
            self.assertTrue(value)

    def test_snapshot_is_not_a_mutable_reference_into_authoritative_state(self):
        before = self.start()
        expected = copy.deepcopy(before)
        before['state']['forged_field'] = 'PRIVATE_SENTINEL'
        self.assert_unchanged(expected)

    def test_scene_change_is_denied_while_model_turn_is_pending(self):
        before = self.start()
        self.session.handle('prepare_turn', {'text': '红色雨衣是谁的？'})
        for action, params in (('advance', {}), ('verdict', {}), ('link', {'clues': ['clock', 'call']})):
            with self.subTest(action=action):
                with self.assertRaises(ContractError):
                    self.session.handle(action, params)
        self.session.handle('cancel_turn', {})
        self.assert_unchanged(before)

    def test_saved_envelope_uses_fixed_schema_and_private_file_mode(self):
        self.start()
        path = self.data_dir / 'session.json'
        saved = json.loads(path.read_text())
        self.assertEqual(set(saved), {'schema', 'domain_id', 'state', 'receipt'})
        self.assertEqual(saved['schema'], 'hal-session/v1')
        self.assertEqual(saved['domain_id'], 'witness-loop')
        self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)


class SessionStorageSecurityTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.data_dir = self.root / 'session'
        self.data_dir.mkdir()

    def write(self, content):
        (self.data_dir / 'session.json').write_text(content)

    def assert_denied(self):
        with self.assertRaises(ContractError) as error:
            Session(self.data_dir)
        self.assertNotIn('PRIVATE_SENTINEL', str(error.exception))

    def test_corrupt_json_fails_closed_without_overwriting_file(self):
        self.write('{"PRIVATE_SENTINEL":')
        before = (self.data_dir / 'session.json').read_bytes()
        self.assert_denied()
        self.assertEqual(before, (self.data_dir / 'session.json').read_bytes())

    def test_oversized_save_is_rejected(self):
        self.write(' ' * (2 * 1024 * 1024 + 1))
        self.assert_denied()

    def test_unknown_schema_and_domain_cannot_restore(self):
        for overrides in ({'schema': 'future/v9000'}, {'domain_id': 'unknown-domain'}):
            with self.subTest(overrides=overrides):
                value = {'schema': 'hal-session/v1', 'domain_id': 'witness-loop',
                         'state': {}, 'receipt': {}}
                value.update(overrides)
                self.write(json.dumps(value))
                self.assert_denied()

    def test_extra_envelope_or_state_fields_cannot_restore(self):
        session = Session(self.data_dir)
        session.handle('start', {'player': '顾遥', 'style': 'empathetic'})
        valid = json.loads((self.data_dir / 'session.json').read_text())
        for where in ('envelope', 'state'):
            with self.subTest(where=where):
                value = copy.deepcopy(valid)
                target = value if where == 'envelope' else value['state']
                target['PRIVATE_SENTINEL'] = 'unvalidated state'
                self.write(json.dumps(value))
                self.assert_denied()

    def test_duplicate_json_fields_cannot_restore(self):
        self.write('{"schema":"hal-session/v1","schema":"PRIVATE_SENTINEL",'
                   '"domain_id":"witness-loop","state":{},"receipt":{}}')
        self.assert_denied()

    def test_invalid_receipt_cannot_restore_untrusted_payload(self):
        session = Session(self.data_dir)
        session.handle('start', {'player': '顾遥', 'style': 'empathetic'})
        valid = json.loads((self.data_dir / 'session.json').read_text())
        for field, value in (('action', 'PRIVATE_SENTINEL'), ('live_model_used', 'yes'),
                             ('external_writes', True), ('package_digest', 'PRIVATE_SENTINEL')):
            with self.subTest(field=field):
                record = copy.deepcopy(valid)
                record['receipt'][field] = value
                self.write(json.dumps(record))
                self.assert_denied()

    def test_receipt_revision_must_match_restored_state_revision(self):
        session = Session(self.data_dir)
        session.handle('start', {'player': '顾遥', 'style': 'empathetic'})
        record = json.loads((self.data_dir / 'session.json').read_text())
        record['receipt']['revision'] = record['state']['revision'] + 1
        self.write(json.dumps(record))
        self.assert_denied()

    def test_local_action_receipt_cannot_fabricate_live_inference(self):
        session = Session(self.data_dir)
        session.handle('start', {'player': '顾遥', 'style': 'empathetic'})
        record = json.loads((self.data_dir / 'session.json').read_text())
        record['receipt'].update(action='reset', mode='LIVE_MODEL', live_model_used=True)
        self.write(json.dumps(record))
        self.assert_denied()

    @unittest.skipUnless(hasattr(os, 'O_NOFOLLOW'), 'requires no-follow file descriptors')
    def test_symlinked_save_cannot_read_or_overwrite_target(self):
        target = self.root / 'outside.json'
        target.write_text('PRIVATE_SENTINEL')
        (self.data_dir / 'session.json').symlink_to(target)
        self.assert_denied()
        self.assertEqual(target.read_text(), 'PRIVATE_SENTINEL')

    @unittest.skipUnless(hasattr(os, 'O_NOFOLLOW'), 'requires no-follow file descriptors')
    def test_symlinked_session_directory_is_rejected(self):
        linked = self.root / 'linked'
        linked.symlink_to(self.data_dir, target_is_directory=True)
        with self.assertRaises(ContractError):
            Session(linked)

    def test_directory_in_place_of_save_file_is_rejected(self):
        (self.data_dir / 'session.json').mkdir()
        self.assert_denied()


class InteractiveProtocolTests(unittest.TestCase):
    def worker(self, message, expected_exit=0):
        with tempfile.TemporaryDirectory() as directory:
            completed = subprocess.run(
                [sys.executable, '-B', '-m', 'hal_core.interactive', '--data-dir', directory],
                input=message, cwd=RUNTIME, text=True, capture_output=True, timeout=15,
                check=False,
            )
        self.assertEqual(completed.returncode, expected_exit, completed.stderr + completed.stdout)
        self.assertEqual(completed.stderr, '')
        self.assertNotIn('Traceback', completed.stdout)
        return [json.loads(line) for line in completed.stdout.splitlines()]

    def test_private_worker_accepts_snapshot_request_without_network_or_credentials(self):
        output = self.worker(json.dumps({'id': 'request_1', 'action': 'snapshot', 'params': {}}) + '\n')
        self.assertEqual(len(output), 1)
        self.assertEqual(output[0]['id'], 'request_1')
        self.assertTrue(output[0]['ok'])
        self.assertIn('state', output[0]['result'])

    def test_malformed_input_returns_static_error_and_channel_continues(self):
        message = '{"PRIVATE_SENTINEL":\n' + json.dumps({'id': 'next', 'action': 'snapshot', 'params': {}}) + '\n'
        output = self.worker(message)
        self.assertEqual(len(output), 2)
        self.assertFalse(output[0]['ok'])
        self.assertNotIn('PRIVATE_SENTINEL', json.dumps(output[0]))
        self.assertTrue(output[1]['ok'])

    def test_oversized_frame_closes_channel_with_one_static_error(self):
        output = self.worker('PRIVATE_SENTINEL' + 'x' * 40_000 + '\n', expected_exit=2)
        self.assertEqual(len(output), 1)
        self.assertFalse(output[0]['ok'])
        self.assertNotIn('PRIVATE_SENTINEL', json.dumps(output))

    def test_incomplete_frame_is_rejected(self):
        output = self.worker('{"PRIVATE_SENTINEL":', expected_exit=2)
        self.assertEqual(len(output), 1)
        self.assertFalse(output[0]['ok'])
        self.assertNotIn('PRIVATE_SENTINEL', json.dumps(output))

    def test_unknown_request_fields_cannot_inject_state(self):
        request = {'id': 'request_2', 'action': 'snapshot', 'params': {},
                   'state': {'PRIVATE_SENTINEL': True}}
        output = self.worker(json.dumps(request) + '\n')
        self.assertFalse(output[0]['ok'])
        self.assertNotIn('PRIVATE_SENTINEL', json.dumps(output))

    def test_large_valid_unicode_save_has_complete_bounded_snapshot_and_export_frames(self):
        # A long legitimate session previously fit the 2 MB save limit but killed
        # the native worker because ASCII-escaped stdout exceeded its 1 MiB buffer.
        with tempfile.TemporaryDirectory() as directory:
            session = Session(Path(directory))
            snapshot = session.handle('start', {'player': '顾遥', 'style': 'empathetic'})
            state = snapshot['state']
            state['transcript'] = [
                {'who': '顾遥' if index % 2 == 0 else '林雾',
                 'text': '雨' * 1000 if index % 2 == 0 else '🙂' * 4000, 'scene': 1}
                for index in range(120)
            ]
            state['memories'] = [
                {'fact': str(index) + '雨' * 295, 'source': 'PLAYER_STATEMENT', 'scene': 1, 'turn': 0}
                for index in range(256)
            ]
            session.binding.validate_state(state)
            record = {'schema': 'hal-session/v1', 'domain_id': 'witness-loop',
                      'state': state, 'receipt': snapshot['receipt']}
            session.store.save(record)
            session.store.close()
            saved = (Path(directory) / 'session.json').read_bytes()
            self.assertGreater(len(saved), 1024 * 1024)
            self.assertLess(len(saved), 2_000_000)
            requests = ''.join(json.dumps({'id': action, 'action': action, 'params': {}}) + '\n'
                               for action in ('snapshot', 'export'))
            completed = subprocess.run(
                [sys.executable, '-B', '-m', 'hal_core.interactive', '--data-dir', directory],
                input=requests, cwd=RUNTIME, text=True, capture_output=True, timeout=15, check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertEqual(completed.stderr, '')
            frames = completed.stdout.splitlines(keepends=True)
            self.assertEqual(len(frames), 2)
            for frame in frames:
                self.assertTrue(frame.endswith('\n'))
                self.assertLess(len(frame.encode('utf-8')), 8 * 1024 * 1024)
            restored, exported = (json.loads(frame) for frame in frames)
            self.assertTrue(restored['ok'])
            self.assertEqual(restored['result']['state'], state)
            self.assertTrue(exported['ok'])
            self.assertEqual(json.loads(exported['result']['export']['state_json']), state)
            self.assertEqual(saved, (Path(directory) / 'session.json').read_bytes())


if __name__ == '__main__':
    unittest.main()
