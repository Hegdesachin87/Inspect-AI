#!/usr/bin/env python3
"""Print the approval decision chain from an approval-demo log."""

import sys
from collections import Counter

from inspect_ai.log import read_eval_log


def main() -> None:
    log = read_eval_log(sys.argv[1])
    print(f"Task: {log.eval.task}   Model: {log.eval.model}")
    totals = Counter()

    for sample in log.samples or []:
        print(f"\n=== sample {sample.id} ===")
        chain: dict[str, list] = {}
        for ev in sample.events or []:
            if ev.event != "approval":
                continue
            call = ev.call
            arg = next(iter(call.arguments.values()), "")
            arg = str(arg).replace("\n", " ")[:70]
            chain.setdefault(call.id, []).append(
                (call.function, arg, ev.approver, ev.decision, ev.explanation or "")
            )
        for call_id, steps in chain.items():
            fn, arg, _, final, expl = steps[-1]
            path = " -> ".join(f"{a}:{d}" for _, _, a, d, _ in steps)
            totals[final] += 1
            print(f"  [{final.upper():7s}] {fn}({arg})")
            if len(steps) > 1 or final != "approve":
                print(f"           chain: {path}")
                print(f"           reason: {expl[:90]}")

    print("\nTotals:", dict(totals))


if __name__ == "__main__":
    main()
