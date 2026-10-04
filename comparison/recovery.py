"""Interrupt each native runner after one completed fixture task, then rerun it.

This measures scheduler reuse, not live-agent checkpoint restoration. Fixtures
return correct source without model calls, keeping recovery testing reproducible.
"""
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

from .agent import save_record
from .cases import CASES, MODEL, prompt
from .sandbox import docker


def install_fixture(runner, output, interrupt):
    calls = 0
    invocation_log = output / "fixture-invocations.jsonl"

    def append(event):
        with invocation_log.open("a") as stream:
            stream.write(json.dumps(event) + "\n")
            stream.flush()

    def fixture_record(case_id):
        return {"case_id": case_id, "model": "deterministic-recovery-fixture",
                "input": prompt(case_id), "final_source": CASES[case_id]["reference"],
                "messages": [], "events": [], "input_tokens": 0,
                "output_tokens": 0, "model_calls": 0, "agent_seconds": 0}

    def begin(case_id, container=None):
        nonlocal calls
        calls += 1
        append({"event": "start", "case_id": case_id})
        if interrupt and calls == 2:
            (output / "interrupt-ready.json").write_text(json.dumps({
                "case_id": case_id, "container": container}))
            while True:
                time.sleep(1)

    def fixture_agent(case_id, output_dir):
        begin(case_id)
        record = fixture_record(case_id)
        save_record(record, output_dir)
        append({"event": "complete", "case_id": case_id})
        return record

    if runner.__name__.endswith("inspect_runner"):
        from inspect_ai.model import ModelOutput
        from inspect_ai.solver import solver
        from inspect_ai.util import sandbox

        @solver(name="recovery_fixture")
        def fixture_solver(output_dir):
            async def solve(state, generate):
                hostname = await sandbox().exec(["hostname"])
                begin(state.sample_id, hostname.stdout.strip())
                record = fixture_record(state.sample_id)
                await sandbox().write_file("/workspace/project.py", record["final_source"])
                state.metadata["record"] = record
                state.output = ModelOutput.from_content(MODEL, "Fixture repair complete")
                save_record(record, output_dir)
                append({"event": "complete", "case_id": state.sample_id})
                return state
            return solve
        runner.bounded_agent = fixture_solver
    else:
        runner.run_agent = fixture_agent


def run_recovery(output, frameworks):
    output.mkdir(parents=True, exist_ok=True)
    summaries = {}
    for framework in frameworks:
        root = output / framework
        root.mkdir(parents=True, exist_ok=True)
        marker = root / "interrupt-ready.json"
        if marker.exists():
            raise RuntimeError(f"Recovery run already exists: {root}; use a fresh output directory")
        command = [sys.executable, "-m", "comparison.worker", "--framework", framework,
                   "--output", str(root), "--fixture-recovery"]
        print("RECOVERY INTERRUPT", framework, flush=True)
        with (root / "interrupted-console.log").open("w") as log:
            # Own a process group so cancellation also stops background SDK work.
            process = subprocess.Popen(command + ["--interrupt"], stdout=log,
                                       stderr=subprocess.STDOUT, start_new_session=True)
            try:
                deadline = time.monotonic() + 120
                while not marker.exists():
                    if process.poll() is not None:
                        raise RuntimeError(f"Recovery worker exited before interruption: {root}")
                    if time.monotonic() >= deadline:
                        raise TimeoutError(f"Recovery worker did not reach the second task: {root}")
                    time.sleep(0.1)
                os.killpg(process.pid, signal.SIGINT)
                try:
                    process.wait(timeout=30)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait()
            finally:
                if process.poll() is None:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait()
        info = json.loads(marker.read_text())
        if info.get("container"):
            docker("rm", "--force", info["container"], check=False)
        events_path = root / "fixture-invocations.jsonl"
        before = [json.loads(line) for line in events_path.read_text().splitlines()]
        with (root / "resumed-console.log").open("w") as log:
            result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, timeout=120)
        after = [json.loads(line) for line in events_path.read_text().splitlines()]
        resumed = after[len(before):]
        complete_before = [e["case_id"] for e in before if e["event"] == "complete"]
        started_after = [e["case_id"] for e in resumed if e["event"] == "start"]
        summaries[framework] = {
            "interrupted_exit_code": process.returncode, "resumed_exit_code": result.returncode,
            "completed_before_interruption": complete_before,
            "callbacks_on_resume": started_after,
            "repeated_completed_callbacks": sorted(set(complete_before) & set(started_after)),
            "model_calls": 0,
        }
        print("RECOVERY RESULT", framework, json.dumps(summaries[framework]), flush=True)
    (output / "summary.json").write_text(json.dumps(summaries, indent=2))
    if any(row["resumed_exit_code"] != 0 for row in summaries.values()):
        raise RuntimeError("One or more native recovery runs failed; inspect their logs")
