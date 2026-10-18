"""Repair one Python function using a real model, Docker, and fixed tests."""

from pathlib import Path

from inspect_ai import Task, task
from inspect_ai.dataset import Sample
from inspect_ai.model import GenerateConfig
from inspect_ai.scorer import CORRECT, INCORRECT, Score, accuracy, scorer
from inspect_ai.solver import generate, system_message, use_tools
from inspect_ai.tool import bash
from inspect_ai.util import sandbox

HERE = Path(__file__).parent
STARTING_CODE = "def sum_even(numbers):\n    return sum(numbers)\n"


@scorer(metrics=[accuracy()])
def repair_tests():
    async def score(state, target):
        # Read through exec because Docker cp cannot reliably read tmpfs files.
        result = await sandbox("default").exec(["cat", "/workspace/project.py"])
        if not result.success:
            return Score(value=INCORRECT, explanation="project.py is missing or unreadable.")
        source = result.stdout

        # The model's shell tool cannot access this second, disconnected container.
        grader = sandbox("grader")
        await grader.write_file("/workspace/project.py", source)
        await grader.write_file(
            "/workspace/fixed_tests.py", (HERE / "fixed_tests.py").read_text()
        )
        result = await grader.exec(
            ["python", "-B", "-m", "unittest", "-v", "fixed_tests"], timeout=30
        )
        return Score(
            value=CORRECT if result.success else INCORRECT,
            answer=source,
            explanation=result.stdout + result.stderr,
            metadata={"test_exit_code": result.returncode},
        )

    return score


@task
def repair():
    return Task(
        dataset=[
            Sample(
                id="sum-even",
                input=(
                    "Fix /workspace/project.py so sum_even(numbers) returns the sum "
                    "of only the even integers. Handle empty lists and negative "
                    "integers, and do not modify the input list. "
                    "For example, sum_even([1, 2, 3, 4]) must return 6. "
                    "Use the bash tool to inspect, edit, and check the file."
                ),
                files={"/workspace/project.py": STARTING_CODE},
            )
        ],
        solver=[
            system_message(
                "You are fixing a Python function. Edit the actual file, not just "
                "your final reply. Work in /workspace and check your repair."
            ),
            use_tools(bash(timeout=30, sandbox="default")),
            generate(),
        ],
        sandbox=("docker", str(HERE / "compose.yaml")),
        scorer=repair_tests(),
        config=GenerateConfig(max_tokens=1024, max_retries=1, timeout=60),
        turn_limit=6,
    )
