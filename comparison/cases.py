"""Small, specified repair tasks. Reference implementations are grading controls."""

CASES = {
    "slug": {
        "requirement": "Fix slug(text). Lowercase ASCII letters, preserve ASCII digits, replace each run of all other characters with one hyphen, and remove leading/trailing hyphens. Empty or all-separator input returns an empty string.",
        "source": "def slug(text):\n    return text.lower().replace(' ', '-')\n",
        "reference": "import re\n\ndef slug(text):\n    return re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')\n",
    },
    "intervals": {
        "requirement": "Fix merge_intervals(intervals). Input is a list of [start, end] pairs with start <= end. Return sorted pairs, merging overlapping or touching intervals. Empty input returns []. Do not mutate the input or its nested pairs.",
        "source": "def merge_intervals(intervals):\n    if not intervals:\n        return []\n    result = [intervals[0]]\n    for start, end in intervals[1:]:\n        if start < result[-1][1]:\n            result[-1][1] = end\n        else:\n            result.append([start, end])\n    return result\n",
        "reference": "def merge_intervals(intervals):\n    result = []\n    for start, end in sorted(intervals):\n        if result and start <= result[-1][1]:\n            result[-1][1] = max(result[-1][1], end)\n        else:\n            result.append([start, end])\n    return result\n",
    },
    "chunks": {
        "requirement": "Fix chunks(items, size). Return a list of successive list slices, including a final shorter slice. Empty items returns []. Raise ValueError whenever size <= 0, including when items is empty. Input items is a list; size is an integer. Do not mutate items.",
        "source": "def chunks(items, size):\n    return [items[i:i + size] for i in range(0, len(items) - size + 1, size)]\n",
        "reference": "def chunks(items, size):\n    if size <= 0:\n        raise ValueError('size must be positive')\n    return [items[i:i + size] for i in range(0, len(items), size)]\n",
    },
}

SYSTEM = """You are repairing a small Python project. Use run_command to inspect and edit /workspace/project.py and run local checks. Implement the stated requirements without changing the function name. You have at most 6 model calls, each with at most 700 output tokens. The sandbox has Python and no network. Grading runs fixed tests outside your editable sandbox after you finish. When done, give a short summary without calling another tool."""
MODEL = "gpt-4o-mini-2024-07-18"
MAX_CALLS = 6
MAX_OUTPUT_TOKENS = 700
COMMAND_TIMEOUT = 15
OUTPUT_CHARS = 8000
TOOL_DESCRIPTION = "Run a shell command in the isolated project workspace."
ARG_DESCRIPTION = "Shell command to run in /workspace."


def prompt(case_id):
    return CASES[case_id]["requirement"] + "\nThe file is /workspace/project.py."
