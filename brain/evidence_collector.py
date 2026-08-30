import ast
from pathlib import Path
from typing import Optional
from models import (
    SymbolDiff,
    BlastRadius,
    BehavioralComparison,
    Evidence,
    ComparisonStatus,
    SymbolChangeKind
)
from brain.diff_analyzer import _path_to_module_name
from brain.test_selector import _build_import_map


from typing import Union

def _map_test_to_candidate_symbols(
    test_nodeid: str,
    codebase_dir: Path,
    candidate_symbols: set[str]
) -> set[str]:
    """
    Statically analyzes a selected test function/method in codebase_dir
    and returns all candidate symbol_ids referenced in its body.
    """
    # Convert nodeid (e.g., "tests/test_service.py::test_calc" or "tests.test_service.test_calc") to file path
    parts = test_nodeid.split("::")
    path_part = parts[0]
    func_name = parts[-1] if len(parts) > 1 else None

    # Resolve file path
    if path_part.endswith(".py"):
        rel_path = Path(path_part)
    else:
        # Dot notation
        mod_parts = path_part.split(".")
        rel_path = Path("/".join(mod_parts) + ".py")

    test_file_path = codebase_dir / rel_path
    if not test_file_path.exists():
        return set()

    try:
        source = test_file_path.read_text(errors="replace")
        tree = ast.parse(source)
    except Exception:
        return set()

    import_map = _build_import_map(tree)
    referenced = set()

    # Locate target test function/method AST node
    target_node = None
    if func_name:
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == func_name:
                target_node = node
                break
            elif isinstance(node, ast.ClassDef):
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) and item.name == func_name:
                        target_node = item
                        break
    else:
        target_node = tree

    if not target_node:
        target_node = tree

    # Walk calls in function body
    for node in ast.walk(target_node):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                called_id = node.func.id
                if called_id in import_map:
                    resolved = import_map[called_id]
                    if resolved in candidate_symbols:
                        referenced.add(resolved)
            elif isinstance(node.func, ast.Attribute):
                if isinstance(node.func.value, ast.Name):
                    base_name = node.func.value.id
                    attr_name = node.func.attr
                    if base_name in import_map:
                        candidate_id = f"{import_map[base_name]}.{attr_name}"
                        if candidate_id in candidate_symbols:
                            referenced.add(candidate_id)

    return referenced


def collect_evidence(
    symbol_diffs: list[SymbolDiff],
    blast_radius: BlastRadius,
    selected_test_ids: list[str],
    behavioral_comparison: BehavioralComparison,
    codebase_dir: Path
) -> list[Evidence]:
    """
    Deterministically attributes test comparison outcomes to changed and blast-radius affected symbols.
    """
    # 1. Candidate Symbol Set
    changed_syms = set(blast_radius.changed_symbols)
    affected_syms = set(blast_radius.all_affected)
    candidate_symbols = changed_syms | affected_syms

    # Map symbol_id -> SymbolDiff for file and change_kind lookup
    diff_map: dict[str, SymbolDiff] = {sd.symbol_id: sd for sd in symbol_diffs}

    # Map test_id -> TestResultComparison from TASK-009
    comp_map = {tc.test_id: tc for tc in behavioral_comparison.test_results}

    # 2. Reconstruct Symbol -> Test Mapping using Static AST Analysis
    symbol_to_tests: dict[str, set[str]] = {sym: set() for sym in candidate_symbols}
    mapped_tests: set[str] = set()

    for test_id in selected_test_ids:
        referenced_syms = _map_test_to_candidate_symbols(test_id, codebase_dir, candidate_symbols)
        for sym in referenced_syms:
            symbol_to_tests[sym].add(test_id)
            mapped_tests.add(test_id)

    # Also check all test_results nodeids in behavioral_comparison against static mapping
    for tc in behavioral_comparison.test_results:
        referenced_syms = _map_test_to_candidate_symbols(tc.test_id, codebase_dir, candidate_symbols)
        for sym in referenced_syms:
            symbol_to_tests[sym].add(tc.test_id)
            mapped_tests.add(tc.test_id)

    evidence_list: list[Evidence] = []

    # 3. Build Evidence per Candidate Symbol
    for sym in sorted(candidate_symbols):
        test_ids = symbol_to_tests[sym]
        failing_tests = set()
        passing_tests = set()
        unverified_tests = set()

        has_regression = False
        has_fixed = False
        has_unverified = False
        has_unchanged = False

        for tid in test_ids:
            if tid in comp_map:
                tc = comp_map[tid]
                if tc.comparison == ComparisonStatus.REGRESSION:
                    has_regression = True
                    failing_tests.add(tid)
                elif tc.comparison == ComparisonStatus.UNVERIFIED:
                    has_unverified = True
                    unverified_tests.add(tid)
                elif tc.comparison == ComparisonStatus.FIXED:
                    has_fixed = True
                    passing_tests.add(tid)
                elif tc.comparison == ComparisonStatus.UNCHANGED:
                    has_unchanged = True
                    if tc.status_migrated == "passed":
                        passing_tests.add(tid)
                    elif tc.status_migrated in ("failed", "error"):
                        failing_tests.add(tid)

        # Determine Aggregate Symbol Comparison Status
        # Priority: REGRESSION > UNVERIFIED > FIXED > UNCHANGED
        if has_regression:
            overall_comp = ComparisonStatus.REGRESSION
        elif has_unverified or len(test_ids) == 0:
            overall_comp = ComparisonStatus.UNVERIFIED
        elif has_fixed:
            overall_comp = ComparisonStatus.FIXED
        elif has_unchanged:
            overall_comp = ComparisonStatus.UNCHANGED
        else:
            overall_comp = ComparisonStatus.UNVERIFIED

        # Lookup file and change_kind
        sd = diff_map.get(sym)
        file_path = sd.file if sd else "unknown"
        change_kind = sd.change_kind if sd else None

        evidence_list.append(
            Evidence(
                symbol_id=sym,
                file=file_path,
                change_kind=change_kind,
                comparison=overall_comp,
                failing_tests=sorted(failing_tests),
                passing_tests=sorted(passing_tests),
                unverified_tests=sorted(unverified_tests),
            )
        )

    # 4. Handle Unattributed Tests
    unattributed_tests = [
        tc for tc in behavioral_comparison.test_results
        if tc.test_id not in mapped_tests
    ]

    if unattributed_tests:
        u_failing = set()
        u_passing = set()
        u_unverified = set()

        u_has_reg = False
        u_has_unver = False
        u_has_fix = False

        for tc in unattributed_tests:
            tid = tc.test_id
            if tc.comparison == ComparisonStatus.REGRESSION:
                u_has_reg = True
                u_failing.add(tid)
            elif tc.comparison == ComparisonStatus.UNVERIFIED:
                u_has_unver = True
                u_unverified.add(tid)
            elif tc.comparison == ComparisonStatus.FIXED:
                u_has_fix = True
                u_passing.add(tid)
            elif tc.comparison == ComparisonStatus.UNCHANGED:
                if tc.status_migrated == "passed":
                    u_passing.add(tid)
                else:
                    u_failing.add(tid)

        if u_has_reg:
            u_comp = ComparisonStatus.REGRESSION
        elif u_has_unver:
            u_comp = ComparisonStatus.UNVERIFIED
        elif u_has_fix:
            u_comp = ComparisonStatus.FIXED
        else:
            u_comp = ComparisonStatus.UNCHANGED

        evidence_list.append(
            Evidence(
                symbol_id="<unattributed>",
                file="unattributed",
                change_kind=None,
                comparison=u_comp,
                failing_tests=sorted(u_failing),
                passing_tests=sorted(u_passing),
                unverified_tests=sorted(u_unverified),
            )
        )

    # 5. Deterministic Sort by symbol_id
    evidence_list.sort(key=lambda e: e.symbol_id)
    return evidence_list
