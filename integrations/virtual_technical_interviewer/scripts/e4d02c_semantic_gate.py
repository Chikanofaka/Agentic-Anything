#!/usr/bin/env python3
"""Read-only TIA E4-D/02C on-device evidence provenance gate.

No model access, no credential access, no host process invocation, no scoring.
Outputs private (0600) human-review metadata. A checksum is not a signature.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys

MAX_SAVE_BYTES = 2 * 1024 * 1024
EXPECTED_SCHEMA = "tia-tutorial-save/v1"
EXPECTED_PROTOCOL = "tia-native-tutorial/v1"
POSSIBLE_EVENTS = {'rehearsal_submit', 'rehearsal_candidate', 'rehearsal_candidate_action',
                   'candidate_submit', 'candidate_action'}
EVALUATOR_COMMIT = 'native_commit_evaluator'
PRIVATE_MODE = 0o600

class GateError(ValueError):
    pass


def _strict_json(raw: bytes):
    def deduplicate(pairs):
        obj = {}
        for k, v in pairs:
            if k in obj:
                raise GateError('DUPLICATE_JSON_KEY')
            obj[k] = v
        return obj
    def no_constant(c):
        raise GateError('NONFINITE_NUMBER')
    try:
        return json.loads(raw.decode('utf-8'), object_pairs_hook=deduplicate,
                          parse_constant=no_constant)
    except (ValueError, UnicodeError, RecursionError) as e:
        raise GateError('INVALID_SAVE_JSON') from e


def digest_object(value):
    data = json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True,
                      allow_nan=False).encode('utf-8')
    return hashlib.sha256(data).hexdigest()


def read_local_save(path: Path):
    """No symlink traversal at leaf, no lock, and no writes to app state."""
    if path.is_symlink():
        raise GateError('SAVE_SYMLINK_REJECTED')
    try:
        flags = os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0)
        fd = os.open(path, flags)
        try:
            meta = os.fstat(fd)
            if not stat.S_ISREG(meta.st_mode) or meta.st_size > MAX_SAVE_BYTES:
                raise GateError('SAVE_UNSAFE_OR_TOO_LARGE')
            raw = os.read(fd, MAX_SAVE_BYTES + 1)
        finally:
            os.close(fd)
    except (OSError, PermissionError) as e:
        raise GateError('SAVE_UNREADABLE') from e
    if len(raw) > MAX_SAVE_BYTES:
        raise GateError('SAVE_TOO_LARGE')
    return _strict_json(raw), hashlib.sha256(raw).hexdigest()


def scan(data: dict, file_digest: str, question: int = 1):
    if not isinstance(data, dict) or data.get('schema') != EXPECTED_SCHEMA or data.get('protocol') != EXPECTED_PROTOCOL:
        raise GateError('UNRECOGNIZED_SAVE_SCHEMA')
    if type(data.get('journal')) is not list or len(data['journal']) > 512:
        raise GateError('INVALID_JOURNAL')
    if set(data) != {'schema', 'protocol', 'instance_id', 'journal', 'state_sha256', 'document_sha256'}:
        raise GateError('UNRECOGNIZED_SAVE_ENVELOPE')
    sealed = {k: v for k, v in data.items() if k != 'document_sha256'}
    if data['document_sha256'] != digest_object(sealed):
        raise GateError('SAVE_DIGEST_MISMATCH')
    count = {}
    actions = []
    candidate_actions = []
    commits = []
    issues = []
    for i, entry in enumerate(data['journal']):
        if type(entry) is not dict or not isinstance(entry.get('action'), str):
            raise GateError('INVALID_JOURNAL_ENTRY')
        action = entry['action']
        count[action] = count.get(action, 0) + 1
        actions.append(action)
        if action in POSSIBLE_EVENTS:
            params = entry.get('params')
            params = params if type(params) is dict else {}
            # Do NOT emit candidate payloads, even into the local evidence report.
            redacted = {'journal_index': i, 'action': action,
                        'outcome': entry.get('outcome', 'UNKNOWN'),
                        'param_keys': sorted(str(k) for k in params),
                        'declared_kind': params.get('kind') if params.get('kind') in
                            ('clarify', 'plan', 'implement', 'test', 'help') else 'UNKNOWN',
                        'declared_question_index': params.get('question_index')
                            if type(params.get('question_index')) is int else None}
            candidate_actions.append(redacted)
        if action == EVALUATOR_COMMIT:
            params = entry.get('params') if type(entry.get('params')) is dict else {}
            # The commit may be in a newer schema; no semantic decoding without reviewed contract.
            commits.append({'journal_index': i, 'outcome': entry.get('outcome', 'UNKNOWN'),
                            'param_keys': sorted(str(k) for k in params),
                            'declared_question_index': params.get('question_index')
                                if type(params.get('question_index')) is int else None})
    if not commits:
        issues.append('NO_EVALUATOR_COMMIT_IN_SAVED_JOURNAL: UI screenshot shows a proposal, but persisted provenance not independently located; review schema/reopen behavior')
    if commits and not any(e['outcome'] == 'OK' for e in commits):
        issues.append('NO_SUCCESSFUL_EVALUATOR_COMMIT_IN_SAVED_JOURNAL')
    if len(candidate_actions) == 0:
        issues.append('NO_CANDIDATE_ACTIONS_RECOGNIZED: app may use a different action name; inspect exact journal schema locally')
    if question == 1:
        issues.append('C01_REVIEW: confirm explicit clarification/expectation alignment in frozen candidate evidence; no automatic grade from mere SQL submission')
        issues.append('C04_REVIEW: confirm a bounded help/gap-to-action behavior actually occurred; no help requests were visible in supplied UAT screenshot')
        issues.append('T02_REVIEW: model phrase "partially correct SQL" is not independently verified by any local SQL fixture; distinguish structural analysis from execution correctness')
    issues.append('SOURCE_SPANS_UNVERIFIED: model rationale, exact Event ID, UTF8 span and checksum must be matched to frozen source by reviewer')
    issues.append('MODEL_TRANSPORT_NOT_ATTESTED: saved Host commit and screenshot alone are not independent provider/billing receipts')
    return {'schema': 'tia-e4d02c-semantic-human-gate/v1',
            'question_number': question, 'save_file_sha256': file_digest,
            'document_sha256_valid': True, 'journal_entries': len(actions),
            'counts': dict(sorted(count.items())), 'candidate_actions_metadata': candidate_actions,
            'evaluator_commits_metadata': commits,
            'review_required': issues, 'gate': 'HUMAN_SEMANTIC_REVIEW_REQUIRED',
            'automatic_human_acceptance': False,
            'restrictions': {'paid_provider_calls': 0, 'source_modifications': 0,
                             'candidate_score_certified': False,
                             'personal_text_exported': False}}


def write_private(path: Path, data: bytes):
    """No symlink overwrite, new file exclusively; no accidental public report."""
    if path.exists() or path.is_symlink():
        raise GateError('OUTPUT_ALREADY_EXISTS')
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, 'O_NOFOLLOW', 0), PRIVATE_MODE)
    try:
        with os.fdopen(fd, 'wb') as f:
            f.write(data)
        os.chmod(path, PRIVATE_MODE)
    except Exception:
        try: path.unlink()
        except OSError: pass
        raise


def report_markdown(result):
    cm = result['candidate_actions_metadata']
    ev = result['evaluator_commits_metadata']
    issue_lines = '\n'.join(f'- [ ] {i}' for i in result['review_required'])
    return f'''# TIA E4-D/02C — Private Semantic Human Gate\n\n**Decision:** {result['gate']}  \n**Question:** Q{result['question_number']}  \n**Save integrity:** CHECKED (SHA-256 integrity only; NOT an authenticity signature)  \n**Journal entries:** {result['journal_entries']}  \n**Candidate command matches:** {len(cm)}  \n**Evaluator commit matches:** {len(ev)}  \n\n## Recorded actions (metadata only)\n\n```json\n{json.dumps(cm, indent=2, ensure_ascii=False)}\n```\n\n## Evaluator commits (metadata only)\n\n```json\n{json.dumps(ev, indent=2, ensure_ascii=False)}\n```\n\n## Human evidence review — before accepting any model-proposed scores\n\n{issue_lines}\n\n**Method:** Open the TIA App Q1, expand C01, C04 and T02, and compare each claimed quote, event reference, byte span and source hash with the actual frozen candidate event. Decide ACCEPT / MODIFY / BLOCKED *only after* semantic comparison. If a metric is unsupported, keep it NOT_OBSERVED; do not silently assign zero. T01 correctness remains NOT_OBSERVED without independently verified fixture output.\n\n**Privacy:** This report contains action metadata and digests only; it does not contain candidate submissions, model JSON replies, secrets or credential values. Keep the original app save on the Mac.\n'''


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--save',type=Path,required=True,help='Existing PRIVATE app tutorial-v1.json; read only')
    p.add_argument('--output-dir',type=Path,required=True,help='New private directory; script never overwrites')
    p.add_argument('--question',type=int,choices=(1,2,3),default=1)
    args=p.parse_args(argv)
    try:
        data, raw_sha=read_local_save(args.save.expanduser())
        result=scan(data,raw_sha,args.question)
        d=args.output_dir.expanduser()
        if d.exists() or d.is_symlink():
            raise GateError('OUTPUT_DIR_ALREADY_EXISTS')
        d.mkdir(mode=0o700,parents=False)
        os.chmod(d,0o700)
        write_private(d/'review_receipt.json', (json.dumps(result,indent=2,ensure_ascii=False)+'\n').encode('utf-8'))
        write_private(d/'HUMAN_REVIEW_Q1.md', report_markdown(result).encode('utf-8'))
    except GateError as e:
        print('E4D02C_SEMANTIC_GATE_ERROR='+str(e),file=sys.stderr)
        return 2
    except (OSError,ValueError,TypeError) as e:
        print('E4D02C_SEMANTIC_GATE_ERROR=IO_OR_SCHEMA_ERROR',file=sys.stderr)
        return 2
    print('E4D02C_SAVE_INTEGRITY=PASS')
    print('E4D02C_JOURNAL_ENTRIES='+str(result['journal_entries']))
    print('E4D02C_CANDIDATE_ACTION_MATCHES='+str(len(result['candidate_actions_metadata'])))
    print('E4D02C_EVALUATOR_COMMIT_MATCHES='+str(len(result['evaluator_commits_metadata'])))
    print('E4D02C_SEMANTIC_GATE='+result['gate'])
    print('E4D02C_NO_PAID_CALLS=YES NO_SOURCE_CHANGED=YES')
    print('E4D02C_PRIVATE_RECEIPT='+str(d/'HUMAN_REVIEW_Q1.md'))
    return 0

if __name__=='__main__':
    raise SystemExit(main())
