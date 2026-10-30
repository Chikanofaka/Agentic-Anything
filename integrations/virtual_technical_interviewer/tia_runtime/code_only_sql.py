"""Conservative syntax recognition for a recorded-communication observation.

This is neither a SQL validator nor a correctness/security boundary. Recognize a
small SELECT/WITH grammar only; comments, prose and unsupported syntax must keep
semantic review available. No SQL is executed and no names/types are resolved.
"""
import re

_TOKEN = re.compile(r'''\s+|(?P<string>'(?:[^']|'')*')|(?P<quoted>"(?:[^"]|"")+")|(?P<number>\d+(?:\.\d+)?)|(?P<word>[A-Za-z_][A-Za-z_0-9]*)|(?P<symbol>::|<=|>=|<>|!=|\|\||[(),.*+/%=<>;\-])''')
_RESERVED = frozenset('SELECT WITH AS DISTINCT ALL FROM WHERE GROUP BY HAVING ORDER ASC DESC NULLS FIRST LAST LIMIT OFFSET JOIN LEFT RIGHT INNER OUTER FULL CROSS ON USING UNION INTERSECT EXCEPT AND OR NOT IS NULL TRUE FALSE IN LIKE ILIKE BETWEEN CASE WHEN THEN ELSE END OVER PARTITION ROWS RANGE UNBOUNDED PRECEDING FOLLOWING CURRENT ROW'.split())
_BINARY = frozenset(('+', '-', '*', '/', '%', '=', '<', '>', '<=', '>=', '<>', '!=', '||', 'AND', 'OR', 'LIKE', 'ILIKE'))


class _Uncertain(ValueError):
    pass


class _Select:
    def __init__(self, tokens):
        self.tokens = tokens
        self.index = 0

    def peek(self):
        return self.tokens[self.index][1] if self.index < len(self.tokens) else ''

    def take(self, value):
        if self.peek() == value:
            self.index += 1
            return True
        return False

    def need(self, value):
        if not self.take(value):
            raise _Uncertain()

    def is_name(self):
        if self.index == len(self.tokens):
            return False
        kind, value = self.tokens[self.index]
        return kind == 'quoted' or (kind == 'word' and value not in _RESERVED)

    def name(self):
        if not self.is_name():
            raise _Uncertain()
        self.index += 1

    def alias(self):
        if self.take('AS'):
            self.name()
        elif self.is_name():
            self.name()

    def expressions(self, *, aliases=False, ordered=False):
        while True:
            self.expression()
            if aliases:
                self.alias()
            if ordered:
                self.take('ASC') or self.take('DESC')
                if self.take('NULLS') and not (self.take('FIRST') or self.take('LAST')):
                    raise _Uncertain()
            if not self.take(','):
                break

    def expression(self):
        self.atom()
        while True:
            if self.peek() in _BINARY:
                self.index += 1
                self.atom()
            elif self.take('IS'):
                self.take('NOT')
                if not (self.take('NULL') or self.take('TRUE') or self.take('FALSE')):
                    raise _Uncertain()
            elif self.take('IN'):
                self.need('(')
                if self.peek() in ('SELECT', 'WITH'):
                    self.query()
                else:
                    self.expressions()
                self.need(')')
            else:
                break

    def atom(self):
        if self.take('+') or self.take('-') or self.take('NOT'):
            self.atom()
        elif self.take('('):
            if self.peek() in ('SELECT', 'WITH'):
                self.query()
            else:
                self.expressions()
            self.need(')')
        elif self.take('CASE'):
            if self.peek() != 'WHEN':
                self.expression()
            self.need('WHEN')
            while True:
                self.expression(); self.need('THEN'); self.expression()
                if not self.take('WHEN'):
                    break
            if self.take('ELSE'):
                self.expression()
            self.need('END')
        elif self.peek() in ('NULL', 'TRUE', 'FALSE', '*'):
            self.index += 1
        elif self.index < len(self.tokens) and self.tokens[self.index][0] in ('number', 'string'):
            self.index += 1
        else:
            self.name()
            while self.take('.'):
                if self.take('*'):
                    break
                self.name()
            if self.take('('):
                if not self.take(')'):
                    self.take('DISTINCT')
                    self.expressions()
                    self.need(')')
        while self.take('::'):
            self.name()
        if self.take('OVER'):
            self.need('(')
            if self.take('PARTITION'):
                self.need('BY'); self.expressions()
            if self.take('ORDER'):
                self.need('BY'); self.expressions(ordered=True)
            if self.take('ROWS'):
                if self.take('BETWEEN'):
                    self.frame_boundary(); self.need('AND'); self.frame_boundary()
                else:
                    self.frame_boundary()
            self.need(')')

    def frame_boundary(self):
        if self.take('CURRENT'):
            self.need('ROW')
            return
        if not self.take('UNBOUNDED'):
            if self.index == len(self.tokens) or self.tokens[self.index][0] != 'number':
                raise _Uncertain()
            self.index += 1
        if not (self.take('PRECEDING') or self.take('FOLLOWING')):
            raise _Uncertain()

    def relation(self):
        if self.take('('):
            self.query(); self.need(')')
        else:
            self.name()
            while self.take('.'):
                self.name()
        self.alias()

    def query(self):
        if self.take('WITH'):
            while True:
                self.name(); self.need('AS'); self.need('(')
                self.query(); self.need(')')
                if not self.take(','):
                    break
        self.need('SELECT')
        self.take('DISTINCT') or self.take('ALL')
        self.expressions(aliases=True)
        if self.take('FROM'):
            self.relation()
            while True:
                if self.take(','):
                    self.relation()
                else:
                    if self.peek() in ('LEFT', 'RIGHT', 'INNER', 'FULL', 'CROSS'):
                        self.index += 1
                        self.take('OUTER'); self.need('JOIN')
                    elif not self.take('JOIN'):
                        break
                    self.relation()
                    if self.take('ON'):
                        self.expression()
                    elif self.take('USING'):
                        self.need('('); self.name()
                        while self.take(','):
                            self.name()
                        self.need(')')
        if self.take('WHERE'):
            self.expression()
        if self.take('GROUP'):
            self.need('BY'); self.expressions()
        if self.take('HAVING'):
            self.expression()
        if self.take('ORDER'):
            self.need('BY'); self.expressions(ordered=True)
        if self.take('LIMIT'):
            self.expression()
        if self.take('OFFSET'):
            self.expression()
        if self.take('UNION'):
            self.take('ALL'); self.query()


def has_recognized_select_syntax(value):
    """True only for fully consumed, recognized SQL; uncertainty is not zero."""
    if len(value.encode('utf-8')) > 8192 or '--' in value or '/*' in value:
        return False
    tokens, offset = [], 0
    while offset < len(value):
        match = _TOKEN.match(value, offset)
        if match is None:
            return False
        if match.lastgroup:
            tokens.append((match.lastgroup, match[0].upper() if match.lastgroup == 'word' else match[0]))
        offset = match.end()
        if len(tokens) > 2048:
            return False
    parser = _Select(tokens)
    try:
        parser.query()
        parser.take(';')
        return parser.index == len(tokens)
    except (_Uncertain, RecursionError):
        return False
