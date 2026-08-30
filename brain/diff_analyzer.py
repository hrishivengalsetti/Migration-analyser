import ast
from pathlib import Path
from models import FileDiff, FileStatus, SymbolDiff, SymbolKind, SymbolChangeKind

def analyze_file_diff(original_dir: Path, migrated_dir: Path) -> list[FileDiff]:
    diffs = []

    original_files = {
        p.relative_to(original_dir): p
        for p in original_dir.rglob("*.py")
        if not any(part.startswith('.') or part == '__pycache__' for part in p.parts)
    }

    migrated_files = {
        p.relative_to(migrated_dir): p
        for p in migrated_dir.rglob("*.py")
        if not any(part.startswith('.') or part == '__pycache__' for part in p.parts)
    }

    all_keys = set(original_files) | set(migrated_files)

    for rel_path in sorted(all_keys):
        if rel_path in original_files and rel_path not in migrated_files:
            # deleted
            diffs.append(FileDiff(
                file=str(rel_path),
                status=FileStatus.DELETED,
                original_content=original_files[rel_path].read_text(errors='replace'),
            ))
        elif rel_path not in original_files and rel_path in migrated_files:
            # added
            diffs.append(FileDiff(
                file=str(rel_path),
                status=FileStatus.ADDED,
                migrated_content=migrated_files[rel_path].read_text(errors='replace'),
            ))
        else:
            # both exist — compare
            orig_content = original_files[rel_path].read_text(errors='replace')
            migr_content = migrated_files[rel_path].read_text(errors='replace')
            if orig_content != migr_content:
                diffs.append(FileDiff(
                    file=str(rel_path),
                    status=FileStatus.MODIFIED,
                    original_content=orig_content,
                    migrated_content=migr_content,
                ))

    return diffs


def _path_to_module_name(rel_path: str) -> str:
    path_obj = Path(rel_path)
    parts = list(path_obj.parts)
    if parts[-1].endswith(".py"):
        parts[-1] = parts[-1][:-3]
    if parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


from typing import Union

def _extract_signature(node: Union[ast.FunctionDef, ast.AsyncFunctionDef]) -> str:
    return ast.unparse(node.args)


def extract_symbols(source: str, module_name: str) -> dict[str, dict]:
    """
    Returns a dict mapping symbol_id -> {kind, source, signature, lineno}
    """
    if not source.strip():
        return {}
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return {}

    symbols = {}

    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            sym_id = f"{module_name}.{node.name}" if module_name else node.name
            symbols[sym_id] = {
                "kind": SymbolKind.FUNCTION,
                "source": ast.unparse(node),
                "signature": _extract_signature(node),
                "lineno": node.lineno
            }
        elif isinstance(node, ast.ClassDef):
            class_id = f"{module_name}.{node.name}" if module_name else node.name
            symbols[class_id] = {
                "kind": SymbolKind.CLASS,
                "source": ast.unparse(node),
                "signature": f"class {node.name}",
                "lineno": node.lineno
            }
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    method_id = f"{class_id}.{item.name}"
                    symbols[method_id] = {
                        "kind": SymbolKind.METHOD,
                        "source": ast.get_source_segment(source, item) or ast.unparse(item),
                        "signature": _extract_signature(item),
                        "lineno": item.lineno,
                    }

    return symbols


def analyze_symbol_diff(
    file_diffs: list[FileDiff],
    original_dir: Path,
    migrated_dir: Path
) -> list[SymbolDiff]:
    symbol_diffs = []

    for fdiff in file_diffs:
        if fdiff.status == FileStatus.UNCHANGED:
            continue

        module_name = _path_to_module_name(fdiff.file)
        orig_symbols = extract_symbols(fdiff.original_content or "", module_name)
        migr_symbols = extract_symbols(fdiff.migrated_content or "", module_name)

        all_symbol_ids = set(orig_symbols.keys()) | set(migr_symbols.keys())

        for sym_id in sorted(all_symbol_ids):
            in_orig = sym_id in orig_symbols
            in_migr = sym_id in migr_symbols

            if in_migr and not in_orig:
                migr_info = migr_symbols[sym_id]
                symbol_diffs.append(SymbolDiff(
                    symbol_id=sym_id,
                    file=fdiff.file,
                    kind=migr_info["kind"],
                    change_kind=SymbolChangeKind.ADDED,
                    migrated_source=migr_info["source"],
                    line_migrated=migr_info["lineno"],
                ))
            elif in_orig and not in_migr:
                orig_info = orig_symbols[sym_id]
                symbol_diffs.append(SymbolDiff(
                    symbol_id=sym_id,
                    file=fdiff.file,
                    kind=orig_info["kind"],
                    change_kind=SymbolChangeKind.DELETED,
                    original_source=orig_info["source"],
                    line_original=orig_info["lineno"],
                ))
            else:
                orig_info = orig_symbols[sym_id]
                migr_info = migr_symbols[sym_id]

                if orig_info["kind"] == SymbolKind.FUNCTION or orig_info["kind"] == SymbolKind.METHOD:
                    sig_changed = orig_info["signature"] != migr_info["signature"]
                    body_changed = orig_info["source"] != migr_info["source"]

                    if sig_changed:
                        symbol_diffs.append(SymbolDiff(
                            symbol_id=sym_id,
                            file=fdiff.file,
                            kind=orig_info["kind"],
                            change_kind=SymbolChangeKind.SIGNATURE_CHANGED,
                            original_source=orig_info["source"],
                            migrated_source=migr_info["source"],
                            line_original=orig_info["lineno"],
                            line_migrated=migr_info["lineno"],
                        ))
                    elif body_changed:
                        symbol_diffs.append(SymbolDiff(
                            symbol_id=sym_id,
                            file=fdiff.file,
                            kind=orig_info["kind"],
                            change_kind=SymbolChangeKind.BODY_CHANGED,
                            original_source=orig_info["source"],
                            migrated_source=migr_info["source"],
                            line_original=orig_info["lineno"],
                            line_migrated=migr_info["lineno"],
                        ))
                elif orig_info["kind"] == SymbolKind.CLASS:
                    body_changed = orig_info["source"] != migr_info["source"]
                    if body_changed:
                        symbol_diffs.append(SymbolDiff(
                            symbol_id=sym_id,
                            file=fdiff.file,
                            kind=SymbolKind.CLASS,
                            change_kind=SymbolChangeKind.BODY_CHANGED,
                            original_source=orig_info["source"],
                            migrated_source=migr_info["source"],
                            line_original=orig_info["lineno"],
                            line_migrated=migr_info["lineno"],
                        ))

    return symbol_diffs

