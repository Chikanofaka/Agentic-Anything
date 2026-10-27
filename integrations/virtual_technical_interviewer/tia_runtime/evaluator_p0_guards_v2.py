"""Versioned bilingual necessary-condition filters for complete-conversation review.

These gates exclude known inadmissible claims. They never establish semantic
truth, score authority or SQL execution. Legacy gates stay byte-for-byte intact.
"""
import re
from .evaluator_p0_guards import eligible_aliases as legacy_aliases
from .evaluator_p0_guards import reason_self_contradicts as legacy_contradiction


def _has(text, expression):
    return re.search(expression, text, re.I | re.S) is not None


def _code_only(text):
    text = re.sub(r'^\s*```(?:sql|python)?\s*', '', text.strip(), flags=re.I)
    text = re.sub(r'(?m)^\s*--[^\n]*\n?', '', text)
    return _has(text, r'^\s*(?:SELECT\b|WITH\b|def\s+\w+|class\s+\w+|import\s+\w+|from\s+\w+\s+import\b)')


def eligible_aliases(identifier, candidates, replies, accuracy):
    if identifier in ('T01', 'C06'):
        return legacy_aliases(identifier, candidates, replies, accuracy)
    english = set(legacy_aliases(identifier, candidates, replies, accuracy))
    out = []
    zh = {
        'T02': r'连接|联接|聚合|窗口函数|分组|算法|函数|日期|排序|求和|计算',
        'T03': r'首先|然后|接着|计划|步骤|分组|过滤|排序|拆分|边界',
        'T04': r'(?:我|我们)(?:已经|刚刚|已)?(?:测试|运行|检查|验证|修复|排查|重现)|实际输出|错误信息|根因|测试(?:通过|失败)',
        'T05': r'复杂度|性能|索引|效率|成本|可读性|可维护|优化|空间开销',
        'C01': r'澄清|确认|假设|约束|预期|期望输出|需求|是否|请问',
        'C02': r'我的计划|首先我|我们(?:将|需要|先)|因为|然后我|为了',
        'C03': r'(?:我|我们)(?:已经|已)?(?:运行|测试|验证|检查|完成|提交|发现)|实际(?:结果|输出)',
        'C04': r'我(?:不确定|卡在|不清楚)|困难在|不确定的地方|能否(?:帮助|检查)|可否(?:验证|检查)|请帮我',
    }
    for entry in candidates:
        text = entry['excerpt']
        code = _code_only(text)
        if (identifier.startswith('C') or identifier == 'T04') and code:
            continue
        allowed = entry['alias'] in english
        if identifier in zh and _has(text, zh[identifier]):
            allowed = True
        if identifier == 'C05' and not allowed:
            # Speaker role and chronological pairing matter; the user-selected
            # clarify/plan label is not proof of (or a bar to) communication.
            before = [e for e in candidates if e['position'] < entry['position']]
            if before:
                feedback = [r for r in replies if before[-1]['position'] < r['position'] < entry['position']]
                action = _has(text, r'我(?:现在|会|将|已经)|改为|改成|修改|修复|调整|你(?:刚才|提到|说)|根据.*建议')
                cue = any(_has(r['excerpt'], r'你(?:的|刚才|提到)|错误|问题|修改|修复|检查|验证|考虑|建议') for r in feedback)
                # Require a shared substantive Chinese phrase or English topic.
                terms = lambda value: set(re.findall(r'[a-z]{4,}|[\u4e00-\u9fff]{2}', value.lower()))
                shared = any((terms(text) & terms(r['excerpt'])) - {'现在', '刚才', '修改', '建议', '问题'} for r in feedback)
                allowed = bool(action and cue and shared)
        # A denial is not affirmative evidence of testing/progress, including
        # a turn whose kind happens to be test or plan.
        if identifier in ('T04', 'C03') and _has(text, r'\b(?:not|never|haven.t|didn.t)\s+(?:yet\s+)?(?:test|run|check|verif)|(?:没有|尚未|还没|未)(?:进行)?(?:测试|运行|验证|检查)'):
            allowed = False
        if allowed:
            out.append(entry['alias'])
    return out


def reason_self_contradicts(reason):
    return legacy_contradiction(reason) or _has(reason, r'\bno\s+(?:explicit|actual|observed|direct|supporting)\s+(?:repair|testing|debugging|evidence|details)|(?:没有|无|缺乏|未观察到)(?:明确|实际|相关)?(?:证据|测试|调试|修复)')
