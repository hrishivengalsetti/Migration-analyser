import pytest
import docker
import time
from pathlib import Path
from brain.sandbox import run_tests_in_sandbox, _translate_nodeid

def docker_available():
    try:
        client = docker.from_env()
        client.ping()
        return True
    except Exception:
        return False

skip_no_docker = pytest.mark.skipif(
    not docker_available(), reason="Docker daemon not available or permission denied"
)

def test_nodeid_translation():
    assert _translate_nodeid("tests.test_service.test_calculate") == "/workspace/tests/test_service.py::test_calculate"
    assert _translate_nodeid("tests.test_service.TestClass.test_method") == "/workspace/tests/test_service.py::TestClass::test_method"
    assert _translate_nodeid("app.pkg.tests.test_unit.test_one") == "/workspace/app/pkg/tests/test_unit.py::test_one"

@skip_no_docker
def test_runs_passing_tests(tmp_path: Path):
    code_dir = tmp_path / "code"
    code_dir.mkdir()
    (code_dir / "test_success.py").write_text("""
def test_ok():
    assert 1 == 1
""")
    
    result = run_tests_in_sandbox(str(code_dir), test_nodeids=None)
    assert result["exit_code"] == 0
    assert result["summary"]["passed"] == 1
    assert result["summary"]["failed"] == 0
    assert len(result["tests"]) == 1
    assert result["tests"][0]["outcome"] == "passed"

@skip_no_docker
def test_runs_failing_tests(tmp_path: Path):
    code_dir = tmp_path / "code"
    code_dir.mkdir()
    (code_dir / "test_fail.py").write_text("""
def test_broken():
    assert 1 == 2
""")

    result = run_tests_in_sandbox(str(code_dir), test_nodeids=None)
    assert result["exit_code"] == 1
    assert result["summary"]["failed"] == 1
    assert len(result["tests"]) == 1
    assert result["tests"][0]["outcome"] == "failed"
    assert "assert 1 == 2" in result["tests"][0]["message"] or "AssertionError" in result["tests"][0]["message"]

@skip_no_docker
def test_nodeid_translation_and_execution(tmp_path: Path):
    code_dir = tmp_path / "code"
    code_dir.mkdir()
    (code_dir / "test_multi.py").write_text("""
def test_one():
    assert True
def test_two():
    assert False
""")
    
    # Run only test_one
    result = run_tests_in_sandbox(str(code_dir), test_nodeids=["test_multi.test_one"])
    assert result["exit_code"] == 0
    assert result["summary"]["passed"] == 1
    assert result["summary"]["failed"] == 0
    assert result["summary"]["total"] == 1
    assert result["tests"][0]["nodeid"] == "test_multi.py::test_one"

def test_empty_test_selection_returns_zero_summary(tmp_path: Path):
    # This shouldn't need Docker running as it short-circuits
    result = run_tests_in_sandbox(str(tmp_path), test_nodeids=[])
    assert result["exit_code"] == 0
    assert result["summary"]["total"] == 0
    assert result["stdout"] == "No tests selected."
    assert result["tests"] == []

@skip_no_docker
def test_read_only_mount_permissions(tmp_path: Path):
    code_dir = tmp_path / "code"
    code_dir.mkdir()
    (code_dir / "test_ro.py").write_text("""
def test_cannot_write():
    with open('/workspace/new_file.txt', 'w') as f:
        f.write('boom')
""")
    
    result = run_tests_in_sandbox(str(code_dir), test_nodeids=None)
    assert result["exit_code"] == 1
    assert result["summary"]["failed"] == 1
    assert "Read-only file system" in result["stdout"] or "PermissionError" in result["tests"][0]["message"]

@skip_no_docker
def test_timeout_handling(tmp_path: Path):
    code_dir = tmp_path / "code"
    code_dir.mkdir()
    (code_dir / "test_slow.py").write_text("""
import time
def test_timeout():
    time.sleep(10)
""")
    
    result = run_tests_in_sandbox(str(code_dir), test_nodeids=None, timeout=2)
    assert result["exit_code"] == -1
    assert "timed out after 2 seconds" in result["stderr"]
    assert result["summary"]["total"] == 0

@skip_no_docker
def test_container_cleanup(tmp_path: Path):
    client = docker.from_env()
    initial_count = len(client.containers.list(all=True, filters={"ancestor": "migration-verifier-runner:latest"}))
    
    code_dir = tmp_path / "code"
    code_dir.mkdir()
    (code_dir / "test_dummy.py").write_text("def test_ok(): pass")
    
    run_tests_in_sandbox(str(code_dir), test_nodeids=None)
    
    final_count = len(client.containers.list(all=True, filters={"ancestor": "migration-verifier-runner:latest"}))
    assert final_count == initial_count
