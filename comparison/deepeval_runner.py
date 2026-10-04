"""DeepEval's traced dataset iterator runs live callbacks; evaluate scores replay."""
from pathlib import Path

from deepeval import evaluate
from deepeval.dataset import EvaluationDataset, Golden
from deepeval.evaluate import AsyncConfig, CacheConfig, DisplayConfig
from deepeval.metrics import BaseMetric
from deepeval.test_case import LLMTestCase
from deepeval.tracing import observe, update_current_trace

from .agent import decode, encode, run_agent
from .cases import CASES, prompt
from .sandbox import grade

_MEASURED = []


class FixedTests(BaseMetric):
    def __init__(self):
        self.threshold = 1
        self.async_mode = False
        self.include_reason = True

    def measure(self, test_case, *args, **kwargs):
        record = decode(test_case.actual_output)
        report = grade(record["case_id"], record["final_source"])
        self.score = int(report["passed"])
        self.reason = report["test_output"]
        self.success = bool(self.score)
        _MEASURED.append({"artifact_id": record.get("artifact_id", record["case_id"]),
                          "score": self.score, "reason": self.reason})
        return self.score

    async def a_measure(self, test_case, *args, **kwargs):
        return self.measure(test_case, *args, **kwargs)

    @property
    def __name__(self):
        return "fixed_tests"


def run(output_dir, records=None, case_ids=None):
    output_dir = Path(output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    _MEASURED.clear()
    options = dict(
        async_config=AsyncConfig(run_async=False),
        cache_config=CacheConfig(write_cache=False, use_cache=False),
        display_config=DisplayConfig(show_indicator=False, print_results=False,
            inspect_after_run=False, results_folder=str(output_dir / "native-results"),
            file_type="md", file_output_dir=str(output_dir / "native-results")),
    )
    if records is not None:
        cases = [LLMTestCase(name=r["artifact_id"], input=r["input"], actual_output=encode(r))
                 for r in records]
        evaluate(test_cases=cases, metrics=[FixedTests()], identifier="shared_trajectory", **options)
        expected = len(records)
    else:
        ids = list(case_ids or CASES)
        dataset = EvaluationDataset(goldens=[Golden(input=prompt(c), name=c) for c in ids])

        @observe(type="agent", name="coding_repair")
        def predict(case_id):
            record = run_agent(case_id, output_dir / "records")
            update_current_trace(test_case=LLMTestCase(
                name=case_id, input=record["input"], actual_output=encode(record)))
            return encode(record)

        for golden in dataset.evals_iterator(metrics=[FixedTests()], identifier="coding_repair", **options):
            predict(golden.name)
        expected = len(ids)
    if len(_MEASURED) != expected:
        raise RuntimeError(f"DeepEval produced {len(_MEASURED)} scores for {expected} rows")
    return sorted(_MEASURED, key=lambda r: r["artifact_id"])
