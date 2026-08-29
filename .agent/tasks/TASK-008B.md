# TASK-008B: Sandbox Executor — Python Docker SDK Client

**Milestone**: M5  
**Assigned to**: LatentCode  
**Status**: pending  
**Depends on**: TASK-008A (complete)  

---

## Goal

Implement the sandboxed test execution engine using the Python Docker SDK. Given a path to a Python codebase directory, run pytest inside an isolated Docker container with strict security limits, capture the JSON test report, and return parsed results. This runs pytest for both the original and migrated codebases separately.

---

## Context Files to Read

Before implementing:
1. `.agent/constitution.md`
2. `.agent/architecture.md`
3. `docker/test-runner/Dockerfile` (from TASK-008A)
4. `backend/models.py`
5. This task file

---

## Inputs

- `code_path: str` — absolute path to the codebase directory to test (either original or migrated, unzipped)

## Outputs

```
backend/pipeline/sandbox.py      ← New file
backend/tests/test_sandbox.py    ← New file
backend/requirements.txt         ← Updated: add docker dependency
```

---

## Acceptance Criteria

### AC-1: Function signature
```python
def run_tests_in_sandbox(code_path: str) -> dict:
    """
    Run pytest in an isolated Docker container.
    
    Returns dict with structure:
    {
        "summary": {"passed": int, "failed": int, "error": int, "total": int},
        "tests": [
            {
                "nodeid": "test_module.py::test_function",
                "outcome": "passed" | "failed" | "error",
                "duration": float,
                "message": str | None  # failure message if any
            },
            ...
        ],
        "exit_code": int,
        "stdout": str,
        "stderr": str
    }
    """
```

### AC-2: Uses Docker Python SDK
- Uses `docker.from_env()` to connect to the Docker daemon
- Creates a container from `migration-verifier-runner` image

### AC-3: Security constraints enforced
- The container MUST be created with ALL of the following:
  - `volumes`: `{code_path: {"bind": "/workspace", "mode": "ro"}}` — read-only bind mount
  - `network_disabled`: `True` — no internet access
  - `mem_limit`: `"512m"` — memory cap
  - `nano_cpus`: `1_000_000_000` — 1 CPU core
  - `pids_limit`: `100` — process limit
  - `user`: `"nobody"` — non-root execution

### AC-4: Command execution
- Container runs: `pytest /workspace --json-report --json-report-file=/tmp/results.json -q`
- Waits for the container to finish (with a timeout of 120 seconds)
- If the container exceeds the timeout, kills it and returns a result with `exit_code: -1` and an error message

### AC-5: Result parsing
- After container finishes, reads `/tmp/results.json` from the container filesystem using `container.get_archive()`
- Parses the JSON report into the return dict structure
- If JSON report is missing or corrupt, falls back to parsing stdout for basic pass/fail counts

### AC-6: Cleanup
- Container is ALWAYS removed after execution (use `try/finally`)
- No containers are left running or stopped after the function returns

### AC-7: Error handling
- If Docker is not running or the image does not exist, raises a clear `RuntimeError` with a descriptive message
- If the container crashes, captures whatever stdout/stderr is available and returns it

### AC-8: All tests pass
- `cd backend && pytest tests/test_sandbox.py -v` exits with code 0

---

## Non-Goals

- Do NOT build the Docker image (that is TASK-008A)
- Do NOT compare test results between codebases (that is TASK-009)
- Do NOT implement test selection filtering — run ALL tests found in the codebase
- Do NOT stream container logs in real-time
- Do NOT implement container caching or pooling

---

## Technical Constraints

- `docker` Python package (add to `backend/requirements.txt`)
- Image name: `migration-verifier-runner` (must match TASK-008A)
- Container timeout: 120 seconds max
- All container resources must be cleaned up

---

## Algorithm

```python
import docker
import json
import io
import tarfile

def run_tests_in_sandbox(code_path: str) -> dict:
    client = docker.from_env()
    container = None
    
    try:
        container = client.containers.run(
            image="migration-verifier-runner",
            command="pytest /workspace --json-report --json-report-file=/tmp/results.json -q",
            volumes={code_path: {"bind": "/workspace", "mode": "ro"}},
            network_disabled=True,
            mem_limit="512m",
            nano_cpus=1_000_000_000,
            pids_limit=100,
            user="nobody",
            detach=True,
        )
        
        # Wait for completion with timeout
        result = container.wait(timeout=120)
        exit_code = result.get("StatusCode", -1)
        
        # Capture stdout/stderr
        stdout = container.logs(stdout=True, stderr=False).decode("utf-8", errors="replace")
        stderr = container.logs(stdout=False, stderr=True).decode("utf-8", errors="replace")
        
        # Try to read JSON report
        tests_data = _read_json_report(container)
        if tests_data is None:
            tests_data = _fallback_parse_stdout(stdout, exit_code)
        
        return {
            "summary": tests_data.get("summary", {}),
            "tests": tests_data.get("tests", []),
            "exit_code": exit_code,
            "stdout": stdout,
            "stderr": stderr,
        }
        
    except Exception as e:
        if "No such image" in str(e) or "Error while fetching" in str(e):
            raise RuntimeError(
                "Docker image 'migration-verifier-runner' not found. "
                "Build it with: docker build -t migration-verifier-runner docker/test-runner"
            ) from e
        raise
        
    finally:
        if container:
            try:
                container.remove(force=True)
            except Exception:
                pass


def _read_json_report(container) -> dict | None:
    """Read /tmp/results.json from container filesystem."""
    try:
        bits, _ = container.get_archive("/tmp/results.json")
        stream = io.BytesIO(b"".join(bits))
        with tarfile.open(fileobj=stream) as tar:
            member = tar.getmembers()[0]
            f = tar.extractfile(member)
            if f:
                report = json.loads(f.read())
                return _normalize_json_report(report)
    except Exception:
        return None


def _normalize_json_report(report: dict) -> dict:
    """Convert pytest-json-report format to our standard format."""
    summary = report.get("summary", {})
    tests = []
    for test in report.get("tests", []):
        tests.append({
            "nodeid": test.get("nodeid", ""),
            "outcome": test.get("outcome", "error"),
            "duration": test.get("duration", 0.0),
            "message": _extract_message(test),
        })
    return {
        "summary": {
            "passed": summary.get("passed", 0),
            "failed": summary.get("failed", 0),
            "error": summary.get("error", 0),
            "total": summary.get("total", 0),
        },
        "tests": tests,
    }
```

You may implement this exactly as shown or adjust as long as all ACs pass.

---

## Test Requirements

Write tests in `backend/tests/test_sandbox.py`:

**Important**: These tests require Docker to be running. Mark all tests with `@pytest.mark.skipif` if Docker is not available.

```python
import pytest
import docker

def docker_available():
    try:
        client = docker.from_env()
        client.ping()
        return True
    except Exception:
        return False

skip_no_docker = pytest.mark.skipif(
    not docker_available(), reason="Docker not available"
)
```

1. `test_runs_passing_tests` — create a temp dir with a simple `test_example.py` that has 1 passing test → result has `exit_code=0`, `summary.passed=1`
2. `test_runs_failing_tests` — create a temp dir with a failing test → result has `summary.failed >= 1`
3. `test_returns_test_details` — verify each test in `tests` list has `nodeid`, `outcome`, `duration` fields
4. `test_container_cleanup` — after execution, no container with our image is left running
5. `test_read_only_mount` — the test cannot write to `/workspace` (container should still work with read-only mount)

---

## Verification

```bash
cd backend && pytest tests/test_sandbox.py -v
```

Note: Tests will be skipped if Docker is not running. This is acceptable.

---

## Blocker Section

*(LatentCode fills this in if blocked)*

---

## Implementation Plan

*(LatentCode fills this in before implementing)*
