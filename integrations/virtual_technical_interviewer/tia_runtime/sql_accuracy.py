"""S03-E2.5A: human-approved fixture comparison with ephemeral local PostgreSQL.

No external DSNs or persistent databases are accepted. This narrow runner
requires PostgreSQL *server binaries* and a non-root OS user. A new cluster is
created per execution with a private Unix socket and a read-only, non-superuser
SQL role. It is a development/practice sandbox, not a certified hostile-code VM.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import os
from pathlib import Path
import re
import secrets
import shutil
import subprocess
import tempfile


class AccuracyError(ValueError):
    """Typed fail-closed outcome; never substitute an AI-generated score."""
    def __init__(self, code):
        self.code = code
        super().__init__(code)


SCHEMA = 'tia-postgres-fixture/v1'
IDENT = re.compile(r'[A-Za-z_][A-Za-z0-9_]{0,62}\Z')
SHA = re.compile(r'[0-9a-f]{64}\Z')
SQL_TYPES = frozenset(('INTEGER', 'BIGINT', 'SMALLINT', 'TEXT', 'DATE',
                       'TIMESTAMP', 'BOOLEAN', 'NUMERIC', 'DOUBLE PRECISION'))
MAX_ROWS = 1000
MAX_FIXTURE_BYTES = 262144
MAX_SQL_BYTES = 8192
MAX_OUTPUT_BYTES = 262144
NULL_MARKER_PREFIX = '__TIA_RESULT_NULL_'
DENIED_FUNCTIONS = re.compile(
    r'\b(?:pg_sleep|pg_read_file|pg_ls_dir|pg_stat_file|pg_terminate_backend|'
    r'pg_cancel_backend|set_config|dblink|lo_export|lo_import|pg_write_file)\s*\(',
    re.IGNORECASE,
)


def _str(value, *, limit=512):
    if type(value) is not str or not value or len(value.encode('utf-8')) > limit or '\x00' in value:
        raise AccuracyError('INVALID_FIXTURE_STRING')
    return value


def _identifier(value):
    if type(value) is not str or not IDENT.fullmatch(value):
        raise AccuracyError('INVALID_SQL_IDENTIFIER')
    return value.lower()


def _value(value):
    if value is None or type(value) is bool or type(value) is int:
        return value
    if type(value) is float and math.isfinite(value):
        return value
    if type(value) is str and len(value.encode('utf-8')) <= 2048 and '\x00' not in value:
        return value
    raise AccuracyError('UNSUPPORTED_FIXTURE_VALUE')


def validate_fixture(blob: bytes) -> tuple[dict, str]:
    if type(blob) is not bytes or not 0 < len(blob) <= MAX_FIXTURE_BYTES:
        raise AccuracyError('INVALID_FIXTURE_SIZE')
    try:
        fixture = json.loads(blob, parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)),
                             object_pairs_hook=_no_duplicate_keys)
    except (ValueError, TypeError, UnicodeError, RecursionError):
        raise AccuracyError('INVALID_FIXTURE_JSON') from None
    if (type(fixture) is not dict or set(fixture) != {
            'schema', 'fixture_id', 'question_sha256', 'environment', 'tables', 'expected'}
            or fixture['schema'] != SCHEMA or fixture['environment'] != 'POSTGRESQL'):
        raise AccuracyError('INVALID_FIXTURE_CONTRACT')
    _str(fixture['fixture_id'], limit=80)
    if type(fixture['question_sha256']) is not str or not SHA.fullmatch(fixture['question_sha256']):
        raise AccuracyError('INVALID_QUESTION_DIGEST')
    tables = fixture['tables']
    if type(tables) is not list or not 1 <= len(tables) <= 8:
        raise AccuracyError('INVALID_FIXTURE_TABLES')
    seen = set()
    total_rows = 0
    for table in tables:
        if type(table) is not dict or set(table) != {'name', 'columns', 'rows'}:
            raise AccuracyError('INVALID_FIXTURE_TABLE')
        tname = _identifier(table['name'])
        if tname in seen:
            raise AccuracyError('DUPLICATE_FIXTURE_TABLE')
        seen.add(tname)
        cols = table['columns']
        if type(cols) is not list or not 1 <= len(cols) <= 32:
            raise AccuracyError('INVALID_FIXTURE_COLUMNS')
        cnames = set()
        for col in cols:
            if type(col) is not dict or set(col) != {'name', 'type'}:
                raise AccuracyError('INVALID_FIXTURE_COLUMN')
            cname = _identifier(col['name'])
            if cname in cnames or col['type'] not in SQL_TYPES:
                raise AccuracyError('INVALID_FIXTURE_COLUMN')
            cnames.add(cname)
        rows = table['rows']
        if type(rows) is not list or len(rows) > MAX_ROWS:
            raise AccuracyError('INVALID_FIXTURE_ROWS')
        total_rows += len(rows)
        for row in rows:
            if type(row) is not list or len(row) != len(cols):
                raise AccuracyError('INVALID_FIXTURE_ROW_WIDTH')
            for cell in row:
                _value(cell)
    if total_rows > MAX_ROWS:
        raise AccuracyError('TOO_MANY_FIXTURE_ROWS')
    expected = fixture['expected']
    if type(expected) is not dict or set(expected) != {'columns', 'rows', 'order_sensitive'}:
        raise AccuracyError('INVALID_EXPECTED_RESULT')
    if type(expected['order_sensitive']) is not bool:
        raise AccuracyError('INVALID_RESULT_ORDER_POLICY')
    cols = expected['columns']
    rows = expected['rows']
    if (type(cols) is not list or not 1 <= len(cols) <= 32 or
            type(rows) is not list or len(rows) > MAX_ROWS):
        raise AccuracyError('INVALID_EXPECTED_RESULT')
    expected_names = [_identifier(x) for x in cols]
    if len(expected_names) != len(set(expected_names)):
        raise AccuracyError('INVALID_EXPECTED_COLUMNS')
    for row in rows:
        if type(row) is not list or len(row) != len(cols):
            raise AccuracyError('INVALID_EXPECTED_ROW')
        for cell in row:
            _value(cell)
    # Source bytes, not model metadata, determine the human approval fingerprint.
    return fixture, hashlib.sha256(blob).hexdigest()


def _no_duplicate_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate JSON key')
        result[key] = value
    return result


def validate_solution(query: str) -> str:
    if type(query) is not str or not query.strip():
        raise AccuracyError('EMPTY_SQL_SUBMISSION')
    try:
        byte_size = len(query.encode('utf-8'))
    except UnicodeError:
        raise AccuracyError('INVALID_SQL_ENCODING') from None
    if byte_size > MAX_SQL_BYTES or '\x00' in query:
        raise AccuracyError('INVALID_SQL_SIZE')
    # Deliberately conservative. This is NOT a SQL parser or a security boundary.
    # The isolated DB role and read-only transaction supply the primary boundary.
    query = query.strip()
    if query.endswith(';'):
        query = query[:-1].rstrip()
    if (';' in query or '\\' in query or not re.match(r'(?is)^(SELECT|WITH)\b', query)
            or DENIED_FUNCTIONS.search(query)):
        raise AccuracyError('SQL_READ_ONLY_SINGLE_STATEMENT_REQUIRED')
    return query


def _quote_identifier(name):
    return '"' + _identifier(name).replace('"', '""') + '"'


def _sql_literal(value):
    value = _value(value)
    if value is None:
        return 'NULL'
    if type(value) is bool:
        return 'TRUE' if value else 'FALSE'
    if type(value) in (int, float):
        return str(value)
    return "'" + value.replace("'", "''") + "'"


def bootstrap_sql(fixture):
    """Trusted human-reviewed data ONLY; candidate SQL never enters this script."""
    script = [
        'BEGIN;',
        'REVOKE CREATE ON SCHEMA public FROM PUBLIC;',
        'CREATE SCHEMA tia_fixture;',
    ]
    for table in fixture['tables']:
        name = 'tia_fixture.' + _quote_identifier(table['name'])
        columns = ', '.join(_quote_identifier(c['name']) + ' ' + c['type'] for c in table['columns'])
        script.append('CREATE TABLE ' + name + ' (' + columns + ');')
        for row in table['rows']:
            script.append('INSERT INTO ' + name + ' VALUES (' + ', '.join(map(_sql_literal, row)) + ');')
    script.extend([
        'CREATE ROLE tia_candidate LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION;',
        'REVOKE ALL ON SCHEMA public FROM tia_candidate;',
        'GRANT USAGE ON SCHEMA tia_fixture TO tia_candidate;',
        'GRANT SELECT ON ALL TABLES IN SCHEMA tia_fixture TO tia_candidate;',
        "ALTER ROLE tia_candidate SET search_path TO tia_fixture, pg_catalog;",
        'ALTER ROLE tia_candidate SET default_transaction_read_only TO on;',
        'COMMIT;',
    ])
    return '\n'.join(script) + '\n'


def _expected_display(value):
    if value is None:
        return None
    if type(value) is bool:
        return 't' if value else 'f'
    return str(value)


def compare_result(fixture, actual_columns, actual_rows):
    if type(actual_columns) is not list or type(actual_rows) is not list:
        raise AccuracyError('INVALID_EXECUTION_OUTPUT')
    expected = fixture['expected']
    ex_cols = [_identifier(x) for x in expected['columns']]
    if len(actual_columns) != len(ex_cols) or len(actual_rows) > MAX_ROWS:
        return False, 'COLUMN_COUNT_MISMATCH' if len(actual_columns) != len(ex_cols) else 'OUTPUT_ROW_LIMIT'
    if [_identifier(x) for x in actual_columns] != ex_cols:
        return False, 'COLUMN_NAMES_MISMATCH'
    erows = [[_expected_display(v) for v in row] for row in expected['rows']]
    if not all(type(row) is list and len(row) == len(ex_cols) for row in actual_rows):
        raise AccuracyError('INVALID_EXECUTION_OUTPUT')
    if expected['order_sensitive']:
        return (erows == actual_rows), ('PASS' if erows == actual_rows else 'ROWS_MISMATCH')
    a = sorted(json.dumps(row, ensure_ascii=True) for row in actual_rows)
    b = sorted(json.dumps(row, ensure_ascii=True) for row in erows)
    return a == b, ('PASS' if a == b else 'ROWS_MISMATCH')


def _postgres_bins(pg_config='pg_config'):
    exe = shutil.which(pg_config)
    if not exe:
        raise AccuracyError('POSTGRES_SERVER_NOT_AVAILABLE')
    result = subprocess.run([exe, '--bindir'], capture_output=True, text=True, timeout=4)
    if result.returncode:
        raise AccuracyError('POSTGRES_SERVER_NOT_AVAILABLE')
    bindir = Path(result.stdout.strip())
    binaries = {name: bindir / name for name in ('initdb', 'pg_ctl', 'psql')}
    if not all(p.is_file() and os.access(p, os.X_OK) for p in binaries.values()):
        raise AccuracyError('POSTGRES_SERVER_NOT_AVAILABLE')
    return binaries


def _pg_environment():
    env = {k: v for k, v in os.environ.items() if not k.upper().startswith('PG')}
    env['PGAPPNAME'] = 'TIA-ephemeral-fixture-grader'
    return env


def _run(argv, *, env, timeout=12, input=None):
    try:
        result = subprocess.run([str(x) for x in argv], input=input, text=True,
                                capture_output=True, timeout=timeout, env=env, check=False)
    except subprocess.TimeoutExpired:
        raise AccuracyError('SQL_PROCESS_TIMEOUT') from None
    except OSError:
        raise AccuracyError('POSTGRES_PROCESS_FAILED') from None
    return result


def _postgres_run(fixture, query, *, pg_config='pg_config', private_query=False):
    if hasattr(os, 'geteuid') and os.geteuid() == 0:
        raise AccuracyError('REFUSE_TO_RUN_POSTGRES_AS_ROOT')
    bins = _postgres_bins(pg_config)
    env = _pg_environment()
    with tempfile.TemporaryDirectory(prefix='tia_pg_') as root:
        r = Path(root)
        socket_dir = r / 'socket'
        pgdata = r / 'cluster'
        socket_dir.mkdir(mode=0o700)
        r.chmod(0o700)
        port = 20000 + secrets.randbelow(30000)
        initialized = _run([bins['initdb'], '-D', pgdata, '-U', 'tia_owner',
                            '--auth-local=trust', '--auth-host=reject', '--no-instructions',
                            '--locale=C', '--encoding=UTF8'],
                           env=env, timeout=30)
        if initialized.returncode:
            raise AccuracyError('ISOLATED_INITDB_FAILED')
        # Config is generated by us. No listening TCP sockets; socket dir is 0700.
        conf = pgdata / 'postgresql.conf'
        with conf.open('a', encoding='utf-8') as stream:
            stream.write("\nlisten_addresses = ''\n")
            stream.write("unix_socket_directories = '" + str(socket_dir).replace("'", "''") + "'\n")
            stream.write('unix_socket_permissions = 0700\n')
            stream.write('port = ' + str(port) + '\n')
            stream.write('statement_timeout = 4000\n')
            stream.write('lock_timeout = 1000\n')
            stream.write('idle_in_transaction_session_timeout = 5000\n')
            stream.write('temp_file_limit = 16384\n')
            stream.write('max_connections = 12\n')
            if private_query:
                stream.write("log_statement = 'none'\nlog_min_error_statement = 'panic'\n")
            stream.write('standard_conforming_strings = on\n')
        attempted_start = False
        try:
            attempted_start = True
            start = _run([bins['pg_ctl'], '-D', pgdata, '-l', r / 'postgres.log',
                          '-w', '-t', '15', 'start'], env=env, timeout=25)
            if start.returncode:
                raise AccuracyError('ISOLATED_POSTGRES_START_FAILED')
            common = [bins['psql'], '-h', socket_dir, '-p', str(port), '-d', 'postgres',
                      '-X', '-w', '-v', 'ON_ERROR_STOP=1']
            script = r / 'fixture.sql'
            script.write_text(bootstrap_sql(fixture), encoding='utf-8')
            boot = _run(common + ['-U', 'tia_owner', '-f', script], env=env, timeout=20)
            if boot.returncode:
                raise AccuracyError('FIXTURE_BOOTSTRAP_FAILED')
            role = _run(common + ['-U', 'tia_candidate', '-A', '-t', '-c',
                                  'SELECT current_user, rolcanlogin, rolsuper, rolcreatedb, rolcreaterole '
                                  'FROM pg_roles WHERE rolname = current_user'],
                        env=env, timeout=6)
            if role.returncode or role.stdout.strip() != 'tia_candidate|t|f|f|f':
                raise AccuracyError('CANDIDATE_ROLE_NOT_ISOLATED')
            readonly = _run(common + ['-U', 'tia_candidate', '-A', '-t', '-c',
                                      'SHOW default_transaction_read_only'], env=env, timeout=6)
            if readonly.returncode or readonly.stdout.strip() != 'on':
                raise AccuracyError('CANDIDATE_TRANSACTION_NOT_READONLY')
            # Exactly one validated SELECT / WITH command; psql --csv handles
            # quoted delimiters. No implicit default DSN or caller-supplied URI.
            null_marker = NULL_MARKER_PREFIX + secrets.token_hex(16) + '__'
            query_args = ['-f', '-'] if private_query else ['-c', query]
            run = _run(common + ['-U', 'tia_candidate', '--csv', '-P', 'null=' + null_marker] +
                       query_args, env=env, timeout=7, **({'input': query + ';\n'} if private_query else {}))
            if run.returncode:
                return {'status': 'EXECUTION_ERROR', 'error_code': 'POSTGRES_QUERY_ERROR',
                        'columns': None, 'rows': None}
            if len(run.stdout.encode('utf-8')) > MAX_OUTPUT_BYTES:
                raise AccuracyError('OUTPUT_BYTES_EXCEEDED')
            try:
                csv_rows = list(csv.reader(io.StringIO(run.stdout)))
            except csv.Error:
                raise AccuracyError('INVALID_POSTGRES_CSV') from None
            if not csv_rows:
                raise AccuracyError('MISSING_RESULT_COLUMNS')
            cols = csv_rows[0]
            rows = [[None if cell == null_marker else cell for cell in row] for row in csv_rows[1:]]
            passed, reason = compare_result(fixture, cols, rows)
            return {'status': 'PASSED' if passed else 'FAILED', 'reason': reason,
                    'columns': cols[:32], 'rows': rows[:20],
                    'actual_row_count': len(rows), 'expected_row_count': len(fixture['expected']['rows'])}
        finally:
            if attempted_start:
                try:
                    _run([bins['pg_ctl'], '-D', pgdata, '-m', 'immediate', '-w', '-t', '8', 'stop'],
                         env=env, timeout=12)
                except AccuracyError:
                    # Teardown errors never replace the original execution result.
                    pass


def grade_fixture(blob: bytes, solution: str, approval_sha256: str,
                  *, pg_config='pg_config', private_query=False) -> dict:
    fixture, digest = validate_fixture(blob)
    if type(approval_sha256) is not str or approval_sha256 != digest:
        raise AccuracyError('HUMAN_FIXTURE_APPROVAL_REQUIRED')
    query = validate_solution(solution)
    result = _postgres_run(fixture, query, pg_config=pg_config, **({'private_query': True} if private_query else {}))
    return {
        'schema': 'tia-local-sql-accuracy/v1',
        'source': 'EPHEMERAL_POSTGRESQL_LOCAL',
        'fixture_id': fixture['fixture_id'],
        'fixture_sha256': digest,
        'question_sha256': fixture['question_sha256'],
        'candidate_sql_sha256': hashlib.sha256(solution.encode('utf-8')).hexdigest(),
        'official_hidden_tests': False,
        'correctness': ('VERIFIED_LOCAL_FIXTURE' if result['status'] in ('PASSED', 'FAILED', 'EXECUTION_ERROR')
                        else 'NOT_VERIFIED'),
        'passed_fixtures': 1 if result['status'] == 'PASSED' else 0,
        'total_approved_fixtures': 1,
        'result': result,
    }
