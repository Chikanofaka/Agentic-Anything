"""One-shot native-only local runner. No credentials, URLs or network requests."""
import json
import os
import signal
import sys
from .post_interview_sql import execute, PostSQLError
from .persistence import strict_json

def main():
    # Ordinary child commands share this cancellation group; PostgreSQL may daemonize.
    # Its normal cleanup is the existing runner finally, invoked by SIGTERM.
    if os.getpgrp() != os.getpid():
        os.setsid()
    # Raising allows the PostgreSQL runner's finally to stop its temporary cluster.
    def cancelled(*_): raise SystemExit(2)
    signal.signal(signal.SIGTERM,cancelled)
    raw=sys.stdin.buffer.read(131073)
    try:
        if len(raw)>131072: raise PostSQLError('POST_SQL_INPUT_TOO_LARGE')
        result=execute(strict_json(raw))
        print(json.dumps(result,ensure_ascii=True,allow_nan=False))
        return 0
    except (ValueError,KeyError,TypeError,RecursionError):
        print(json.dumps({'error':'POST_SQL_EXECUTION_UNAVAILABLE'})); return 2
if __name__=='__main__': sys.exit(main())
