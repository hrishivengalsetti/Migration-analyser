import pytest
from pathlib import Path
from brain.evidence_collector import collect_evidence
from models import (
    SymbolDiff,
    BlastRadius,
    BehavioralComparison,
    SymbolTestComparison,
    ComparisonStatus,
    SymbolKind,
    SymbolChangeKind
)

def test_attribute_test_to_correct_changed_symbol(tmp_path: Path):
    codebase = tmp_path / "code"
    app_dir = codebase / "app"
    tests_dir = codebase / "tests"
    app_dir.mkdir(parents=True)
    tests_dir.mkdir(parents=True)

    (app_dir / "calc.py").write_text("def add(): pass")
    (tests_dir / "test_calc.py").write_text("from app.calc import add\ndef test_add(): add()")

    symbol_diffs = [
        SymbolDiff(
            symbol_id="app.calc.add",
            file="app/calc.py",
            kind=SymbolKind.FUNCTION,
            change_kind=SymbolChangeKind.BODY_CHANGED
        )
    ]
    blast_radius = BlastRadius(
        changed_symbols=["app.calc.add"],
        directly_affected=[],
        transitively_affected=[],
        all_affected=[],
        cycles_detected=False,
        total_affected_count=0
    )
    behavioral_comp = BehavioralComparison(
        total_tests=1,
        regressions_count=1,
        fixed_count=0,
        unchanged_count=0,
        added_count=0,
        deleted_count=0,
        unverified_count=0,
        test_results=[
            SymbolTestComparison(
                test_id="tests/test_calc.py::test_add",
                status_original="passed",
                status_migrated="failed",
                comparison=ComparisonStatus.REGRESSION,
                message="AssertionError"
            )
        ]
    )

    evidence = collect_evidence(
        symbol_diffs=symbol_diffs,
        blast_radius=blast_radius,
        selected_test_ids=["tests/test_calc.py::test_add"],
        behavioral_comparison=behavioral_comp,
        codebase_dir=codebase
    )

    assert len(evidence) == 1
    ev = evidence[0]
    assert ev.symbol_id == "app.calc.add"
    assert ev.comparison == ComparisonStatus.REGRESSION
    assert ev.failing_tests == ["tests/test_calc.py::test_add"]

def test_attribute_test_to_affected_blast_radius_symbol(tmp_path: Path):
    codebase = tmp_path / "code"
    app_dir = codebase / "app"
    tests_dir = codebase / "tests"
    app_dir.mkdir(parents=True)
    tests_dir.mkdir(parents=True)

    (app_dir / "service.py").write_text("def process(): pass")
    (tests_dir / "test_service.py").write_text("from app.service import process\ndef test_proc(): process()")

    symbol_diffs = []
    blast_radius = BlastRadius(
        changed_symbols=["app.core.base"],
        directly_affected=["app.service.process"],
        transitively_affected=[],
        all_affected=["app.service.process"],
        cycles_detected=False,
        total_affected_count=1
    )
    behavioral_comp = BehavioralComparison(
        total_tests=1,
        regressions_count=1,
        fixed_count=0,
        unchanged_count=0,
        added_count=0,
        deleted_count=0,
        unverified_count=0,
        test_results=[
            SymbolTestComparison(
                test_id="tests/test_service.py::test_proc",
                status_original="passed",
                status_migrated="failed",
                comparison=ComparisonStatus.REGRESSION
            )
        ]
    )

    evidence = collect_evidence(
        symbol_diffs=symbol_diffs,
        blast_radius=blast_radius,
        selected_test_ids=["tests/test_service.py::test_proc"],
        behavioral_comparison=behavioral_comp,
        codebase_dir=codebase
    )

    ev = [e for e in evidence if e.symbol_id == "app.service.process"][0]
    assert ev.comparison == ComparisonStatus.REGRESSION
    assert ev.failing_tests == ["tests/test_service.py::test_proc"]

def test_unrelated_selected_tests_not_falsely_attributed(tmp_path: Path):
    codebase = tmp_path / "code"
    tests_dir = codebase / "tests"
    tests_dir.mkdir(parents=True)

    (tests_dir / "test_other.py").write_text("def test_other(): pass")

    blast_radius = BlastRadius(
        changed_symbols=["app.calc.add"],
        directly_affected=[],
        transitively_affected=[],
        all_affected=[],
        cycles_detected=False,
        total_affected_count=0
    )
    behavioral_comp = BehavioralComparison(
        total_tests=1,
        regressions_count=1,
        fixed_count=0,
        unchanged_count=0,
        added_count=0,
        deleted_count=0,
        unverified_count=0,
        test_results=[
            SymbolTestComparison(
                test_id="tests/test_other.py::test_other",
                status_original="passed",
                status_migrated="failed",
                comparison=ComparisonStatus.REGRESSION
            )
        ]
    )

    evidence = collect_evidence(
        symbol_diffs=[],
        blast_radius=blast_radius,
        selected_test_ids=["tests/test_other.py::test_other"],
        behavioral_comparison=behavioral_comp,
        codebase_dir=codebase
    )

    calc_ev = [e for e in evidence if e.symbol_id == "app.calc.add"][0]
    unattr_ev = [e for e in evidence if e.symbol_id == "<unattributed>"][0]

    assert calc_ev.comparison == ComparisonStatus.UNVERIFIED
    assert calc_ev.failing_tests == []
    assert unattr_ev.comparison == ComparisonStatus.REGRESSION
    assert unattr_ev.failing_tests == ["tests/test_other.py::test_other"]

def test_priority_regression_over_fixed(tmp_path: Path):
    codebase = tmp_path / "code"
    tests_dir = codebase / "tests"
    tests_dir.mkdir(parents=True)

    (tests_dir / "test_calc.py").write_text("""
from app.calc import add
def test_1(): add()
def test_2(): add()
""")

    blast_radius = BlastRadius(
        changed_symbols=["app.calc.add"],
        directly_affected=[],
        transitively_affected=[],
        all_affected=[],
        cycles_detected=False,
        total_affected_count=0
    )
    behavioral_comp = BehavioralComparison(
        total_tests=2,
        regressions_count=1,
        fixed_count=1,
        unchanged_count=0,
        added_count=0,
        deleted_count=0,
        unverified_count=0,
        test_results=[
            SymbolTestComparison(test_id="tests/test_calc.py::test_1", status_original="passed", status_migrated="failed", comparison=ComparisonStatus.REGRESSION),
            SymbolTestComparison(test_id="tests/test_calc.py::test_2", status_original="failed", status_migrated="passed", comparison=ComparisonStatus.FIXED)
        ]
    )

    evidence = collect_evidence(
        symbol_diffs=[],
        blast_radius=blast_radius,
        selected_test_ids=["tests/test_calc.py::test_1", "tests/test_calc.py::test_2"],
        behavioral_comparison=behavioral_comp,
        codebase_dir=codebase
    )

    ev = evidence[0]
    assert ev.comparison == ComparisonStatus.REGRESSION
    assert ev.failing_tests == ["tests/test_calc.py::test_1"]
    assert ev.passing_tests == ["tests/test_calc.py::test_2"]

def test_priority_unverified_over_fixed(tmp_path: Path):
    codebase = tmp_path / "code"
    tests_dir = codebase / "tests"
    tests_dir.mkdir(parents=True)

    (tests_dir / "test_calc.py").write_text("""
from app.calc import add
def test_1(): add()
def test_2(): add()
""")

    blast_radius = BlastRadius(
        changed_symbols=["app.calc.add"],
        directly_affected=[],
        transitively_affected=[],
        all_affected=[],
        cycles_detected=False,
        total_affected_count=0
    )
    behavioral_comp = BehavioralComparison(
        total_tests=2,
        regressions_count=0,
        fixed_count=1,
        unchanged_count=0,
        added_count=0,
        deleted_count=0,
        unverified_count=1,
        test_results=[
            SymbolTestComparison(test_id="tests/test_calc.py::test_1", status_original="passed", status_migrated=None, comparison=ComparisonStatus.UNVERIFIED),
            SymbolTestComparison(test_id="tests/test_calc.py::test_2", status_original="failed", status_migrated="passed", comparison=ComparisonStatus.FIXED)
        ]
    )

    evidence = collect_evidence(
        symbol_diffs=[],
        blast_radius=blast_radius,
        selected_test_ids=["tests/test_calc.py::test_1", "tests/test_calc.py::test_2"],
        behavioral_comparison=behavioral_comp,
        codebase_dir=codebase
    )

    ev = evidence[0]
    assert ev.comparison == ComparisonStatus.UNVERIFIED
    assert ev.unverified_tests == ["tests/test_calc.py::test_1"]
    assert ev.passing_tests == ["tests/test_calc.py::test_2"]

def test_priority_fixed_when_no_regression_or_unverified(tmp_path: Path):
    codebase = tmp_path / "code"
    tests_dir = codebase / "tests"
    tests_dir.mkdir(parents=True)

    (tests_dir / "test_calc.py").write_text("from app.calc import add\ndef test_1(): add()")

    blast_radius = BlastRadius(changed_symbols=["app.calc.add"], directly_affected=[], transitively_affected=[], all_affected=[], cycles_detected=False, total_affected_count=0)
    behavioral_comp = BehavioralComparison(
        total_tests=1, regressions_count=0, fixed_count=1, unchanged_count=0, added_count=0, deleted_count=0, unverified_count=0,
        test_results=[SymbolTestComparison(test_id="tests/test_calc.py::test_1", status_original="failed", status_migrated="passed", comparison=ComparisonStatus.FIXED)]
    )

    evidence = collect_evidence(
        symbol_diffs=[], blast_radius=blast_radius, selected_test_ids=["tests/test_calc.py::test_1"],
        behavioral_comparison=behavioral_comp, codebase_dir=codebase
    )

    assert evidence[0].comparison == ComparisonStatus.FIXED
    assert evidence[0].passing_tests == ["tests/test_calc.py::test_1"]

def test_no_attributed_tests_yields_unverified(tmp_path: Path):
    codebase = tmp_path / "code"
    codebase.mkdir()

    blast_radius = BlastRadius(changed_symbols=["app.calc.untested"], directly_affected=[], transitively_affected=[], all_affected=[], cycles_detected=False, total_affected_count=0)
    behavioral_comp = BehavioralComparison(total_tests=0, regressions_count=0, fixed_count=0, unchanged_count=0, added_count=0, deleted_count=0, unverified_count=0, test_results=[])

    evidence = collect_evidence(
        symbol_diffs=[], blast_radius=blast_radius, selected_test_ids=[],
        behavioral_comparison=behavioral_comp, codebase_dir=codebase
    )

    assert len(evidence) == 1
    assert evidence[0].symbol_id == "app.calc.untested"
    assert evidence[0].comparison == ComparisonStatus.UNVERIFIED

def test_deterministic_output_ordering(tmp_path: Path):
    codebase = tmp_path / "code"
    codebase.mkdir()

    blast_radius = BlastRadius(
        changed_symbols=["z_mod.z_func", "a_mod.a_func", "m_mod.m_func"],
        directly_affected=[], transitively_affected=[], all_affected=[], cycles_detected=False, total_affected_count=0
    )
    behavioral_comp = BehavioralComparison(total_tests=0, regressions_count=0, fixed_count=0, unchanged_count=0, added_count=0, deleted_count=0, unverified_count=0, test_results=[])

    evidence = collect_evidence(
        symbol_diffs=[], blast_radius=blast_radius, selected_test_ids=[],
        behavioral_comparison=behavioral_comp, codebase_dir=codebase
    )

    ids = [e.symbol_id for e in evidence]
    assert ids == ["a_mod.a_func", "m_mod.m_func", "z_mod.z_func"]
