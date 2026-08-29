import ast
from pathlib import Path
from brain.diff_analyzer import _path_to_module_name


def _build_import_map(tree: ast.Module) -> dict[str, str]:
    """
    Map local imported names / aliases to full module or symbol paths.
    Examples:
        from app.service import calculate -> import_map["calculate"] = "app.service.calculate"
        import app.service as service -> import_map["service"] = "app.service"
        import app.service -> import_map["app.service"] = "app.service"
    """
    import_map = {}
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                full_mod = alias.name
                local_name = alias.asname or full_mod
                import_map[local_name] = full_mod
        elif isinstance(node, ast.ImportFrom):
            mod_name = node.module or ""
            for alias in node.names:
                name_in_mod = alias.name
                local_as = alias.asname or name_in_mod
                full_symbol = f"{mod_name}.{name_in_mod}" if mod_name else name_in_mod
                import_map[local_as] = full_symbol
    return import_map


def _test_references_affected(
    func_node: ast.FunctionDef | ast.AsyncFunctionDef,
    import_map: dict[str, str],
    affected_set: set[str]
) -> bool:
    """Check if a test function/method body references any affected symbol in affected_set."""
    for node in ast.walk(func_node):
        if isinstance(node, ast.Call):
            # 1. Direct function call: calculate()
            if isinstance(node.func, ast.Name):
                called_id = node.func.id
                if called_id in import_map:
                    resolved = import_map[called_id]
                    if resolved in affected_set:
                        return True
            # 2. Deterministic attribute call: service.calculate()
            elif isinstance(node.func, ast.Attribute):
                if isinstance(node.func.value, ast.Name):
                    base_name = node.func.value.id
                    attr_name = node.func.attr
                    if base_name in import_map:
                        candidate_id = f"{import_map[base_name]}.{attr_name}"
                        if candidate_id in affected_set:
                            return True

    return False


def select_tests(codebase_dir: Path, affected_symbols: list[str]) -> list[str]:
    """
    Discovers test functions in codebase_dir and returns sorted symbol IDs of tests
    that reference any symbol in affected_symbols.
    """
    affected_set = set(affected_symbols)
    if not affected_set or not codebase_dir.exists():
        return []

    selected_tests = set()

    test_files = [
        p for p in codebase_dir.rglob("*.py")
        if (p.name.startswith("test_") or p.name.endswith("_test.py"))
        and not any(part.startswith('.') or part == '__pycache__' for part in p.parts)
    ]

    for test_file in test_files:
        try:
            source = test_file.read_text(errors='replace')
            tree = ast.parse(source)
        except SyntaxError:
            continue

        rel_path_str = str(test_file.relative_to(codebase_dir))
        module_name = _path_to_module_name(rel_path_str)
        import_map = _build_import_map(tree)

        for node in tree.body:
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                if node.name.startswith("test_"):
                    test_id = f"{module_name}.{node.name}" if module_name else node.name
                    if _test_references_affected(node, import_map, affected_set):
                        selected_tests.add(test_id)
            elif isinstance(node, ast.ClassDef):
                class_id = f"{module_name}.{node.name}" if module_name else node.name
                for item in node.body:
                    if isinstance(item, ast.FunctionDef | ast.AsyncFunctionDef):
                        if item.name.startswith("test_"):
                            test_id = f"{class_id}.{item.name}"
                            if _test_references_affected(item, import_map, affected_set):
                                selected_tests.add(test_id)

    return sorted(selected_tests)
