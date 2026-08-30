import docker
import requests
import json
import io
import tarfile
import re
from typing import Optional
from pathlib import Path

def _translate_nodeid(symbol_id: str) -> str:
    """
    Translates a module-based symbol_id (e.g. tests.test_service.test_calculate) 
    into a pytest-compatible nodeid inside /workspace.
    Example: tests.test_service.test_calculate -> /workspace/tests/test_service.py::test_calculate
    Example: tests.test_service.TestClass.test_method -> /workspace/tests/test_service.py::TestClass::test_method
    """
    parts = symbol_id.split(".")
    # Try to find the file part (which ends with a 'test_' module or similar)
    # Since we can't reliably know the exact file boundary without the file system,
    # we assume the first part starting with 'test_' or the last part before uppercase class is the module.
    # Actually, a simpler standard approach for this project:
    # We know the symbol ID comes from brain/test_selector which uses dot-notation.
    # To keep it reliable statically, we convert the dot notation to a file path + nodeid string.
    # Example: tests.test_service.TestPricing.test_discount
    
    file_parts = []
    symbol_parts = []
    found_file = False
    
    for i, part in enumerate(parts):
        if not found_file:
            file_parts.append(part)
            if part.startswith("test_") or part.endswith("_test"):
                found_file = True
        else:
            symbol_parts.append(part)
            
    file_path = "/workspace/" + "/".join(file_parts) + ".py"
    
    if symbol_parts:
        return f"{file_path}::" + "::".join(symbol_parts)
    return file_path


def run_tests_in_sandbox(code_path: str, test_nodeids: Optional[list[str]] = None, timeout: int = 120) -> dict:
    """
    Run pytest in an isolated Docker container against the specified codebase.
    
    test_nodeids defines the execution mode:
      - None: Run all tests in /workspace
      - []: Run zero tests (returns zero-test summary without launching Docker)
      - [list]: Run only the specific selected test symbol IDs
    """
    # 1. Handle Empty Selection
    if test_nodeids is not None and len(test_nodeids) == 0:
        return {
            "summary": {"passed": 0, "failed": 0, "error": 0, "total": 0},
            "tests": [],
            "exit_code": 0,
            "stdout": "No tests selected.",
            "stderr": "",
        }

    # 2. Build pytest command
    base_cmd = ["--json-report", "--json-report-file=/tmp/results.json", "-q"]
    
    if test_nodeids is None:
        cmd_args = ["/workspace"] + base_cmd
    else:
        # Convert selected module IDs to pytest nodeids
        target_paths = [_translate_nodeid(t) for t in test_nodeids]
        cmd_args = target_paths + base_cmd

    command_str = " ".join(cmd_args)

    # 3. Connect to Docker and run
    client = docker.from_env()
    container = None
    
    try:
        container = client.containers.run(
            image="migration-verifier-runner:latest",
            command=cmd_args,
            volumes={str(Path(code_path).resolve()): {"bind": "/workspace", "mode": "ro"}},
            network_disabled=True,
            mem_limit="512m",
            nano_cpus=1_000_000_000,
            pids_limit=100,
            user="nobody",
            detach=True,
        )
        
        # Wait with timeout
        result = container.wait(timeout=timeout)
        exit_code = result.get("StatusCode", -1)
        
        # Capture logs
        stdout = container.logs(stdout=True, stderr=False).decode("utf-8", errors="replace")
        stderr = container.logs(stdout=False, stderr=True).decode("utf-8", errors="replace")
        
        # Parse JSON report
        tests_data = _read_json_report(container)
        
        if tests_data is None:
            # Fallback to stdout parsing
            tests_data = _fallback_parse_stdout(stdout, exit_code)
            
        return {
            "summary": tests_data.get("summary", {}),
            "tests": tests_data.get("tests", []),
            "exit_code": exit_code,
            "stdout": stdout,
            "stderr": stderr,
        }
        
    except docker.errors.ImageNotFound as e:
        raise RuntimeError(
            "Docker image 'migration-verifier-runner:latest' not found. "
            "Build it with: docker build -t migration-verifier-runner docker/test-runner"
        ) from e
    except docker.errors.APIError as e:
        if "No such image" in str(e):
            raise RuntimeError("Docker image 'migration-verifier-runner' not found.") from e
        raise
    except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError) as e:
        # Docker SDK / requests wraps urllib3.exceptions.ReadTimeoutError inside ConnectionError
        is_timeout = isinstance(e, requests.exceptions.ReadTimeout) or "Read timed out" in str(e) or "ReadTimeoutError" in str(e)
        if is_timeout and container:
            try:
                container.kill()
            except Exception:
                pass
            stdout = container.logs(stdout=True, stderr=False).decode("utf-8", errors="replace")
            stderr = container.logs(stdout=False, stderr=True).decode("utf-8", errors="replace")
            return {
                "summary": {"passed": 0, "failed": 0, "error": 0, "total": 0},
                "tests": [],
                "exit_code": -1,
                "stdout": stdout,
                "stderr": f"Container execution timed out after {timeout} seconds.\n{stderr}",
            }
        raise

    finally:
        if container:
            try:
                container.remove(force=True)
            except Exception:
                pass


def _read_json_report(container) -> Optional[dict]:
    """Extract and read /tmp/results.json from the container filesystem."""
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
    return None


def _normalize_json_report(report: dict) -> dict:
    """Convert pytest-json-report format into the standard data contract."""
    summary = report.get("summary", {})
    tests = []
    
    for test in report.get("tests", []):
        tests.append({
            "nodeid": test.get("nodeid", ""),
            "outcome": test.get("outcome", "error"),
            "duration": test.get("setup", {}).get("duration", 0.0) + test.get("call", {}).get("duration", 0.0),
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


def _extract_message(test_report: dict) -> Optional[str]:
    """Extract crash/failure traceback from the pytest json report."""
    if test_report.get("outcome") in ("failed", "error"):
        call_phase = test_report.get("call", {})
        crash = call_phase.get("crash", {})
        if crash:
            return f"{crash.get('message', '')} at {crash.get('path', '')}:{crash.get('lineno', '')}"
        longrepr = call_phase.get("longrepr")
        if longrepr:
            return str(longrepr)
    return None


def _fallback_parse_stdout(stdout: str, exit_code: int) -> dict:
    """Basic fallback parser if JSON report is unavailable or corrupt."""
    passed = len(re.findall(r"\bPASSED\b", stdout))
    failed = len(re.findall(r"\bFAILED\b", stdout))
    errors = len(re.findall(r"\bERROR\b", stdout))
    
    # If exit code is 0 but regex failed, assume 1 passed test just to reflect success
    if exit_code == 0 and passed == 0 and failed == 0 and errors == 0:
        passed = 1
        
    total = passed + failed + errors
    
    return {
        "summary": {
            "passed": passed,
            "failed": failed,
            "error": errors,
            "total": total
        },
        "tests": []
    }