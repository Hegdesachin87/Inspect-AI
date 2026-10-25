#!/usr/bin/env python3
"""Print a judge-comparison matrix for a judge-swap experiment log."""

import sys

from inspect_ai.log import read_eval_log


def scorer_map(log):
    raw = log.results.scores if log.results and log.results.scores else []
    if isinstance(raw, dict):
        return dict(raw)
    return {s.name: s for s in raw}  # older logs store a list of EvalScore


def main() -> None:
    log = read_eval_log(sys.argv[1])
    by_name = scorer_map(log)
    scorers = sorted(by_name)

    print(f"Model: {log.eval.model}   Samples: {len(log.samples)}")
    print(f"Scorers appended: {', '.join(scorers)}\n")

    header = f"{'sample':<24s}" + "".join(f"{s[:18]:<20s}" for s in scorers)
    print(header)
    for sample in log.samples or []:
        row = "".join(
            f"{str((sample.scores or {}).get(s, {}).value)[:18]:<20s}"
            for s in scorers
        )
        print(f"{str(sample.id or '?')[:23]:<24s}{row}")

    print()
    for s in scorers:
        metrics = by_name[s].metrics or {}
        acc = metrics.get("accuracy")
        if acc and acc.value is not None:
            print(f"accuracy[{s}] = {acc.value}")


if __name__ == "__main__":
    main()
