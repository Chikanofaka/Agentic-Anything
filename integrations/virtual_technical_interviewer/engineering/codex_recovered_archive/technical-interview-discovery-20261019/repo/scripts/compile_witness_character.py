#!/usr/bin/env python3
"""Compile exactly the reviewed Witness authoring sources. No provider calls."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'runtime'))
from trusted_adapters.character_context import compile_sources, ARTIFACT

parser = argparse.ArgumentParser()
parser.add_argument('--check', action='store_true')
args = parser.parse_args()
artifact, drift = compile_sources(ROOT / 'integrations/witness_loop/source', ROOT / 'WTL-029_Witness_Loop_v0.1')
rendered = json.dumps(artifact, ensure_ascii=False, indent=2) + '\n'
if args.check:
    if not ARTIFACT.is_file() or ARTIFACT.read_text(encoding='utf-8') != rendered:
        sys.exit('CHARACTER_ARTIFACT_STALE: run python3 scripts/compile_witness_character.py')
else:
    ARTIFACT.write_text(rendered, encoding='utf-8')
print(json.dumps({'version': artifact['version'], 'digest': artifact['digest'], 'canonical': 'integrations/witness_loop/source',
                  'duplicate_drift': drift, 'full_director_story_bundled': False}))
