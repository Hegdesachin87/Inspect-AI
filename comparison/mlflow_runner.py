"""MLflow owns prediction scheduling, custom scoring and local trace storage."""
import json
import os
from pathlib import Path

import mlflow
from mlflow.entities import Feedback
from mlflow.genai.scorers import scorer

from .agent import run_agent
from .cases import CASES
from .sandbox import grade


@scorer(name="fixed_tests")
def fixed_tests(outputs):
    report = grade(outputs["case_id"], outputs["final_source"])
    return Feedback(value=int(report["passed"]), rationale=report["test_output"])


def run(output_dir, records=None, case_ids=None):
    output_dir = Path(output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    mlflow.set_tracking_uri("sqlite:///" + str(output_dir / "mlflow.db"))
    experiment = mlflow.get_experiment_by_name("coding_repair")
    if experiment is None:
        experiment_id = mlflow.create_experiment("coding_repair",
            artifact_location=(output_dir / "artifacts").as_uri())
    else:
        experiment_id = experiment.experiment_id
    mlflow.set_experiment(experiment_id=experiment_id)
    if records is None:
        # MLflow otherwise calls predict_fn once for validation AND once for evaluation.
        # The callback is explicitly traced and verified below; avoid an extra paid repair.
        os.environ["MLFLOW_GENAI_EVAL_SKIP_TRACE_VALIDATION"] = "true"
        mlflow.openai.autolog(log_traces=True, silent=True)

        @mlflow.trace(name="coding_repair", span_type="AGENT")
        def predict(case_id):
            return run_agent(case_id, output_dir / "records")

        result = mlflow.genai.evaluate(
            data=[{"inputs": {"case_id": c}} for c in (case_ids or CASES)],
            predict_fn=predict, scorers=[fixed_tests])
    else:
        result = mlflow.genai.evaluate(data=[
            {"inputs": {"artifact_id": r["artifact_id"]}, "outputs": r} for r in records
        ], scorers=[fixed_tests])
    table = result.result_df
    table.to_json(output_dir / "native-results.json", orient="records", indent=2)
    rows = []
    for row in table.to_dict(orient="records"):
        record = row["response"]
        rows.append({"artifact_id": record.get("artifact_id", record["case_id"]),
                     "score": row["fixed_tests/value"],
                     "reason": row.get("fixed_tests/rationale")})
    mlflow.flush_trace_async_logging()
    traces = mlflow.search_traces(experiment_ids=[experiment_id])
    details = []
    for _, row in traces.iterrows():
        trace = mlflow.get_trace(row["trace_id"])
        details.append({"trace_id": row["trace_id"], "spans": [
            {"name": s.name, "type": s.span_type} for s in trace.data.spans]})
    (output_dir / "trace-verification.json").write_text(json.dumps(details, indent=2))
    if records is None and not details:
        raise RuntimeError("MLflow did not persist live traces")
    return sorted(rows, key=lambda r: r["artifact_id"])
