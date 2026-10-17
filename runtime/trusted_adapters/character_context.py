"""Build-time reviewed Markdown projection; runtime reads only a bounded artifact.

This is deliberately not a general Markdown prompt loader. Only named sections
and reviewed fields are projected, no includes, URLs, code, or instructions from
session data are evaluated. Authors remain trusted contributors; semantic review
is still required when changing story canon.
"""
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import re

VERSION = 'witness-character/v1'
FILES = ('identity.md', 'memory.md', 'user.md', 'narrator_intro.md', 'case_brief.md')
ARTIFACT = Path(__file__).with_name('witness_character.json')


def _json(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))


def section(text, heading):
    lines = text.splitlines()
    try:
        start = lines.index(heading) + 1
    except ValueError:
        raise ValueError('CHARACTER_REQUIRED_SECTION_MISSING') from None
    end = next((i for i in range(start, len(lines)) if lines[i].startswith('## ')), len(lines))
    return '\n'.join(lines[start:end]).strip()


def _reviewed(text, maximum=5000):
    if not text or len(text) > maximum or re.search(r'```|!\[|<\s*(?:script|iframe)|(?:ignore|override)\s+(?:all|previous|system)|\bsk-(?:proj-)?[A-Za-z0-9_-]{16,}', text, re.I):
        raise ValueError('CHARACTER_UNREVIEWED_CONTENT')
    return text


def _quotes(text):
    return '\n'.join(line[2:].strip().replace('**', '') for line in text.splitlines() if line.startswith('> '))


def compile_sources(directory, duplicate_directory=None):
    directory = Path(directory)
    sources, digests = {}, {}
    for name in FILES:
        path = directory / name
        if path.is_symlink() or not path.is_file() or path.stat().st_size > 50000:
            raise ValueError('CHARACTER_UNSAFE_SOURCE')
        raw = path.read_bytes()
        sources[name], digests[name] = raw.decode('utf-8'), sha256(raw).hexdigest()
    identity = section(sources['identity.md'], '## 1. Who I am')
    for invariant in ('林雾', 'Lin Wu', '27', 'younger brother', '林屿', 'Lin Yu', '周序', 'Zhou Xu'):
        if invariant not in identity:
            raise ValueError('CHARACTER_CANON_REVIEW_REQUIRED')
    if '- **Family:** younger brother 林屿 (Lin Yu, 23)' not in identity or '- **Name:** 林雾 (Lin Wu), codename Witness 07; **age:** 27.' not in identity:
        raise ValueError('CHARACTER_CANON_REVIEW_REQUIRED')
    persona = _reviewed(section(sources['identity.md'], '## 3. Stable personality — the soft rules'))
    private = section(sources['memory.md'], "## 3. Lin Wu's stable private memories (`NPC_KNOWS`)")
    def fact(prefix):
        line = next((line[2:] for line in private.splitlines() if line.startswith('- ' + prefix)), None)
        return _reviewed(line or '', 500)
    private_facts = {
        'call_0017': fact('She received an incoming call'),
        'raincoat': fact('She herself wore the red raincoat'),
        'timeline': fact('She deliberately gave the misleading'),
        'relation': fact('Zhou Xu is Lin Yu'),
    }
    starting = section(sources['user.md'], '## 2. What the player actually knows before entering the platform')
    reported = '\n'.join(line for line in starting.splitlines() if re.match(r'^[1-5]\. ', line))
    brief = _quotes(section(sources['case_brief.md'], '## 2. Player-safe case brief (safe to show on the opening card)'))
    narrator = _quotes(section(sources['narrator_intro.md'], '## Screen 1 — Pre-approach sound, empty station'))
    entrance_quotes = _quotes(section(sources['narrator_intro.md'], '## Screen 3 — Lin Wu enters (same location, no evidence occlusion)')).split('\n')
    intro = next((line.strip('“”') for line in entrance_quotes if '你来得比' in line), '')
    policy = section(sources['memory.md'], '## 1. Knowledge is not all one thing')
    policy = next((line.replace('**', '') for line in policy.splitlines() if line.startswith('**Invariant:**')), '')
    projection = {
        'invariants': {'name': 'Lin Wu / 林雾', 'age': 27, 'role': 'adult night railway dispatcher',
                       'brother': 'Lin Yu / 林屿', 'brother_exists': True,
                       'missing_person': 'Zhou Xu / 周序', 'station': 'Yunjiang / 云江站'},
        'personality': persona,
        'private_npc_knowledge': private_facts,
        'disclosure_policy': _reviewed(policy),
        'unknown': ['Zhou Xu current location', 'complete actions of any third party', 'future verdict'],
        'suspicions': {'status': 'UNCONFIRMED', 'release': 'NONE_IN_THIS_SPRINT'},
        'player_starting_knowledge': _reviewed(reported),
        'opening': {'case_brief': _reviewed(brief), 'narrator': _reviewed(narrator), 'intro': _reviewed(intro)},
        'call_events': {'recent': 'later interrupted outgoing call; recipient unreleased',
                        'historical': 'earlier incoming call at 00:17; caller gated'},
    }
    body = {'version': VERSION, 'sources': digests, 'projection': projection}
    artifact = dict(body, digest=sha256(_json(body).encode()).hexdigest())
    drift = []
    if duplicate_directory is not None:
        for name in FILES:
            path = Path(duplicate_directory) / name
            if not path.is_file() or sha256(path.read_bytes()).hexdigest() != digests[name]:
                drift.append(name)
    return artifact, drift


def load():
    if ARTIFACT.is_symlink() or ARTIFACT.stat().st_size > 40000:
        raise ValueError('CHARACTER_ARTIFACT_INVALID')
    artifact = json.loads(ARTIFACT.read_text(encoding='utf-8'))
    if set(artifact) != {'version', 'sources', 'projection', 'digest'} or artifact['version'] != VERSION:
        raise ValueError('CHARACTER_ARTIFACT_INVALID')
    body = {k: artifact[k] for k in ('version', 'sources', 'projection')}
    if sha256(_json(body).encode()).hexdigest() != artifact['digest']:
        raise ValueError('CHARACTER_ARTIFACT_DIGEST_MISMATCH')
    return artifact


def metadata():
    artifact = load()
    return {'version': artifact['version'], 'digest': artifact['digest'], 'source_digests': artifact['sources']}


def public_projection():
    value = load()['projection']
    return deepcopy({key: value[key] for key in ('opening', 'player_starting_knowledge')})


def model_projection(released):
    artifact = load()
    value = artifact['projection']
    return {'version': artifact['version'], 'digest': artifact['digest'],
            'CHARACTER_INVARIANTS': deepcopy(value['invariants']),
            'personality': value['personality'], 'DISCLOSURE_POLICY': value['disclosure_policy'],
            'NPC_UNKNOWN': value['unknown'], 'PLAYER_STARTING_KNOWLEDGE': value['player_starting_knowledge'],
            'AUTHORIZED_DISCLOSURES': [value['private_npc_knowledge'][key] for key in released if key in value['private_npc_knowledge']]}
