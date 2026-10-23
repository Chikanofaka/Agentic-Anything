#!/usr/bin/env python3
"""Local-only, explicitly approved PostgreSQL fixture grader.

Never accepts a database connection string and never touches an existing cluster.
"""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tia_runtime.sql_accuracy import AccuracyError, validate_fixture, grade_fixture  # noqa E402


def main():
    p = argparse.ArgumentParser(description='Review a fixture fingerprint; optionally execute an approved local SQL test.')
    p.add_argument('--fixture', type=Path, required=True)
    p.add_argument('--sql-file', type=Path)
    p.add_argument('--approve-fixture-sha256', default='')
    p.add_argument('--execute', action='store_true')
    args = p.parse_args()
    try:
        blob = args.fixture.read_bytes()
        fixture, digest = validate_fixture(blob)
        if not args.execute:
            print(json.dumps({'fixture_id': fixture['fixture_id'], 'sha256': digest,
                              'tables': [{'name': x['name'], 'rows': len(x['rows'])}
                                         for x in fixture['tables']],
                              'expected_rows': len(fixture['expected']['rows']),
                              'executable': False, 'status': 'AWAITING_HUMAN_DIGEST_APPROVAL'}, indent=2))
            return 0
        if args.sql_file is None or not args.approve_fixture_sha256:
            raise AccuracyError('SQL_FILE_AND_APPROVAL_REQUIRED')
        solution = args.sql_file.read_text(encoding='utf-8')
        result = grade_fixture(blob, solution, args.approve_fixture_sha256)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0 if result['result']['status'] == 'PASSED' else 2
    except (AccuracyError, OSError, UnicodeError) as e:
        code = e.code if isinstance(e, AccuracyError) else 'LOCAL_INPUT_UNAVAILABLE'
        print(json.dumps({'status': 'NOT_VERIFIED', 'error_code': code}), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
