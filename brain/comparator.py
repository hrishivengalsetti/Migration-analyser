from typing import Optional
from models import ComparisonStatus, SymbolTestComparison, BehavioralComparison

def compare_results(original_results: dict, migrated_results: dict) -> BehavioralComparison:
    """
    Deterministically compares test sandbox execution results between original and migrated runs.
    """
    orig_exit = original_results.get("exit_code", 0)
    migr_exit = migrated_results.get("exit_code", 0)

    orig_infra_failed = (orig_exit == -1 or orig_exit >= 2)
    migr_infra_failed = (migr_exit == -1 or migr_exit >= 2)

    # Build dictionaries mapping nodeid -> test_data (last record preserved if duplicate)
    orig_map = {}
    for t in original_results.get("tests", []):
        if "nodeid" in t:
            orig_map[t["nodeid"]] = t

    migr_map = {}
    for t in migrated_results.get("tests", []):
        if "nodeid" in t:
            migr_map[t["nodeid"]] = t

    all_nodeids = sorted(set(orig_map.keys()) | set(migr_map.keys()))

    test_results: list[SymbolTestComparison] = []

    regressions_count = 0
    fixed_count = 0
    unchanged_count = 0
    added_count = 0
    deleted_count = 0
    unverified_count = 0

    for nodeid in all_nodeids:
        orig_test = orig_map.get(nodeid)
        migr_test = migr_map.get(nodeid)

        status_orig = orig_test.get("outcome") if orig_test else None
        status_migr = migr_test.get("outcome") if migr_test else None

        msg_migr = migr_test.get("message") if migr_test else None
        stdout_migr = migrated_results.get("stdout") if migr_test else None
        stderr_migr = migrated_results.get("stderr") if migr_test else None

        # Determine comparison status
        if orig_infra_failed and migr_infra_failed:
            comp_status = ComparisonStatus.UNVERIFIED
        elif orig_infra_failed:
            comp_status = ComparisonStatus.UNVERIFIED
        elif migr_infra_failed:
            if status_orig == "passed":
                comp_status = ComparisonStatus.UNVERIFIED
            elif status_migr is None:
                comp_status = ComparisonStatus.UNVERIFIED
            else:
                comp_status = _classify_outcomes(status_orig, status_migr)
        else:
            comp_status = _classify_outcomes(status_orig, status_migr)

        # Increment aggregate counts
        if comp_status == ComparisonStatus.REGRESSION:
            regressions_count += 1
        elif comp_status == ComparisonStatus.FIXED:
            fixed_count += 1
        elif comp_status == ComparisonStatus.UNCHANGED:
            unchanged_count += 1
        elif comp_status == ComparisonStatus.ADDED:
            added_count += 1
        elif comp_status == ComparisonStatus.DELETED:
            deleted_count += 1
        elif comp_status == ComparisonStatus.UNVERIFIED:
            unverified_count += 1

        test_results.append(
            SymbolTestComparison(
                test_id=nodeid,
                status_original=status_orig,
                status_migrated=status_migr,
                comparison=comp_status,
                stdout_migrated=stdout_migr,
                stderr_migrated=stderr_migr,
                message=msg_migr,
            )
        )

    return BehavioralComparison(
        total_tests=len(test_results),
        regressions_count=regressions_count,
        fixed_count=fixed_count,
        unchanged_count=unchanged_count,
        added_count=added_count,
        deleted_count=deleted_count,
        unverified_count=unverified_count,
        test_results=test_results,
    )


def _classify_outcomes(status_orig: Optional[str], status_migr: Optional[str]) -> ComparisonStatus:
    if status_orig is None and status_migr is not None:
        return ComparisonStatus.ADDED
    if status_orig is not None and status_migr is None:
        return ComparisonStatus.DELETED

    # Both non-None
    if status_orig == "passed" and status_migr in ("failed", "error"):
        return ComparisonStatus.REGRESSION

    if status_orig in ("failed", "error", "skipped") and status_migr == "passed":
        return ComparisonStatus.FIXED

    # All other combinations (passed->passed, failed->failed, error->error, skipped->*, passed->skipped, etc.)
    return ComparisonStatus.UNCHANGED
