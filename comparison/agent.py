"""One application agent for Ragas, DeepEval, MLflow and shared trajectories."""
import json
import time
from pathlib import Path

from openai import OpenAI

from .cases import (ARG_DESCRIPTION, CASES, MAX_CALLS, MAX_OUTPUT_TOKENS,
                    MODEL, SYSTEM, TOOL_DESCRIPTION, prompt)
from .sandbox import Workspace

TOOL = {
    "type": "function", "function": {
        "name": "run_command", "description": TOOL_DESCRIPTION,
        "parameters": {
            "type": "object", "properties": {
                "command": {"type": "string", "description": ARG_DESCRIPTION},
            }, "required": ["command"],
        },
    },
}


def run_agent(case_id, output_dir):
    started = time.monotonic()
    messages = [{"role": "system", "content": SYSTEM},
                {"role": "user", "content": prompt(case_id)}]
    events, input_tokens, output_tokens = [], 0, 0
    client = OpenAI(max_retries=0, timeout=45)
    with Workspace(CASES[case_id]["source"]) as workspace:
        for call in range(MAX_CALLS):
            result = client.chat.completions.create(
                model=MODEL, messages=messages, tools=[TOOL],
                temperature=0, max_tokens=MAX_OUTPUT_TOKENS,
                parallel_tool_calls=False,
            )
            input_tokens += result.usage.prompt_tokens
            output_tokens += result.usage.completion_tokens
            message = result.choices[0].message
            messages.append(message.model_dump(exclude_none=True))
            events.append({"type": "model", "call": call + 1,
                           "usage": result.usage.model_dump(),
                           "message": message.model_dump(exclude_none=True)})
            if not message.tool_calls:
                break
            for tc in message.tool_calls:
                if tc.function.name != "run_command":
                    raise ValueError(f"Unknown tool {tc.function.name}")
                command = json.loads(tc.function.arguments)["command"]
                output = workspace.execute(command)
                events.append({"type": "tool", "command": command, "output": output})
                messages.append({"role": "tool", "tool_call_id": tc.id, "content": output})
        source = workspace.read_source()
    record = {"case_id": case_id, "model": MODEL, "input": prompt(case_id),
              "final_source": source, "messages": messages, "events": events,
              "input_tokens": input_tokens, "output_tokens": output_tokens,
              "model_calls": sum(e["type"] == "model" for e in events),
              "agent_seconds": time.monotonic() - started}
    save_record(record, output_dir)
    return record


def save_record(record, output_dir):
    target = Path(output_dir) / (record["case_id"] + ".json")
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(".tmp")
    temporary.write_text(json.dumps(record, indent=2))
    temporary.replace(target)


def encode(record):
    return json.dumps(record)


def decode(value):
    return json.loads(value)
