"""Run both comparison passes and keep actual SDK artifacts and normalized results."""
import argparse
import hashlib
import importlib.metadata
import json
import os
import platform
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from .agent import run_agent
from .cases import CASES, MAX_CALLS, MAX_OUTPUT_TOKENS, MODEL, SYSTEM, prompt
from .sandbox import docker, grade

FRAMEWORKS = ["inspect", "ragas", "deepeval", "mlflow"]


def configure():
    os.environ.setdefault("DOCKER_HOST", "unix://" + str(Path.home() / ".colima/inspect-comparison/docker.sock"))
    if "COMPARISON_IMAGE" not in os.environ:
        image = json.loads(docker("image", "inspect", "python:3.12-slim").stdout)[0]
        os.environ["COMPARISON_IMAGE"] = image["RepoDigests"][0]
    docker("info")


def run_worker(framework, output, records=None):
    output.mkdir(parents=True, exist_ok=True)
    command = [sys.executable, "-m", "comparison.worker", "--framework", framework, "--output", str(output)]
    if records:
        command += ["--records", str(records)]
    print("START", framework, output, flush=True)
    start = time.monotonic()
    with (output / "console.log").open("w") as log:
        result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, timeout=600)
    print("END", framework, "exit", result.returncode, "seconds", round(time.monotonic()-start, 2), flush=True)
    if result.returncode:
        print((output / "console.log").read_text()[-6000:], flush=True)
        return {"status": "error", "log": str(output / "console.log")}
    return {"status": "success", "scores": json.loads((output / "scores.json").read_text())}


def summarize(output):
    report = {"shared": {}, "live": {}}
    for framework in FRAMEWORKS:
        for phase in report:
            root = output / phase / framework
            scores_file = root / "scores.json"
            if not scores_file.exists():
                report[phase][framework] = {"status": "error"}
                continue
            scores = json.loads(scores_file.read_text())
            if phase == "shared":
                model = [r for r in scores if r["artifact_id"].endswith("-model")]
                controls = [r for r in scores if not r["artifact_id"].endswith("-model")]
                report[phase][framework] = {
                    "status": "success", "model_passed": sum(r["score"] == 1 for r in model),
                    "model_total": len(model), "controls": controls,
                    "controls_correct": all(
                        r["score"] == int(r["artifact_id"].endswith("-reference")) for r in controls),
                }
            else:
                records = [json.loads(p.read_text()) for p in sorted((root / "records").glob("*.json"))]
                report[phase][framework] = {
                    "status": "success", "passed": sum(r["score"] == 1 for r in scores),
                    "total": len(scores), "model_calls": sum(r["model_calls"] for r in records),
                    "input_tokens": sum(r["input_tokens"] for r in records),
                    "output_tokens": sum(r["output_tokens"] for r in records),
                    "final_source_hashes": {r["case_id"]: hashlib.sha256(r["final_source"].encode()).hexdigest() for r in records},
                }
    (output / "summary.json").write_text(json.dumps(report, indent=2))
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("comparison/runs") / datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))
    parser.add_argument("--phase", choices=["all", "controls", "shared", "live", "summary", "recovery"], default="all")
    parser.add_argument("--framework", choices=FRAMEWORKS, action="append")
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    frameworks = args.framework or FRAMEWORKS
    if args.phase != "summary":
        configure()
        config = {
            "timestamp": datetime.now(timezone.utc).isoformat(), "python": platform.python_version(),
            "versions": {p: importlib.metadata.version(p) for p in ["inspect-ai", "ragas", "deepeval", "mlflow", "openai", "langchain-community"]},
            "model": MODEL, "max_model_calls_per_case": MAX_CALLS,
            "max_output_tokens_per_call": MAX_OUTPUT_TOKENS, "temperature": 0,
            "image": os.environ["COMPARISON_IMAGE"], "system_prompt": SYSTEM,
            "case_ids": list(CASES),
        }
        (output / "config.json").write_text(json.dumps(config, indent=2))
    if args.phase == "controls":
        records = []
        for case_id, case in CASES.items():
            for label, source in [("broken", case["source"]), ("reference", case["reference"])]:
                report = grade(case_id, source)
                expected = label == "reference"
                if report["passed"] != expected:
                    raise RuntimeError(f"Invalid grading control {case_id}/{label}: {report}")
                records.append({"artifact_id": case_id + "-" + label, "case_id": case_id,
                                "input": prompt(case_id), "final_source": source})
        path = output / "controls.json"
        path.write_text(json.dumps(records, indent=2))
        results = [run_worker(framework, output / "controls" / framework, path)
                   for framework in frameworks]
        if any(result["status"] != "success" for result in results):
            raise SystemExit(1)
        return
    if args.phase in ["all", "shared"]:
        records = []
        for case_id in CASES:
            print("COMMON AGENT", case_id, flush=True)
            record = run_agent(case_id, output / "common" / "records")
            record["artifact_id"] = case_id + "-model"
            records.append(record)
        for case_id, case in CASES.items():
            for label, source in [("broken", case["source"]), ("reference", case["reference"])]:
                records.append({"artifact_id": case_id + "-" + label, "case_id": case_id,
                                "input": prompt(case_id), "final_source": source})
        shared = output / "shared-records.json"
        shared.write_text(json.dumps(records, indent=2))
        for framework in frameworks:
            run_worker(framework, output / "shared" / framework, shared)
    if args.phase in ["all", "live"]:
        for framework in frameworks:
            run_worker(framework, output / "live" / framework)
    if args.phase in ["all", "recovery"]:
        from .recovery import run_recovery
        run_recovery(output / "recovery", frameworks)
    report = summarize(output)
    print(json.dumps(report, indent=2), flush=True)
    if any(report[p][f]["status"] != "success" for p in report for f in frameworks) and args.phase in ["all", "shared", "live"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
