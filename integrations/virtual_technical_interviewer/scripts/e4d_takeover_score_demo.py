"""Offline scoring MVM CLI. Read-only: prints JSON, no network or session writes."""
import argparse
import json
from pathlib import Path
import sys

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))
from tia_runtime.evaluator_v1_scoring import WEIGHTS, AssessmentContractError, score_assessment, safe_load_json


def demo():
    observed = {"T1":3,"T2":2,"T3":None,"T4":3,"C1":3,"C2":3,"C3":2,
                "C4":4,"P1":3,"P2":None,"P3":2,"P4":1}
    return {"schema":"tia-evaluator-score-input/v1","interview_id":"synthetic001",
            "target_role":"DATA_ANALYST","seniority":"JUNIOR","interviewer_mode":"STRICT_CHALLENGING",
            "questions":[{"question_id":f"q{i}","candidate_event_ids":[f"e{i}"]} for i in (1,2,3)],
            "ratings":{k:{"anchor":v,"evidence_event_ids":["e1"] if v is not None else [],
                          "source":"SYNTHETIC_DEMO" if v is not None else None} for k,v in observed.items()}}


def main():
    parser=argparse.ArgumentParser(description="TIA E4D offline provisional score")
    g=parser.add_mutually_exclusive_group(required=True)
    g.add_argument("--demo",action="store_true",help="run synthetic 64/100 example")
    g.add_argument("--input",type=Path,help="read a synthetic structured JSON scoring record")
    args=parser.parse_args()
    try:
        if args.demo: record=demo()
        else: record=safe_load_json(args.input.read_text(encoding="utf-8"))
        result=score_assessment(record)
        print(json.dumps(result,indent=2,ensure_ascii=False,sort_keys=True,allow_nan=False))
        print(f"E4D_OFFLINE_SCORE_GATE=PASS SCORE={result['score']} COVERAGE={result['rating_coverage_pct']} STATUS={result['score_status']}",file=sys.stderr)
    except (AssessmentContractError,OSError,UnicodeError) as e:
        print("E4D_OFFLINE_SCORE_GATE=HOLD reason="+str(e),file=sys.stderr)
        raise SystemExit(2)


if __name__=="__main__": main()
