"""Versioned value contracts owned by HAL's reviewed specialist adapters.

Manifest contract identifiers select a reviewed contract; they cannot redefine it.
Validators do not include rejected values in their error messages.
"""
from __future__ import annotations

import math


class ValueContractError(ValueError):
    pass


def _fields(value, expected):
    if not isinstance(value, dict) or set(value) != set(expected):
        raise ValueContractError('VALUE_CONTRACT_FIELDS_MISMATCH')


def _number(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueContractError('VALUE_CONTRACT_EXPECTED_NUMBER')
    try:
        finite = math.isfinite(value)
    except (OverflowError, ValueError):
        finite = False
    if not finite:
        raise ValueContractError('VALUE_CONTRACT_NON_FINITE_NUMBER')


def _research_input(value):
    _fields(value, ('revenue', 'cost'))
    _number(value['revenue'])
    _number(value['cost'])
    if value['revenue'] <= 0 or value['cost'] < 0:
        raise ValueContractError('VALUE_CONTRACT_AMOUNT_RANGE')


def _research_output(value):
    _fields(value, ('profit', 'margin_pct', 'unit', 'rule'))
    _number(value['profit'])
    _number(value['margin_pct'])
    if value['unit'] != 'user_supplied_units' or value['rule'] != 'margin-v1':
        raise ValueContractError('VALUE_CONTRACT_RESULT_CONSTANT')


def _returns_input(value):
    _fields(value, ('condition', 'proof', 'days'))
    if value['condition'] not in ('sealed', 'opened', 'damaged') or value['proof'] not in ('yes', 'no'):
        raise ValueContractError('VALUE_CONTRACT_ENUM')
    if type(value['days']) is not int or not 0 <= value['days'] <= 365:
        raise ValueContractError('VALUE_CONTRACT_DAYS_RANGE')


def _returns_output(value):
    _fields(value, ('classification', 'rule', 'not_a_real_business_policy'))
    if value['classification'] not in ('MANUAL_REVIEW', 'INSPECT', 'STANDARD_RETURN', 'OUT_OF_WINDOW'):
        raise ValueContractError('VALUE_CONTRACT_ENUM')
    if value['rule'] != 'fictional-returns-v1' or value['not_a_real_business_policy'] is not True:
        raise ValueContractError('VALUE_CONTRACT_RESULT_CONSTANT')


VALUE_CONTRACTS = {
    'research-margin-input/v1': _research_input,
    'research-margin-output/v1': _research_output,
    'returns-triage-input/v1': _returns_input,
    'returns-triage-output/v1': _returns_output,
}


def validate_value(contract_id: str, value) -> None:
    validator = VALUE_CONTRACTS.get(contract_id)
    if validator is None:
        raise ValueContractError('UNKNOWN_VALUE_CONTRACT')
    validator(value)
