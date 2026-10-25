"""Theory-of-mind task used by the judge-swap experiment.

Copied from the official Inspect example
(reference/inspect_ai/examples/theory_of_mind.py) so the experiment runs
from its own folder without touching the read-only reference snapshot.
Behavior is unchanged: chain-of-thought solver, model-graded-fact scorer.
The scorer here only matters for ordinary runs; the experiment itself
generates with --no-score and re-scores via `inspect score`.
"""

from inspect_ai import Task, task
from inspect_ai.dataset import example_dataset
from inspect_ai.scorer import model_graded_fact
from inspect_ai.solver import chain_of_thought, generate


@task
def theory_of_mind():
    return Task(
        dataset=example_dataset("theory_of_mind"),
        solver=[chain_of_thought(), generate()],
        scorer=model_graded_fact(),
    )
