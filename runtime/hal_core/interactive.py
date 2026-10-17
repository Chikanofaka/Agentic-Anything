"""Private stdio host: reviewed domain lifecycle, atomic state and staged turns.

No listening socket, credentials, provider SDK, arbitrary paths or imported code.
Only a trusted native parent may provide model output and label its provenance.
"""
from __future__ import annotations

import argparse
import copy
import json
import os
import re
from pathlib import Path
import stat
import sys
import uuid

from .contracts import ContractError, inspect, parse_json
from .registry import INTERACTIVE

MAX_SAVE_BYTES = 2_000_000
MAX_MESSAGE_BYTES = 32_768
CURRENT_SAVE = 'session-v2.json'
LEGACY_PACKAGE_DIGEST = 'bd1f1f6f3c916e319d6553f382e756d400f7634a2a8709d542afdc5515c67c67'
MODES = ('SIMULATED', 'LIVE_MODEL', 'LIVE_MODEL_REJECTED_FALLBACK')
LOCAL_ACTIONS = ('continue', 'inspect', 'approach', 'language', 'advance', 'link', 'verdict', 'reset')


class SessionStore:
    def __init__(self, directory):
        directory = Path(directory)
        if directory.is_symlink():
            raise ContractError('UNSAFE_SESSION_DIRECTORY')
        directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        if not hasattr(os, 'O_NOFOLLOW'):
            raise ContractError('SAFE_STORAGE_UNSUPPORTED')
        try:
            self.fd = os.open(directory, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        except OSError:
            raise ContractError('SESSION_STORAGE_UNAVAILABLE') from None

    def close(self):
        if getattr(self, 'fd', None) is not None:
            os.close(self.fd)
            self.fd = None

    def __del__(self):
        self.close()

    def load(self, name=CURRENT_SAVE):
        if name not in (CURRENT_SAVE, 'session.json'):
            raise ContractError('INVALID_SESSION_FILENAME')
        try:
            fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=self.fd)
        except FileNotFoundError:
            return None
        except OSError:
            raise ContractError('SESSION_READ_FAILED') from None
        try:
            info = os.fstat(fd)
            if not stat.S_ISREG(info.st_mode) or info.st_size > MAX_SAVE_BYTES:
                raise ContractError('INVALID_SESSION_FILE')
            with os.fdopen(os.dup(fd), 'rb') as stream:
                data = stream.read(MAX_SAVE_BYTES + 1)
            if len(data) > MAX_SAVE_BYTES:
                raise ContractError('INVALID_SESSION_FILE')
            return parse_json(data)
        except (OSError, ValueError):
            raise ContractError('INVALID_SESSION_FILE') from None
        finally:
            os.close(fd)

    def save(self, record):
        data = json.dumps(record, ensure_ascii=False, allow_nan=False, separators=(',', ':')).encode('utf-8')
        if len(data) > MAX_SAVE_BYTES:
            raise ContractError('SESSION_LIMIT_REACHED')
        name = '.pending-' + uuid.uuid4().hex
        fd = None
        try:
            # Reject a planted symlink rather than quietly replacing it.
            try:
                current = os.stat(CURRENT_SAVE, dir_fd=self.fd, follow_symlinks=False)
                if not stat.S_ISREG(current.st_mode):
                    raise ContractError('UNSAFE_SESSION_FILE')
            except FileNotFoundError:
                pass
            fd = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=self.fd)
            with os.fdopen(fd, 'wb') as stream:
                fd = None
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(name, CURRENT_SAVE, src_dir_fd=self.fd, dst_dir_fd=self.fd)
        except OSError:
            raise ContractError('SESSION_WRITE_FAILED') from None
        finally:
            if fd is not None:
                os.close(fd)
            try:
                os.unlink(name, dir_fd=self.fd)
            except FileNotFoundError:
                pass


class Session:
    def __init__(self, data_dir, domain_id='witness-loop'):
        self.binding = INTERACTIVE.get(domain_id)
        if self.binding is None:
            raise ContractError('UNREGISTERED_INTERACTIVE_DOMAIN')
        self.domain_id = domain_id
        self.package_path = Path(__file__).resolve().parents[1] / 'fixtures' / self.binding.package_directory
        self.package = inspect(self.package_path)
        if self.package.contract['id'] != domain_id:
            raise ContractError('INTERACTIVE_PACKAGE_MISMATCH')
        self.store = SessionStore(data_dir)
        self.pending = None
        saved = self.store.load()
        if saved is None:
            legacy = self.store.load('session.json')
            if legacy is None:
                self.state = self.binding.start({})
                self.receipt = self._receipt('INITIALIZED', 'SIMULATED')
            else:
                self._restore_legacy(legacy)
        else:
            if not isinstance(saved, dict) or set(saved) != {'schema', 'domain_id', 'state', 'receipt'} or saved['schema'] != 'hal-session/v2' or saved['domain_id'] != domain_id:
                raise ContractError('INVALID_SAVED_SESSION')
            try:
                if not isinstance(saved['state'], dict) or saved['state'].get('schema') != 'witness-state/v2':
                    raise ValueError('INVALID_SAVED_STATE_VERSION')
                self.binding.validate_state(saved['state'])
                self._validate_receipt(saved['receipt'])
                if saved['receipt']['revision'] != saved['state']['revision']:
                    raise ValueError('STALE_SAVED_RECEIPT')
                if saved['receipt']['action'] == 'TURN_COMMITTED' and saved['receipt']['output_rejection_reason'] != saved['state']['last_validation']['rejection_reason']:
                    raise ValueError('INCONSISTENT_SAVED_VALIDATION')
            except (ValueError, TypeError, KeyError):
                raise ContractError('INVALID_SAVED_SESSION') from None
            self.state, self.receipt = saved['state'], saved['receipt']

    def _restore_legacy(self, saved):
        """Copy one validated v1 save forward; never edit the original backup."""
        try:
            if not isinstance(saved, dict) or set(saved) != {'schema', 'domain_id', 'state', 'receipt'} or saved['schema'] != 'hal-session/v1' or saved['domain_id'] != self.domain_id:
                raise ValueError('INVALID_LEGACY_SAVE')
            receipt = saved['receipt']
            if not isinstance(receipt, dict) or set(receipt) != {'kind', 'domain_id', 'package_digest', 'action', 'mode', 'live_model_used', 'external_writes', 'revision'}:
                raise ValueError('INVALID_LEGACY_RECEIPT')
            if receipt['kind'] != 'HAL_INTERACTIVE_RECEIPT_V1' or receipt['domain_id'] != self.domain_id or receipt['package_digest'] != LEGACY_PACKAGE_DIGEST:
                raise ValueError('INVALID_LEGACY_RECEIPT')
            if receipt['action'] not in ('INITIALIZED', 'STARTED', 'TURN_COMMITTED', 'advance', 'link', 'verdict', 'reset', 'FORGOTTEN') or receipt['mode'] not in ('SIMULATED', 'LIVE_MODEL') or type(receipt['live_model_used']) is not bool or receipt['live_model_used'] != (receipt['action'] == 'TURN_COMMITTED' and receipt['mode'] == 'LIVE_MODEL') or receipt['external_writes'] is not False:
                raise ValueError('INVALID_LEGACY_RECEIPT')
            if saved['state']['schema'] != 'witness-state/v1' or type(receipt['revision']) is not int or receipt['revision'] != saved['state']['revision']:
                raise ValueError('INVALID_LEGACY_STATE')
            self.state = self.binding.migrate_v1(copy.deepcopy(saved['state']))
            self.binding.validate_state(self.state)
            # Old transcript provenance remains in the untouched original file.
            self.receipt = self._receipt('MIGRATED_V1', receipt['mode'])
            self._persist(self.state, self.receipt)
        except (ValueError, TypeError, KeyError):
            raise ContractError('LEGACY_SAVE_MIGRATION_REJECTED') from None

    def _receipt(self, action, mode, rejection_reason=None):
        return {'kind': 'HAL_INTERACTIVE_RECEIPT_V2', 'domain_id': self.domain_id,
                'package_digest': self.package.digest, 'action': action, 'mode': mode,
                'live_model_used': action == 'TURN_COMMITTED' and mode in ('LIVE_MODEL', 'LIVE_MODEL_REJECTED_FALLBACK'), 'external_writes': False,
                'revision': self.state['revision'], 'character_context': self.binding.context_metadata(),
                'output_rejection_reason': rejection_reason}

    def _validate_receipt(self, value):
        if not isinstance(value, dict) or set(value) != {'kind', 'domain_id', 'package_digest', 'action', 'mode', 'live_model_used', 'external_writes', 'revision', 'character_context', 'output_rejection_reason'}:
            raise ValueError('INVALID_RECEIPT')
        if value['kind'] != 'HAL_INTERACTIVE_RECEIPT_V2' or value['domain_id'] != self.domain_id or value['package_digest'] != self.package.digest:
            raise ValueError('INVALID_RECEIPT')
        if value['mode'] not in MODES or type(value['live_model_used']) is not bool or value['live_model_used'] != (value['mode'] in MODES[1:] and value['action'] == 'TURN_COMMITTED') or value['external_writes'] is not False:
            raise ValueError('INVALID_RECEIPT')
        if value['action'] not in ('INITIALIZED', 'STARTED', 'TURN_COMMITTED', 'MIGRATED_V1', 'FORGOTTEN') + LOCAL_ACTIONS or type(value['revision']) is not int or value['revision'] < 0:
            raise ValueError('INVALID_RECEIPT')
        metadata = value['character_context']
        if not isinstance(metadata, dict) or set(metadata) != {'version', 'digest', 'source_digests'} or not isinstance(metadata['version'], str) or not 1 <= len(metadata['version']) <= 80:
            raise ValueError('INVALID_CONTEXT_RECEIPT')
        if not isinstance(metadata['digest'], str) or not re.fullmatch('[a-f0-9]{64}', metadata['digest']):
            raise ValueError('INVALID_CONTEXT_RECEIPT')
        hashes = metadata['source_digests']
        if not isinstance(hashes, dict) or not 1 <= len(hashes) <= 16 or any(not isinstance(k, str) or not re.fullmatch('[a-z_]+\\.md', k) or not isinstance(v, str) or not re.fullmatch('[a-f0-9]{64}', v) for k, v in hashes.items()):
            raise ValueError('INVALID_CONTEXT_RECEIPT')
        reason = value['output_rejection_reason']
        if reason is not None and (not isinstance(reason, str) or not re.fullmatch('[A-Z_]{1,80}', reason)):
            raise ValueError('INVALID_REJECTION_REASON')
        if value['action'] != 'TURN_COMMITTED' and reason is not None:
            raise ValueError('INVALID_REJECTION_REASON')
        if value['action'] == 'TURN_COMMITTED' and ((value['mode'] == 'LIVE_MODEL_REJECTED_FALLBACK') != (reason is not None and value['live_model_used'])):
            raise ValueError('INVALID_REJECTION_REASON')

    def snapshot(self):
        return {'state': copy.deepcopy(self.state), 'receipt': copy.deepcopy(self.receipt),
                'view': self.binding.public_view(copy.deepcopy(self.state)),
                'reality': {'LIVE_MODEL': 'REAL_STATE_LIVE_LANGUAGE', 'LIVE_MODEL_REJECTED_FALLBACK': 'REAL_STATE_VALIDATED_FALLBACK'}.get(self.receipt['mode'], 'REAL_STATE_SIMULATED_LANGUAGE'),
                'package': {'id': self.domain_id, 'title': self.package.contract['name'],
                            'digest': self.package.digest, 'schema': self.package.contract['schema_version']}}

    def _persist(self, state, receipt):
        self.binding.validate_state(state)
        receipt['revision'] = state['revision']
        self._validate_receipt(receipt)
        self.store.save({'schema': 'hal-session/v2', 'domain_id': self.domain_id, 'state': state, 'receipt': receipt})
        self.state, self.receipt = state, receipt

    @staticmethod
    def _fields(params, required, optional=()):
        if not isinstance(params, dict) or set(params) - set(required) - set(optional) or set(required) - set(params):
            raise ContractError('INVALID_ACTION_FIELDS')

    def handle(self, action, params):
        try:
            return self._handle(action, params)
        except ContractError:
            raise
        except (ValueError, TypeError, KeyError, UnicodeError, OverflowError):
            # Domain errors are static; never echo provider/player/OS exception text.
            raise ContractError('DOMAIN_ACTION_REJECTED') from None
        except OSError:
            raise ContractError('SESSION_STORAGE_UNAVAILABLE') from None

    def _handle(self, action, params):
        if not isinstance(action, str) or not isinstance(params, dict):
            raise ContractError('INVALID_ACTION')
        if self.pending and action not in ('snapshot', 'cancel_turn', 'reset', 'forget', 'commit_turn'):
            raise ContractError('TURN_IN_PROGRESS')
        if action == 'snapshot':
            self._fields(params, ())
            return self.snapshot()
        if action == 'start':
            self._fields(params, ('player', 'style'), ('language',))
            state = self.binding.start(params)
            state['revision'] = self.state['revision'] + 1
            self._persist(state, self._receipt('STARTED', 'SIMULATED'))
            return self.snapshot()
        if action == 'preview_turn':
            self._fields(params, ('text',))
            return self.binding.preview_turn(copy.deepcopy(self.state), params['text'])
        if action == 'classify_context':
            self._fields(params, ('text',), ('confirm_case',))
            self._preflight(params)
            return self.binding.classify_context(copy.deepcopy(self.state), params['text'])
        if action == 'prepare_turn':
            self._fields(params, ('text',), ('topic', 'confirm_case'))
            self._preflight(params)
            draft = self.binding.prepare_turn(copy.deepcopy(self.state), params['text'], params.get('topic'))
            self.binding.validate_state(draft['state'])
            if draft['state']['case_turns'] > self.state['case_turns'] and params.get('confirm_case') is not True:
                raise ContractError('CASE_ACTION_CONFIRMATION_REQUIRED')
            transaction_id = uuid.uuid4().hex
            self.pending = {'id': transaction_id, 'revision': self.state['revision'], 'draft': draft}
            return {'transaction_id': transaction_id, 'context': draft['context'],
                    'fallback_reply': draft['fallback_reply'], 'topic': draft['topic'], 'route': draft['route']}
        if action == 'commit_turn':
            self._fields(params, ('transaction_id', 'reply', 'mode'))
            if not self.pending or params['transaction_id'] != self.pending['id'] or self.pending['revision'] != self.state['revision']:
                raise ContractError('STALE_TURN')
            if params['mode'] not in ('SIMULATED', 'LIVE_MODEL'):
                raise ContractError('INVALID_LANGUAGE_MODE')
            state = self.binding.finalize_turn(copy.deepcopy(self.pending['draft']['state']), params['reply'])
            reason = state.get('last_validation', {}).get('rejection_reason')
            mode = 'LIVE_MODEL_REJECTED_FALLBACK' if reason and params['mode'] == 'LIVE_MODEL' else params['mode']
            self._persist(state, self._receipt('TURN_COMMITTED', mode, reason))
            self.pending = None
            return self.snapshot()
        if action == 'cancel_turn':
            self._fields(params, ())
            self.pending = None
            return self.snapshot()
        if action in LOCAL_ACTIONS:
            required = {'link': ('clues',), 'inspect': ('id',), 'language': ('language',)}.get(action, ())
            self._fields(params, required)
            state = self.binding.act(copy.deepcopy(self.state), action, params)
            self._persist(state, self._receipt(action, 'SIMULATED' if action == 'reset' else self.receipt['mode']))
            self.pending = None
            return self.snapshot()
        if action == 'forget':
            self._fields(params, ())
            state = self.binding.start({})
            state['revision'] = self.state['revision'] + 1
            self._persist(state, self._receipt('FORGOTTEN', 'SIMULATED'))
            self.pending = None
            return self.snapshot()
        if action == 'export':
            self._fields(params, ())
            return {'export': {'state_json': json.dumps(self.state, ensure_ascii=False, indent=2),
                               'user_md': self.binding.user_markdown(self.state),
                               'receipt_json': json.dumps(self.receipt, ensure_ascii=False, indent=2)}}
        if action == 'developer':
            self._fields(params, ())
            # Only reviewed bundled asset paths; renderer cannot supply a filename.
            contract = self.package.contract
            def read_asset(path):
                data = (self.package_path / path).read_text(encoding='utf-8')
                if len(data) > 32_000:
                    raise ContractError('DEVELOPER_ASSET_TOO_LARGE')
                return data
            return {'developer': {'readme': read_asset(contract['readme']),
                                  'skills': [read_asset(path) for path in contract['skills']],
                                  'entrypoint': read_asset(contract['entrypoint']), 'manifest': contract}}
        raise ContractError('UNKNOWN_INTERACTIVE_ACTION')

    def _preflight(self, params):
        if 'confirm_case' in params and type(params['confirm_case']) is not bool:
            raise ContractError('INVALID_CASE_CONFIRMATION')
        preview = self.binding.preview_turn(copy.deepcopy(self.state), params['text'])
        if preview['case_action'] and params.get('confirm_case') is not True:
            raise ContractError('CASE_ACTION_CONFIRMATION_REQUIRED')
        if preview['case_action'] and preview['remaining'] <= 0:
            raise ContractError('CASE_ACTIONS_EXHAUSTED')


def main():
    parser = argparse.ArgumentParser(description='HAL private native stdio host; no network or credentials')
    parser.add_argument('--data-dir', required=True)
    parser.add_argument('--domain', default='witness-loop')
    args = parser.parse_args()
    try:
        session = Session(args.data_dir, args.domain)
    except Exception:
        print(json.dumps({'id': None, 'ok': False, 'error': 'SESSION_INITIALIZATION_FAILED'}), flush=True)
        return 2
    try:
        while True:
            line = sys.stdin.buffer.readline(MAX_MESSAGE_BYTES + 1)
            if not line:
                break
            request_id = None
            try:
                if len(line) > MAX_MESSAGE_BYTES or not line.endswith(b'\n'):
                    # Oversized framing closes the private channel rather than resynchronizing.
                    print(json.dumps({'id': None, 'ok': False, 'error': 'MESSAGE_TOO_LARGE'}), flush=True)
                    return 2
                request = parse_json(line)
                Session._fields(request, ('id', 'action', 'params'))
                if not isinstance(request['id'], str) or not 1 <= len(request['id']) <= 64 or not request['id'].isascii() or not request['id'].replace('-', '').replace('_', '').isalnum():
                    raise ContractError('INVALID_REQUEST_ID')
                request_id = request['id']
                result = session.handle(request['action'], request['params'])
                output = {'id': request_id, 'ok': True, 'result': result}
            except ContractError as error:
                output = {'id': request_id, 'ok': False, 'error': str(error)}
            except Exception:
                output = {'id': request_id, 'ok': False, 'error': 'INTERACTIVE_REQUEST_FAILED'}
            print(json.dumps(output, ensure_ascii=False, allow_nan=False), flush=True)
    finally:
        session.store.close()
    return 0


if __name__ == '__main__':
    sys.exit(main())
