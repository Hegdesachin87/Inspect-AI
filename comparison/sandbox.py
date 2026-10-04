"""Docker execution needed by the application-based comparison setups.

Generated code never runs on the host. Neither sandbox receives credentials or
host mounts. The grader is a separate container created after the agent exits.
"""
import json
import os
import subprocess
import uuid

from .cases import COMMAND_TIMEOUT, OUTPUT_CHARS


def docker(*args, input=None, timeout=60, check=True):
    result = subprocess.run(
        ["docker", *args], input=input, text=True, capture_output=True,
        timeout=timeout, check=False,
    )
    if check and result.returncode:
        raise RuntimeError(f"docker {args[0]} failed: {result.stderr[-3000:]}")
    return result


def restrictions(image):
    return [
        "--network", "none", "--read-only", "--cap-drop", "ALL",
        "--security-opt", "no-new-privileges", "--pids-limit", "64",
        "--memory", "256m", "--cpus", "1", "--user", "1000:1000",
        "--tmpfs", "/workspace:rw,size=32m,uid=1000,gid=1000,mode=700",
        "--tmpfs", "/tmp:rw,size=16m,uid=1000,gid=1000,mode=700",
        "--workdir", "/workspace", image,
    ]


def command_result(exit_code, stdout, stderr):
    return json.dumps({"exit_code": exit_code, "stdout": stdout[:OUTPUT_CHARS],
                       "stderr": stderr[:OUTPUT_CHARS]})


class Workspace:
    def __init__(self, source):
        self.source = source
        self.name = "inspect-comparison-" + uuid.uuid4().hex

    def __enter__(self):
        docker("run", "--detach", "--name", self.name,
               *restrictions(os.environ["COMPARISON_IMAGE"]), "sleep", "infinity")
        try:
            docker("exec", "-i", self.name, "python", "-c",
                   "import pathlib,sys; pathlib.Path('/workspace/project.py').write_text(sys.stdin.read())",
                   input=self.source)
        except BaseException:
            self.__exit__(None, None, None)
            raise
        return self

    def execute(self, command):
        # timeout(1) kills the command in the container, not only the Docker client.
        result = docker("exec", self.name, "timeout", "--kill-after=2s",
                        str(COMMAND_TIMEOUT), "sh", "-lc", command,
                        timeout=COMMAND_TIMEOUT + 10, check=False)
        return command_result(result.returncode, result.stdout, result.stderr)

    def read_source(self):
        return docker("exec", self.name, "cat", "/workspace/project.py").stdout

    def __exit__(self, *args):
        docker("rm", "--force", self.name, check=False)


# This runner is supplied by the experiment, not any evaluation framework.
# Tests are injected only into the separate grading container, never the workspace.
GRADE_SCRIPT = r'''
import contextlib, copy, io, json, pathlib, sys, traceback, unittest
req = json.load(sys.stdin)
pathlib.Path('/workspace/project.py').write_text(req['source'])
class RepairTests(unittest.TestCase):
    def test_slug(self):
        if req['case_id'] != 'slug': return
        for value, expected in [('Hello World', 'hello-world'), ('  A___B!!! ', 'a-b'),
                                ('---', ''), ('', ''), ('API v2.0', 'api-v2-0'),
                                ('a\tb\nc', 'a-b-c'), ('CAFÉ', 'caf')]:
            with self.subTest(value=value): self.assertEqual(module['slug'](value), expected)
    def test_intervals(self):
        if req['case_id'] != 'intervals': return
        for value, expected in [([], []), ([[5,7],[1,3],[2,6]], [[1,7]]),
                                ([[1,10],[2,3]], [[1,10]]), ([[1,2],[2,3]], [[1,3]]),
                                ([[5,6],[1,2]], [[1,2],[5,6]]), ([[2,2]], [[2,2]])]:
            with self.subTest(value=value):
                original = copy.deepcopy(value)
                self.assertEqual(module['merge_intervals'](value), expected)
                self.assertEqual(value, original)
    def test_chunks(self):
        if req['case_id'] != 'chunks': return
        for value, size, expected in [([1,2,3,4,5],2,[[1,2],[3,4],[5]]),
                                     ([],3,[]), ([1,2],5,[[1,2]]), ([1,2],1,[[1],[2]])]:
            with self.subTest(value=value,size=size):
                original = value.copy()
                self.assertEqual(module['chunks'](value,size),expected)
                self.assertEqual(value,original)
        for value in [[],[1,2]]:
            for size in [0,-1]:
                with self.subTest(value=value,size=size):
                    with self.assertRaises(ValueError): module['chunks'](value,size)
try:
    module = {'__name__': 'project'}
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        exec(compile(req['source'], 'project.py', 'exec'), module)
        suite = unittest.TestSuite([RepairTests('test_' + req['case_id'])])
        stream = io.StringIO()
        result = unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
    report = {'passed': result.wasSuccessful(), 'test_output': stream.getvalue()}
except BaseException:
    report = {'passed': False, 'test_output': traceback.format_exc()}
print(json.dumps(report))
'''


def grade(case_id, source):
    """Grade cooperative repairs. This is not an adversarial anti-cheating system."""
    name = "inspect-comparison-grade-" + uuid.uuid4().hex
    try:
        result = docker(
            "run", "--rm", "--interactive", "--name", name,
            *restrictions(os.environ["COMPARISON_IMAGE"]),
            "python", "-I", "-c", GRADE_SCRIPT,
            input=json.dumps({"case_id": case_id, "source": source}), timeout=30,
            check=False,
        )
        if result.returncode:
            return {"passed": False, "test_output": result.stderr[-OUTPUT_CHARS:]}
        return json.loads(result.stdout)
    finally:
        # Also handles timeout, for which --rm alone would leave a running container.
        docker("rm", "--force", name, check=False)
