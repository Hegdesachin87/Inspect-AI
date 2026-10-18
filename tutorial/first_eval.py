"""A first Inspect AI evaluation: ask three questions and score the answers."""

from inspect_ai import Task, task
from inspect_ai.dataset import Sample
from inspect_ai.scorer import match
from inspect_ai.solver import generate, system_message


@task
def capitals():
    return Task(
        dataset=[
            Sample(input="What is the capital of France?", target="Paris"),
            Sample(input="What is the capital of Japan?", target="Tokyo"),
            Sample(input="What is the capital of Italy?", target="Rome"),
        ],
        solver=[
            system_message("Reply with only the city name, without punctuation."),
            generate(),
        ],
        scorer=match(location="exact"),
    )
