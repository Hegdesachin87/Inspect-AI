"""Ragas runs the experiment callback and stores local JSONL results."""
import asyncio
from pathlib import Path

from ragas import Dataset, experiment
from ragas.backends.local_jsonl import LocalJSONLBackend
from ragas.metrics import MetricResult, discrete_metric

from .agent import run_agent
from .cases import CASES
from .sandbox import grade


@discrete_metric(name="fixed_tests", allowed_values=["pass", "fail"])
def fixed_tests(case_id, source):
    report = grade(case_id, source)
    return MetricResult(value="pass" if report["passed"] else "fail",
                        reason=report["test_output"])


def run(output_dir, records=None, case_ids=None):
    output_dir = Path(output_dir).resolve()
    backend = LocalJSONLBackend(root_dir=str(output_dir / "backend"))
    dataset = Dataset(name="coding_repair", backend=backend)
    data = ([{"case_id": c} for c in (case_ids or CASES)] if records is None
            else [{"case_id": r["case_id"], "record": r} for r in records])
    for row in data:
        dataset.append(row)
    dataset.save()

    @experiment(backend=backend)
    async def evaluate_row(row):
        record = row.get("record") or run_agent(row["case_id"], output_dir / "records")
        metric = await fixed_tests.ascore(case_id=record["case_id"], source=record["final_source"])
        return {"artifact_id": record.get("artifact_id", record["case_id"]),
                "score": int(metric.value == "pass"), "reason": metric.reason,
                "record": record}

    result = asyncio.run(evaluate_row.arun(dataset, name="coding_repair"))
    rows = [{k: row[k] for k in ("artifact_id", "score", "reason")} for row in result]
    # Ragas logs callback errors and continues; the experiment requires every row.
    if len(rows) != len(data):
        raise RuntimeError("Ragas callback failures left missing experiment rows")
    return sorted(rows, key=lambda r: r["artifact_id"])
