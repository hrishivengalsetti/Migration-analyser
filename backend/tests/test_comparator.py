import pytest
from brain.comparator import compare_results
from models import ComparisonStatus

def test_detects_regression_passed_to_failed():
    orig = {"exit_code": 0, "tests": [{"nodeid": "t1", "outcome": "passed"}]}
    migr = {"exit_code": 1, "tests": [{"nodeid": "t1", "outcome": "failed", "message": "AssertionError"}]}

    res = compare_results(orig, migr)
    assert res.regressions_count == 1
    assert res.test_results[0].comparison == ComparisonStatus.REGRESSION
    assert res.test_results[0].status_original == "passed"
    assert res.test_results[0].status_migrated == "failed"

def test_detects_regression_passed_to_error():
    orig = {"exit_code": 0, "tests": [{"nodeid": "t1", "outcome": "passed"}]}
    migr = {"exit_code": 1, "tests": [{"nodeid": "t1", "outcome": "error"}]}

    res = compare_results(orig, migr)
    assert res.regressions_count == 1
    assert res.test_results[0].comparison == ComparisonStatus.REGRESSION

def test_detects_fixed_failed_to_passed():
    orig = {"exit_code": 1, "tests": [{"nodeid": "t1", "outcome": "failed"}]}
    migr = {"exit_code": 0, "tests": [{"nodeid": "t1", "outcome": "passed"}]}

    res = compare_results(orig, migr)
    assert res.fixed_count == 1
    assert res.test_results[0].comparison == ComparisonStatus.FIXED

def test_detects_unchanged_passed_to_passed():
    orig = {"exit_code": 0, "tests": [{"nodeid": "t1", "outcome": "passed"}]}
    migr = {"exit_code": 0, "tests": [{"nodeid": "t1", "outcome": "passed"}]}

    res = compare_results(orig, migr)
    assert res.unchanged_count == 1
    assert res.test_results[0].comparison == ComparisonStatus.UNCHANGED

def test_detects_unchanged_failed_to_failed():
    orig = {"exit_code": 1, "tests": [{"nodeid": "t1", "outcome": "failed"}]}
    migr = {"exit_code": 1, "tests": [{"nodeid": "t1", "outcome": "failed"}]}

    res = compare_results(orig, migr)
    assert res.unchanged_count == 1
    assert res.test_results[0].comparison == ComparisonStatus.UNCHANGED

def test_handles_added_and_deleted_tests():
    orig = {"exit_code": 0, "tests": [{"nodeid": "t_del", "outcome": "passed"}]}
    migr = {"exit_code": 0, "tests": [{"nodeid": "t_add", "outcome": "passed"}]}

    res = compare_results(orig, migr)
    assert res.added_count == 1
    assert res.deleted_count == 1
    
    add_item = [t for t in res.test_results if t.test_id == "t_add"][0]
    del_item = [t for t in res.test_results if t.test_id == "t_del"][0]
    
    assert add_item.comparison == ComparisonStatus.ADDED
    assert del_item.comparison == ComparisonStatus.DELETED

def test_skipped_test_matrix():
    orig = {"exit_code": 0, "tests": [
        {"nodeid": "t_skip_skip", "outcome": "skipped"},
        {"nodeid": "t_skip_pass", "outcome": "skipped"},
        {"nodeid": "t_pass_skip", "outcome": "passed"},
    ]}
    migr = {"exit_code": 0, "tests": [
        {"nodeid": "t_skip_skip", "outcome": "skipped"},
        {"nodeid": "t_skip_pass", "outcome": "passed"},
        {"nodeid": "t_pass_skip", "outcome": "skipped"},
    ]}

    res = compare_results(orig, migr)
    t_skip_skip = [t for t in res.test_results if t.test_id == "t_skip_skip"][0]
    t_skip_pass = [t for t in res.test_results if t.test_id == "t_skip_pass"][0]
    t_pass_skip = [t for t in res.test_results if t.test_id == "t_pass_skip"][0]

    assert t_skip_skip.comparison == ComparisonStatus.UNCHANGED
    assert t_skip_pass.comparison == ComparisonStatus.FIXED
    assert t_pass_skip.comparison == ComparisonStatus.UNCHANGED

def test_infrastructure_failure_yields_unverified():
    orig = {"exit_code": 0, "tests": [{"nodeid": "t1", "outcome": "passed"}]}
    migr = {"exit_code": -1, "stdout": "Container timed out", "tests": []}

    res = compare_results(orig, migr)
    assert res.unverified_count == 1
    assert res.regressions_count == 0
    assert res.test_results[0].comparison == ComparisonStatus.UNVERIFIED

def test_deterministic_alphabetical_sorting():
    orig = {"exit_code": 0, "tests": [
        {"nodeid": "z_test", "outcome": "passed"},
        {"nodeid": "a_test", "outcome": "passed"},
        {"nodeid": "m_test", "outcome": "passed"}
    ]}
    migr = {"exit_code": 0, "tests": [
        {"nodeid": "z_test", "outcome": "passed"},
        {"nodeid": "a_test", "outcome": "passed"},
        {"nodeid": "m_test", "outcome": "passed"}
    ]}

    res = compare_results(orig, migr)
    nodeids = [t.test_id for t in res.test_results]
    assert nodeids == ["a_test", "m_test", "z_test"]

