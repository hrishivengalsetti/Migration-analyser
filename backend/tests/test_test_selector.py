import pytest
from pathlib import Path
from brain.test_selector import select_tests

def test_selects_test_covering_affected_symbol(tmp_path: Path):
    code_dir = tmp_path / "codebase"
    app_dir = code_dir / "app"
    tests_dir = code_dir / "tests"
    app_dir.mkdir(parents=True)
    tests_dir.mkdir(parents=True)

    (app_dir / "service.py").write_text("def calculate():\n    return 42")
    (tests_dir / "test_service.py").write_text("""
from app.service import calculate

def test_calculate():
    assert calculate() == 42
""")

    affected = ["app.service.calculate"]
    selected = select_tests(code_dir, affected)
    assert selected == ["tests.test_service.test_calculate"]

def test_selects_test_via_aliased_module_attribute_call(tmp_path: Path):
    code_dir = tmp_path / "codebase"
    app_dir = code_dir / "app"
    tests_dir = code_dir / "tests"
    app_dir.mkdir(parents=True)
    tests_dir.mkdir(parents=True)

    (app_dir / "service.py").write_text("def calculate():\n    return 42")
    (tests_dir / "test_service.py").write_text("""
import app.service as service

def test_calculate():
    assert service.calculate() == 42
""")

    affected = ["app.service.calculate"]
    selected = select_tests(code_dir, affected)
    assert selected == ["tests.test_service.test_calculate"]

def test_excludes_test_not_covering_affected_symbol(tmp_path: Path):
    code_dir = tmp_path / "codebase"
    tests_dir = code_dir / "tests"
    tests_dir.mkdir(parents=True)

    (tests_dir / "test_other.py").write_text("""
def test_unrelated():
    assert 1 + 1 == 2
""")

    affected = ["app.service.calculate"]
    selected = select_tests(code_dir, affected)
    assert selected == []

def test_returns_empty_when_no_tests_exist(tmp_path: Path):
    code_dir = tmp_path / "codebase"
    code_dir.mkdir()

    selected = select_tests(code_dir, ["app.service.calculate"])
    assert selected == []

def test_returns_empty_when_no_affected_symbols(tmp_path: Path):
    code_dir = tmp_path / "codebase"
    tests_dir = code_dir / "tests"
    tests_dir.mkdir(parents=True)

    (tests_dir / "test_service.py").write_text("""
from app.service import calculate

def test_calculate():
    assert calculate() == 42
""")

    selected = select_tests(code_dir, [])
    assert selected == []

def test_handles_syntax_error_in_test_file(tmp_path: Path):
    code_dir = tmp_path / "codebase"
    tests_dir = code_dir / "tests"
    tests_dir.mkdir(parents=True)

    (tests_dir / "test_invalid.py").write_text("def test_broken( invalid python syntax :::")
    (tests_dir / "test_valid.py").write_text("""
from app.service import calculate
def test_valid():
    calculate()
""")

    affected = ["app.service.calculate"]
    selected = select_tests(code_dir, affected)
    assert selected == ["tests.test_valid.test_valid"]

def test_discovers_test_methods_in_class(tmp_path: Path):
    code_dir = tmp_path / "codebase"
    tests_dir = code_dir / "tests"
    tests_dir.mkdir(parents=True)

    (tests_dir / "test_service.py").write_text("""
from app.service import calculate

class TestService:
    def test_calculate(self):
        assert calculate() == 42
""")

    affected = ["app.service.calculate"]
    selected = select_tests(code_dir, affected)
    assert selected == ["tests.test_service.TestService.test_calculate"]

def test_symbol_id_format_correct(tmp_path: Path):
    code_dir = tmp_path / "codebase"
    tests_dir = code_dir / "pkg" / "tests"
    tests_dir.mkdir(parents=True)

    (tests_dir / "test_helpers.py").write_text("""
from app.utils import helper

class TestHelpers:
    def test_one(self):
        helper()

def test_two():
    helper()
""")

    affected = ["app.utils.helper"]
    selected = select_tests(code_dir, affected)
    assert selected == [
        "pkg.tests.test_helpers.TestHelpers.test_one",
        "pkg.tests.test_helpers.test_two"
    ]
