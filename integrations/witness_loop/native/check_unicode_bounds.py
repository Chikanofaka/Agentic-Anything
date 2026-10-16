"""Read-only worst-case wire-size check for the reviewed Witness binding."""
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'runtime'))
from hal_core.interactive import MAX_SAVE_BYTES
from trusted_adapters import witness

state = witness.initial_state()
state['memories'] = [
    {'fact': '\U0001f600' * 297 + f'{n:03}', 'source': 'PLAYER_STATEMENT', 'scene': 1, 'turn': 0}
    for n in range(witness.MAX_MEMORIES)
]
state['transcript'] = [
    {'who': '林雾', 'text': '\U0001f600' * witness.MAX_REPLY, 'scene': 1}
    for _ in range(witness.MAX_TRANSCRIPT)
]
receipt = {'kind': 'HAL_INTERACTIVE_RECEIPT_V1', 'domain_id': 'witness-loop',
           'package_digest': '0' * 64, 'action': 'INITIALIZED', 'mode': 'SIMULATED',
           'live_model_used': False, 'external_writes': False, 'revision': 0}
record = {'schema': 'hal-session/v1', 'domain_id': 'witness-loop', 'state': state, 'receipt': receipt}

def stored_bytes():
    return len(json.dumps(record, ensure_ascii=False, separators=(',', ':')).encode())

# Keep all 256 largest memories, then fill the remaining save budget with the
# largest legal four-byte Unicode transcript. This maximizes duplicate export expansion.
while stored_bytes() > MAX_SAVE_BYTES:
    excess = stored_bytes() - MAX_SAVE_BYTES
    row = state['transcript'][-1]
    remove = min(len(row['text']), (excess + 3) // 4)
    row['text'] = row['text'][:-remove]
    if not row['text']:
        state['transcript'].pop()
witness.validate_state(state)
export = {'state_json': json.dumps(state, ensure_ascii=False, indent=2),
          'user_md': witness.user_markdown(state),
          'receipt_json': json.dumps(receipt, ensure_ascii=False, indent=2)}
wire = json.dumps({'id': 'native-1', 'ok': True, 'result': {'export': export}}, ensure_ascii=True).encode()
assert stored_bytes() <= MAX_SAVE_BYTES
assert len(wire) < 8 * 1024 * 1024
print(f'Unicode bound PASS: saved={stored_bytes()} bytes; export wire={len(wire)} bytes; native bound={8 * 1024 * 1024} bytes; no files/network used.')
