"""Conservative evidence admissibility and static SQL signals (no execution).

This is a *necessary-condition* filter, NOT a semantic evaluator. Passing a rule
never proves a score, competence, SQL correctness, or interview quality.
All user/transcript text is treated as untrusted data.
"""
import re


def _has(text, pattern):
    return re.search(pattern, text, re.I | re.S) is not None


def eligible_aliases(identifier, candidates, replies, accuracy):
    """Return event aliases that can *possibly* support a criterion.

    Evidence kind labels alone are insufficient; candidate language or observed
    code must establish a minimally relevant behavior. Interviewer speech never
    becomes candidate evidence. A human must still check every semantic claim.
    """
    if identifier == 'C06':
        return []  # No dedicated spoken closure recorded by this product.
    if identifier == 'T01':
        return ([e['alias'] for e in candidates
                 if e['event_id'] == accuracy.get('candidate_event_id')]
                if accuracy.get('status') in ('PASSED', 'FAILED') else [])
    if identifier == 'C05':
        out = []
        for e in candidates:
            earlier_candidate = [x for x in candidates if x['position'] < e['position']]
            if not earlier_candidate:
                continue
            # The interviewer must have reacted to an already-observed candidate
            # turn; the initial question alone is NEVER collaboration evidence.
            last_candidate_position = earlier_candidate[-1]['position']
            feedback = [r for r in replies if
                        last_candidate_position < r['position'] < e['position'] and
                        _has(r['excerpt'], r'\b(your (?:query|plan|answer)|you (?:said|mentioned|used)|incorrect|issue|change|revise|fix|instead|feedback|explain|check|verify|consider)\b')]
            if not feedback:
                continue
            candidate_action = _has(e['excerpt'],
                r'\b(changed|revised|fixed|updated|corrected|instead|feedback|you (?:said|mentioned)|i (?:now|will|would)|we (?:now|will))\b')
            if not candidate_action:
                continue
            # For directive-only feedback (e.g. 'Explain the join cardinality'),
            # require nontrivial shared topic terms, not a generic 'I will'.
            stop = {'would', 'could', 'should', 'about', 'before', 'after', 'please',
                    'explain', 'check', 'verify', 'consider', 'using', 'where', 'their',
                    'there', 'these', 'those', 'because', 'first', 'next', 'then',
                    'think', 'answer', 'query', 'plan', 'your', 'with', 'from',
                    'have', 'will', 'need', 'just', 'them', 'this', 'that'}
            topics = lambda text: {t for t in re.findall(r'[a-z]{4,}', text.lower()) if t not in stop}
            if not any(topics(r['excerpt']) & topics(e['excerpt']) for r in feedback):
                continue
            out.append(e['alias'])
        return out
    out = []
    for e in candidates:
        s = e['excerpt'].strip()
        kind = e['kind']
        # SQL code is useful evidence for technical design but not for oral
        # clarification, progress narration, assistance, or debugging.
        code_only = _has(s, r'(?m)^\s*(?:--|select\s|with\s|def\s+\w+|class\s+\w+)') or (kind == 'implement' and _has(s, r'\bselect\b'))
        if identifier == 'T02':
            ok = _has(s, r'\b(select|join|over\s*\(|sum\s*\(|filter|where|first\s+order|\bcte\b|group\s+by|approach|algorithm|function|date|weight|calculate|compute)\b')
        elif identifier == 'T03':
            ok = _has(s, r'\b(firstly|then|next|plan|step|approach|before|after|group|filter|join|order\s+by|select|limit|window)\b')
        elif identifier == 'T04':
            ok = not code_only and _has(s, r'\b(i|we)\s+(?:have\s+)?(?:tested|ran|checked|debugged|verified|fixed|repaired|retried|reproduced)\b|\b(test\s+case\s+(?:passed|failed)|actual\s+output|error\s+message|root\s+cause|fails?\s+when|after\s+(?:running|testing))\b')
        elif identifier == 'T05':
            ok = _has(s, r'\b(performance|efficien\w*|optimi\w*|scalab\w*|index(?:es|ing)?|cost\s+of|complexity|o\s*\(\s*n|readab\w*|maintainab\w*|refactor\w*|materializ\w*|explain\s+analyze)\b')
        elif identifier == 'C01':
            ok = not code_only and not _has(s, r'^\s*(?:sorry\s+)?(?:can|could)\s+you\s+(?:please\s+)?repeat\b') and (
                _has(s, r'\b(clarify|assum\w*|confirm|constraint|requirement|expected|percentage|round\s+to|output\s+is)\b')
                or '?' in s and _has(s, r'\b(what|which|whether|how|if)\b'))
        elif identifier == 'C02':
            ok = not code_only and _has(s, r'\b(my\s+plan|firstly|first\s+i|we\s+(?:will|need|want)|because|so\s+i\s+(?:will|would)|then\s+(?:i|we)|next\s+(?:i|we)|in\s+order\s+to)\b')
        elif identifier == 'C03':
            ok = not code_only and _has(s, r'\b(i|we)\s+(?:have\s+)?(?:ran|tested|verified|checked|completed|submitted|found|observed|got)\b|\b(after\s+(?:running|executing)|passed\s+the\s+test)\b')
        elif identifier == 'C04':
            ok = not code_only and _has(s, r'\b(i\s+(?:am\s+)?(?:stuck|unsure|not\s+sure)|\bproblem\s+is\b|\bgap\s+is\b|\bblocker\b|\bcan\s+you\s+help\s+(?:me\s+)?(?:with|check)|\bcould\s+we\s+(?:test|verify|check)|\bto\s+resolve\b)')
        else:
            ok = False
        if ok:
            out.append(e['alias'])
    return out


def reason_self_contradicts(reason):
    """Reject an anchored positive claim that explicitly denies its own evidence."""
    return _has(reason.strip(), r'^(?:no\s+evidence\s+(?:of|for)|not\s+observed\b|there\s+is\s+no\s+evidence|no\s+(?:testing|debugging|clarification|explanation|narration|progress|help|repair)\s+(?:observed|performed|provided))')


def static_sql_signals(question, candidates):
    """Narrow read-only *structural* review; NEVER a PASSED SQL result."""
    sqls = [e for e in candidates if e['kind'] == 'implement' and _has(e['excerpt'], r'\bselect\b')]
    if not sqls:
        return {'status': 'NO_SQL_SUBMISSION', 'execution': 'NOT_RUN', 'correctness': 'NOT_VERIFIED'}
    chosen = sqls[-1]
    sql = chosen['excerpt']
    result = {'status': 'STATIC_REVIEW_ONLY', 'execution': 'NOT_RUN',
              'correctness': 'NOT_VERIFIED', 'candidate_event_id': chosen['event_id'],
              'candidate_text_sha256': chosen['text_sha256'], 'excerpt_truncated': chosen['excerpt_truncated']}
    if _has(question.get('title', ''), r'last\s+person\s+to\s+fit\s+in\s+the\s+bus'):
        patterns = {
            'running_total': r'\bsum\s*\(\s*weight\s*\)\s*over\s*\(\s*order\s+by\s+turn\b',
            'cumulative_frame': r'\brows\s+between\s+unbounded\s+preceding\s+and\s+current\s+row\b',
            'capacity_filter': r'\bwhere\s+\w+\s*<=\s*1000\b',
            'latest_fitting_turn': r'\border\s+by\s+turn\s+desc\s+limit\s+1\b',
            'person_name_output': r'\bselect\s+person_name\b',
        }
        checks = {k: _has(sql, p) for k,p in patterns.items()}
        result.update(structural_signals=checks,
                      structural_match_all=all(checks.values()),
                      confidence='HEURISTIC_PATTERN_ONLY_NOT_A_SQL_PARSER',
                      note='Static match is not PostgreSQL execution, hidden-test success or T01 grading.',
                      dialect_note='FROM subqueries without aliases require PostgreSQL 16+; older PostgreSQL requires aliases.'
                          if len(re.findall(r'\bfrom\s*\(', sql, re.I)) else 'PostgreSQL compatibility unverified.')
    return result
