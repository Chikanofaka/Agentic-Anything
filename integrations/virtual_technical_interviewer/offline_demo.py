#!/usr/bin/env python3
"""Run a reproducible, synthetic no-key interview and separate Trainer handoff."""
import argparse
import asyncio
import json
import sys

from tia_runtime.controller import InterviewController, SessionConfig, SessionError
from tia_runtime.provider import ModelConfig, ModelPortalError, build_portal


class DemoClock:
    """Explicit deterministic fixture clock, not a production interview timer."""
    def __init__(self):
        self.value = 0.0

    def __call__(self):
        return self.value

    def advance(self):
        self.value += 1.0


async def run_demo(provider='offline_mock', timeout_seconds=1.0):
    clock = DemoClock()
    controller = InterviewController(SessionConfig(),
        portal=build_portal(ModelConfig(provider=provider, timeout_seconds=timeout_seconds)), clock=clock)
    await controller.start('Describe how you would find the first order per customer, including ties and NULL dates. Text-only mock; no query execution.')
    for kind, text, operation in [
        ('clarify', 'For tied dates I will use order ID as a stable tie-breaker. Should unknown dates be excluded?', 'clarify'),
        ('plan', 'I will partition by customer, order by date and order ID, then inspect one row per customer.', 'feedback'),
        ('help', 'I have a plan but have not verified row grain. May I check one customer with tied dates before implementing?', 'feedback'),
        ('implement', 'Proposed text: ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY order_date, order_id). This has not been executed.', 'feedback'),
        ('test', 'Proposed checks: tied dates, NULL dates and customers with multiple orders. These are planned checks, not passing tests.', 'feedback'),
        ('conclude', 'I can explain the intended row grain and tie policy; correctness remains unverified because this slice has no SQL evaluator.', 'close')]:
        clock.advance()
        controller.candidate_action(kind, text)
        await controller.respond(operation)
    clock.advance()
    receipt = controller.close()
    controller.review('synthetic-demo-reviewer')
    await controller.handoff()
    controller.finish_training()
    result = controller.snapshot()
    result['demo'] = {'input': 'SYNTHETIC_SCRIPT', 'clock': 'DETERMINISTIC_FIXTURE',
                      'review': 'SCRIPTED_HANDOFF_REVIEW_NOT_HUMAN_CALIBRATION',
                      'receipt_unchanged_after_training': controller.receipt == receipt}
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--json', action='store_true', help='Print the full synthetic event receipt.')
    parser.add_argument('--provider', default='offline_mock', help='Only offline_mock is enabled; live providers fail closed.')
    parser.add_argument('--timeout-seconds', type=float, default=1.0)
    args = parser.parse_args(argv)
    try:
        result = asyncio.run(run_demo(args.provider, args.timeout_seconds))
    except (SessionError, ModelPortalError) as error:
        print(json.dumps({'status': 'BLOCKED', 'code': error.code, 'live_model_used': False}), file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
    else:
        print('TIA offline demonstration | SYNTHETIC SCRIPT | SIMULATED MODEL | NO SQL / NO GRADING')
        for event in result['events']:
            payload = event['payload']
            detail = payload.get('text', payload.get('reason'))
            if detail is None:
                detail = json.dumps(payload, sort_keys=True)
            print(f"{event['sequence']:02d} [{event['actor']}] {event['kind']}: {detail}")
        print(f"State: {result['phase']} | Events: {len(result['events'])}")
        print('Technical: NOT_SCORED | Communication: NOT_SCORED')
        print('Reviewed receipt unchanged after Trainer: ' + str(result['demo']['receipt_unchanged_after_training']))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
