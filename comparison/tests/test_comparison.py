"""Correctness checks for grading and the isolation used for generated code."""
import json
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from comparison.agent import run_agent
from comparison.cases import CASES, MAX_CALLS, MAX_OUTPUT_TOKENS
from comparison.run import configure
from comparison.sandbox import Workspace, docker, grade


class ComparisonTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        configure()

    def test_grading_rejects_bugs_and_accepts_references(self):
        for case_id, case in CASES.items():
            with self.subTest(case_id=case_id):
                self.assertFalse(grade(case_id, case["source"])["passed"])
                self.assertTrue(grade(case_id, case["reference"])["passed"])

    def test_invalid_python_is_a_failed_repair(self):
        self.assertFalse(grade("slug", "def slug(:\n")["passed"])

    def test_generated_code_has_no_host_mounts_or_network(self):
        with Workspace(CASES["slug"]["source"]) as workspace:
            info = json.loads(docker("inspect", workspace.name).stdout)[0]
            self.assertEqual(info["HostConfig"]["NetworkMode"], "none")
            self.assertTrue(info["HostConfig"]["ReadonlyRootfs"])
            self.assertFalse(info["HostConfig"].get("Binds"))
            self.assertTrue(all(m["Type"] == "tmpfs" for m in info["Mounts"]))
            names = {e.split("=", 1)[0] for e in info["Config"]["Env"]}
            self.assertFalse({"OPENAI_API_KEY", "DEEPSEEK_API_KEY"} & names)
            self.assertEqual(workspace.read_source(), CASES["slug"]["source"])
        self.assertNotEqual(docker("inspect", workspace.name, check=False).returncode, 0)


class AgentBudgetTests(unittest.TestCase):
    def response(self, tool_calls):
        message = SimpleNamespace(tool_calls=tool_calls,
            model_dump=lambda **kwargs: {"role": "assistant", "content": "done"})
        usage = SimpleNamespace(prompt_tokens=10, completion_tokens=1,
            model_dump=lambda: {"prompt_tokens": 10, "completion_tokens": 1})
        return SimpleNamespace(usage=usage, choices=[SimpleNamespace(message=message)])

    def run_with_response(self, response):
        with patch("comparison.agent.OpenAI") as client, patch("comparison.agent.Workspace") as workspace:
            client.return_value.chat.completions.create.return_value = response
            workspace.return_value.__enter__.return_value.execute.return_value = "{}"
            workspace.return_value.__enter__.return_value.read_source.return_value = CASES["slug"]["source"]
            with tempfile.TemporaryDirectory() as output:
                record = run_agent("slug", output)
            calls = client.return_value.chat.completions.create
            return record, calls

    def test_never_exceeds_declared_model_call_budget(self):
        tool_call = SimpleNamespace(id="fixture", function=SimpleNamespace(
            name="run_command", arguments=json.dumps({"command": "true"})))
        record, calls = self.run_with_response(self.response([tool_call]))
        self.assertEqual(calls.call_count, MAX_CALLS)
        self.assertEqual(record["model_calls"], MAX_CALLS)
        self.assertTrue(all(c.kwargs["max_tokens"] == MAX_OUTPUT_TOKENS for c in calls.call_args_list))

    def test_stops_spending_when_model_finishes(self):
        record, calls = self.run_with_response(self.response([]))
        self.assertEqual(calls.call_count, 1)
        self.assertEqual(record["model_calls"], 1)


if __name__ == "__main__":
    unittest.main()
