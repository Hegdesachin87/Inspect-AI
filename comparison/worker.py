"""Each SDK runs in its own process so tracing hooks cannot affect other stacks."""
import argparse
import importlib
import json
import os
import time
from pathlib import Path

# Keep evaluation data local, apart from the explicitly requested model calls.
os.environ["RAGAS_DO_NOT_TRACK"] = "true"
os.environ["DEEPEVAL_TELEMETRY_OPT_OUT"] = "1"
os.environ["DEEPEVAL_DISABLE_DOTENV"] = "1"
os.environ["CONFIDENT_API_KEY"] = ""
os.environ["MLFLOW_DISABLE_AGENT_HINT"] = "1"
os.environ["MLFLOW_DISABLE_TELEMETRY"] = "true"
os.environ["MLFLOW_GENAI_EVAL_MAX_WORKERS"] = "1"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--framework", choices=["inspect", "ragas", "deepeval", "mlflow"], required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--records", type=Path)
    parser.add_argument("--fixture-recovery", action="store_true")
    parser.add_argument("--interrupt", action="store_true")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    runner = importlib.import_module("comparison." + args.framework + "_runner")
    if args.fixture_recovery:
        from .recovery import install_fixture
        install_fixture(runner, args.output, args.interrupt)
    records = json.loads(args.records.read_text()) if args.records else None
    start = time.monotonic()
    rows = runner.run(args.output, records=records,
                      case_ids=["slug", "intervals"] if args.fixture_recovery else None)
    (args.output / "scores.json").write_text(json.dumps(rows, indent=2))
    (args.output / "execution.json").write_text(json.dumps({
        "framework": args.framework, "elapsed_seconds": time.monotonic() - start,
        "rows": len(rows), "fixture_recovery": args.fixture_recovery,
    }, indent=2))
    print(json.dumps({"framework": args.framework, "rows": len(rows),
                      "passed": sum(r["score"] == 1 for r in rows)}), flush=True)


if __name__ == "__main__":
    main()
