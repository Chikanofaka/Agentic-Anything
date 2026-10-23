"""Bounded native-worker contracts. No transport, credentials, or model authority."""

import re

from .controller import SessionError


PREPARE_FIELDS = {'request_id', 'generation', 'operation', 'text', 'kind', 'mechanism'}
COMMIT_FIELDS = {'transaction_id', 'request_id', 'generation', 'reply', 'model', 'usage'}
MECHANISMS = ('STRICT_CHALLENGING', 'PROFESSIONAL_SUPPORTIVE')


def _text(value, limit, nonempty=True):
    if type(value) is not str or (nonempty and not value.strip()):
        raise SessionError('INVALID_NATIVE_REQUEST')
    try:
        if len(value.encode('utf-8')) > limit:
            raise SessionError('NATIVE_INPUT_TOO_LARGE')
    except UnicodeError:
        raise SessionError('INVALID_NATIVE_REQUEST') from None


def _identifier(value):
    if type(value) is not str or not re.fullmatch(r'[A-Za-z0-9_-]{1,80}', value):
        raise SessionError('INVALID_NATIVE_REQUEST')


def validate_prepare(params):
    if type(params) is not dict or set(params) != PREPARE_FIELDS:
        raise SessionError('INVALID_NATIVE_REQUEST')
    for key in ('request_id', 'generation'):
        _identifier(params[key])
    if (params['operation'] not in ('verify', 'reply')
            or params['mechanism'] not in MECHANISMS
            or params['kind'] not in ('clarify', 'plan', 'help', 'implement', 'test')):
        raise SessionError('INVALID_NATIVE_REQUEST')
    _text(params['text'], 4096, nonempty=params['operation'] == 'reply')
    if params['operation'] == 'verify' and (params['text'] != '' or params['kind'] != 'clarify'):
        raise SessionError('INVALID_NATIVE_REQUEST')


def validate_commit(params):
    if type(params) is not dict or set(params) != COMMIT_FIELDS:
        raise SessionError('INVALID_NATIVE_REQUEST')
    for key in ('transaction_id', 'request_id', 'generation'):
        _identifier(params[key])
    if type(params['transaction_id']) is not str or not re.fullmatch(r'[a-f0-9]{64}', params['transaction_id']):
        raise SessionError('INVALID_NATIVE_REQUEST')
    reply = params['reply']
    if type(reply) is not dict or set(reply) != {'reply'}:
        raise SessionError('INVALID_NATIVE_REPLY')
    _text(reply['reply'], 8000)
    if len(reply['reply']) > 2000:
        raise SessionError('INVALID_NATIVE_REPLY')
    model = params['model']
    if type(model) is not str or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]{0,79}', model):
        raise SessionError('INVALID_NATIVE_REPLY')
    usage = params['usage']
    if usage is not None:
        if (type(usage) is not dict or set(usage) != {'input_tokens', 'output_tokens', 'total_tokens'}
                or any(type(value) is not int or not 0 <= value <= 100000000 for value in usage.values())
                or usage['total_tokens'] != usage['input_tokens'] + usage['output_tokens']):
            raise SessionError('INVALID_NATIVE_USAGE')
