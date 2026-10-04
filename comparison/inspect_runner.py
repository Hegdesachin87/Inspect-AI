"""Inspect owns dataset iteration, tool dispatch, sandboxes, logs and eval-set reuse."""
import json
import time
from pathlib import Path

from inspect_ai import Task, eval_set, task
from inspect_ai.dataset import Sample
from inspect_ai.log import read_eval_log
from inspect_ai.model import GenerateConfig, ModelOutput
from inspect_ai.scorer import Score, accuracy, scorer
from inspect_ai.solver import solver, system_message, use_tools
from inspect_ai.tool import tool
from inspect_ai.util import sandbox

from .agent import encode, save_record
from .cases import (CASES, COMMAND_TIMEOUT, MAX_CALLS, MAX_OUTPUT_TOKENS,
                    MODEL, SYSTEM, prompt)
from .sandbox import command_result, grade


@tool(name="run_command")
def shell_tool():
    async def execute(command: str) -> str:
        """Run a shell command in the isolated project workspace.

        Args:
            command: Shell command to run in /workspace.
        """
        result = await sandbox().exec(
            ["timeout", "--kill-after=2s", str(COMMAND_TIMEOUT), "sh", "-lc", command],
            timeout=COMMAND_TIMEOUT + 10,
        )
        return command_result(result.returncode, result.stdout, result.stderr)
    return execute


@solver
def bounded_agent(output_dir):
    async def solve(state, generate):
        started = time.monotonic()
        input_tokens = output_tokens = calls = 0
        for _ in range(MAX_CALLS):
            state = await generate(state, tool_calls="single")
            calls += 1
            if state.output.usage:
                input_tokens += state.output.usage.input_tokens
                output_tokens += state.output.usage.output_tokens
            if not state.output.message.tool_calls:
                break
        # Docker cp cannot reliably read tmpfs mounts. Read through sandbox exec,
        # as the application-based stacks do, while retaining sandbox isolation.
        result = await sandbox().exec(["cat", "/workspace/project.py"])
        if not result.success:
            raise RuntimeError(f"Cannot read repaired project: {result.stderr}")
        source = result.stdout
        record = {"case_id": state.sample_id, "model": MODEL,
                  "input": prompt(state.sample_id), "final_source": source,
                  "messages": [m.model_dump(mode="json", exclude_none=True) for m in state.messages],
                  "input_tokens": input_tokens, "output_tokens": output_tokens,
                  "model_calls": calls, "agent_seconds": time.monotonic() - started}
        state.metadata["record"] = record
        save_record(record, output_dir)
        return state
    return solve


@solver
def replay(record):
    async def solve(state, generate):
        state.metadata["record"] = record
        state.output = ModelOutput.from_content(MODEL, encode(record))
        return state
    return solve


@scorer(metrics=[accuracy()])
def fixed_tests():
    async def score(state, target):
        record = state.metadata["record"]
        report = grade(record["case_id"], record["final_source"])
        return Score(value=int(report["passed"]), explanation=report["test_output"])
    return score


@task
def repair(case_id, compose_file, output_dir):
    return Task(
        name="coding_repair", dataset=[Sample(id=case_id, input=prompt(case_id),
            files={"/workspace/project.py": CASES[case_id]["source"]})],
        solver=[system_message(SYSTEM), use_tools(shell_tool()), bounded_agent(output_dir)],
        scorer=fixed_tests(), sandbox=("docker", compose_file),
        config=GenerateConfig(temperature=0, max_tokens=MAX_OUTPUT_TOKENS,
                              parallel_tool_calls=False, max_retries=0, timeout=45),
    )


@task
def replay_task(case_id, record):
    return Task(name="shared_trajectory", dataset=[Sample(id=case_id, input=prompt(record["case_id"]))],
                solver=replay(record), scorer=fixed_tests())


def run(output_dir, records=None, case_ids=None):
    import os
    output_dir = Path(output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    if records is None:
        compose_file = output_dir / "compose.yaml"
        compose_file.write_text("""services:
  default:
    image: %s
    init: true
    command: [sleep, infinity]
    working_dir: /workspace
    user: '1000:1000'
    read_only: true
    network_mode: none
    cap_drop: [ALL]
    security_opt: [no-new-privileges:true]
    pids_limit: 64
    mem_limit: 256m
    cpus: 1
    tmpfs:
      - /workspace:rw,size=32m,uid=1000,gid=1000,mode=700
      - /tmp:rw,size=16m,uid=1000,gid=1000,mode=700
""" % os.environ["COMPARISON_IMAGE"])
        tasks = [repair(c, str(compose_file), str(output_dir / "records"))
                 for c in (case_ids or CASES)]
    else:
        tasks = [replay_task(r["artifact_id"], r) for r in records]
    success, logs = eval_set(
        tasks, model="openai/" + MODEL, log_dir=str(output_dir / "logs"),
        display="none", max_tasks=1, max_samples=1, max_sandboxes=1,
        retry_attempts=0, log_model_api=False,
    )
    if not success:
        errors = [read_eval_log(l.location).error for l in logs if l.status != "success"]
        raise RuntimeError(f"Inspect eval-set failed: {errors}")
    rows = []
    for header in logs:
        log = read_eval_log(header.location)
        for sample in log.samples:
            result = sample.scores["fixed_tests"]
            rows.append({"artifact_id": sample.id, "score": result.value,
                         "reason": result.explanation})
    return sorted(rows, key=lambda r: r["artifact_id"])
