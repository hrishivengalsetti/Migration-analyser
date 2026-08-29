import pytest
from pathlib import Path
from brain.diff_analyzer import analyze_file_diff, analyze_symbol_diff
from models import FileStatus, SymbolKind, SymbolChangeKind

def test_detects_added_file(tmp_path: Path):
    original_dir = tmp_path / "original"
    migrated_dir = tmp_path / "migrated"
    original_dir.mkdir()
    migrated_dir.mkdir()
    
    # Create file in migrated only
    file_path = migrated_dir / "new_file.py"
    file_path.write_text("print('hello')")
    
    diffs = analyze_file_diff(original_dir, migrated_dir)
    assert len(diffs) == 1
    assert diffs[0].file == "new_file.py"
    assert diffs[0].status == FileStatus.ADDED
    assert diffs[0].migrated_content == "print('hello')"
    assert diffs[0].original_content is None

def test_detects_deleted_file(tmp_path: Path):
    original_dir = tmp_path / "original"
    migrated_dir = tmp_path / "migrated"
    original_dir.mkdir()
    migrated_dir.mkdir()
    
    # Create file in original only
    file_path = original_dir / "old_file.py"
    file_path.write_text("print('bye')")
    
    diffs = analyze_file_diff(original_dir, migrated_dir)
    assert len(diffs) == 1
    assert diffs[0].file == "old_file.py"
    assert diffs[0].status == FileStatus.DELETED
    assert diffs[0].original_content == "print('bye')"
    assert diffs[0].migrated_content is None

def test_detects_modified_file(tmp_path: Path):
    original_dir = tmp_path / "original"
    migrated_dir = tmp_path / "migrated"
    original_dir.mkdir()
    migrated_dir.mkdir()
    
    # Create file in both with different content
    (original_dir / "mod_file.py").write_text("a = 1")
    (migrated_dir / "mod_file.py").write_text("a = 2")
    
    diffs = analyze_file_diff(original_dir, migrated_dir)
    assert len(diffs) == 1
    assert diffs[0].file == "mod_file.py"
    assert diffs[0].status == FileStatus.MODIFIED
    assert diffs[0].original_content == "a = 1"
    assert diffs[0].migrated_content == "a = 2"

def test_ignores_unchanged_file(tmp_path: Path):
    original_dir = tmp_path / "original"
    migrated_dir = tmp_path / "migrated"
    original_dir.mkdir()
    migrated_dir.mkdir()
    
    # Create file in both with same content
    (original_dir / "same_file.py").write_text("x = 10")
    (migrated_dir / "same_file.py").write_text("x = 10")
    
    diffs = analyze_file_diff(original_dir, migrated_dir)
    assert len(diffs) == 0

def test_only_python_files(tmp_path: Path):
    original_dir = tmp_path / "original"
    migrated_dir = tmp_path / "migrated"
    original_dir.mkdir()
    migrated_dir.mkdir()
    
    # Create text file
    (migrated_dir / "notes.txt").write_text("some notes")
    
    diffs = analyze_file_diff(original_dir, migrated_dir)
    assert len(diffs) == 0

def test_ignores_pycache(tmp_path: Path):
    original_dir = tmp_path / "original"
    migrated_dir = tmp_path / "migrated"
    original_dir.mkdir()
    migrated_dir.mkdir()
    
    # Create __pycache__ dir and a pyc file inside
    pycache_dir = migrated_dir / "__pycache__"
    pycache_dir.mkdir()
    (pycache_dir / "script.cpython-39.pyc").write_text("binary data")
    
    # also test ignoring .py files inside pycache (sometimes happens)
    (pycache_dir / "test.py").write_text("should be ignored")
    
    diffs = analyze_file_diff(original_dir, migrated_dir)
    assert len(diffs) == 0

def test_relative_paths(tmp_path: Path):
    original_dir = tmp_path / "original"
    migrated_dir = tmp_path / "migrated"
    original_dir.mkdir()
    migrated_dir.mkdir()
    
    # Create nested structure
    nested_dir = migrated_dir / "app" / "utils"
    nested_dir.mkdir(parents=True)
    (nested_dir / "helpers.py").write_text("def help(): pass")
    
    diffs = analyze_file_diff(original_dir, migrated_dir)
    assert len(diffs) == 1
    assert diffs[0].file == "app/utils/helpers.py"

def test_symbol_diff_detects_added_function(tmp_path: Path):
    original_dir = tmp_path / "original"
    migrated_dir = tmp_path / "migrated"
    original_dir.mkdir()
    migrated_dir.mkdir()
    
    (original_dir / "mod.py").write_text("")
    (migrated_dir / "mod.py").write_text("def new_func():\n    pass")
    
    file_diffs = analyze_file_diff(original_dir, migrated_dir)
    sym_diffs = analyze_symbol_diff(file_diffs, original_dir, migrated_dir)
    
    assert len(sym_diffs) == 1
    assert sym_diffs[0].symbol_id == "mod.new_func"
    assert sym_diffs[0].kind == SymbolKind.FUNCTION
    assert sym_diffs[0].change_kind == SymbolChangeKind.ADDED

def test_symbol_diff_detects_deleted_function(tmp_path: Path):
    original_dir = tmp_path / "original"
    migrated_dir = tmp_path / "migrated"
    original_dir.mkdir()
    migrated_dir.mkdir()
    
    (original_dir / "mod.py").write_text("def old_func():\n    pass")
    (migrated_dir / "mod.py").write_text("")
    
    file_diffs = analyze_file_diff(original_dir, migrated_dir)
    sym_diffs = analyze_symbol_diff(file_diffs, original_dir, migrated_dir)
    
    assert len(sym_diffs) == 1
    assert sym_diffs[0].symbol_id == "mod.old_func"
    assert sym_diffs[0].kind == SymbolKind.FUNCTION
    assert sym_diffs[0].change_kind == SymbolChangeKind.DELETED

def test_symbol_diff_detects_body_change(tmp_path: Path):
    original_dir = tmp_path / "original"
    migrated_dir = tmp_path / "migrated"
    original_dir.mkdir()
    migrated_dir.mkdir()
    
    (original_dir / "mod.py").write_text("def calc(x):\n    return x + 1")
    (migrated_dir / "mod.py").write_text("def calc(x):\n    return x + 2")
    
    file_diffs = analyze_file_diff(original_dir, migrated_dir)
    sym_diffs = analyze_symbol_diff(file_diffs, original_dir, migrated_dir)
    
    assert len(sym_diffs) == 1
    assert sym_diffs[0].symbol_id == "mod.calc"
    assert sym_diffs[0].kind == SymbolKind.FUNCTION
    assert sym_diffs[0].change_kind == SymbolChangeKind.BODY_CHANGED

def test_symbol_diff_detects_signature_change(tmp_path: Path):
    original_dir = tmp_path / "original"
    migrated_dir = tmp_path / "migrated"
    original_dir.mkdir()
    migrated_dir.mkdir()
    
    (original_dir / "mod.py").write_text("def calc(x):\n    return x + 1")
    (migrated_dir / "mod.py").write_text("def calc(x, y=1):\n    return x + y")
    
    file_diffs = analyze_file_diff(original_dir, migrated_dir)
    sym_diffs = analyze_symbol_diff(file_diffs, original_dir, migrated_dir)
    
    assert len(sym_diffs) == 1
    assert sym_diffs[0].symbol_id == "mod.calc"
    assert sym_diffs[0].kind == SymbolKind.FUNCTION
    assert sym_diffs[0].change_kind == SymbolChangeKind.SIGNATURE_CHANGED

def test_symbol_diff_detects_method_change(tmp_path: Path):
    original_dir = tmp_path / "original"
    migrated_dir = tmp_path / "migrated"
    original_dir.mkdir()
    migrated_dir.mkdir()
    
    (original_dir / "mod.py").write_text("class MyClass:\n    def run(self):\n        return 1")
    (migrated_dir / "mod.py").write_text("class MyClass:\n    def run(self):\n        return 2")
    
    file_diffs = analyze_file_diff(original_dir, migrated_dir)
    sym_diffs = analyze_symbol_diff(file_diffs, original_dir, migrated_dir)
    
    # Both class and method body will change
    method_diffs = [s for s in sym_diffs if s.kind == SymbolKind.METHOD]
    assert len(method_diffs) == 1
    assert method_diffs[0].symbol_id == "mod.MyClass.run"
    assert method_diffs[0].change_kind == SymbolChangeKind.BODY_CHANGED

def test_symbol_diff_ignores_unchanged_symbol(tmp_path: Path):
    original_dir = tmp_path / "original"
    migrated_dir = tmp_path / "migrated"
    original_dir.mkdir()
    migrated_dir.mkdir()
    
    (original_dir / "mod.py").write_text("def same():\n    pass\ndef changed():\n    return 1")
    (migrated_dir / "mod.py").write_text("def same():\n    pass\ndef changed():\n    return 2")
    
    file_diffs = analyze_file_diff(original_dir, migrated_dir)
    sym_diffs = analyze_symbol_diff(file_diffs, original_dir, migrated_dir)
    
    assert len(sym_diffs) == 1
    assert sym_diffs[0].symbol_id == "mod.changed"

def test_symbol_id_format(tmp_path: Path):
    original_dir = tmp_path / "original"
    migrated_dir = tmp_path / "migrated"
    original_dir.mkdir()
    migrated_dir.mkdir()
    
    pkg_dir = migrated_dir / "mypackage" / "utils"
    pkg_dir.mkdir(parents=True)
    (pkg_dir / "helpers.py").write_text("class Helper:\n    def do_work(self):\n        pass")
    
    file_diffs = analyze_file_diff(original_dir, migrated_dir)
    sym_diffs = analyze_symbol_diff(file_diffs, original_dir, migrated_dir)
    
    ids = {s.symbol_id for s in sym_diffs}
    assert "mypackage.utils.helpers.Helper" in ids
    assert "mypackage.utils.helpers.Helper.do_work" in ids

