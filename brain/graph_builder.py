import ast
import json
from pathlib import Path
import networkx as nx
from brain.diff_analyzer import _path_to_module_name


def save_graph(G: nx.DiGraph, path: Path) -> None:
    data = nx.node_link_data(G)
    path.write_text(json.dumps(data, indent=2))


def load_graph(path: Path) -> nx.DiGraph:
    data = json.loads(path.read_text())
    return nx.node_link_graph(data)


class _CallVisitor(ast.NodeVisitor):
    def __init__(self):
        self.calls = []

    def visit_Call(self, node: ast.Call):
        if isinstance(node.func, ast.Name):
            self.calls.append(node.func.id)
        elif isinstance(node.func, ast.Attribute):
            self.calls.append(node.func.attr)
        self.generic_visit(node)


def build_graph(codebase_dir: Path) -> nx.DiGraph:
    G = nx.DiGraph()

    py_files = {
        p.relative_to(codebase_dir): p
        for p in codebase_dir.rglob("*.py")
        if not any(part.startswith('.') or part == '__pycache__' for part in p.parts)
    }

    file_asts = {}
    file_modules = {}

    # Pass 1: Node Extraction
    for rel_path, abs_path in py_files.items():
        rel_str = str(rel_path)
        module_name = _path_to_module_name(rel_str)
        file_modules[rel_str] = module_name

        try:
            source = abs_path.read_text(errors='replace')
            tree = ast.parse(source)
            file_asts[rel_str] = (source, tree)
        except SyntaxError:
            continue

        # Add module node
        G.add_node(
            module_name,
            id=module_name,
            kind="module",
            file=rel_str,
            line_start=1
        )

        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                sym_id = f"{module_name}.{node.name}" if module_name else node.name
                G.add_node(
                    sym_id,
                    id=sym_id,
                    kind="function",
                    file=rel_str,
                    line_start=node.lineno
                )
            elif isinstance(node, ast.ClassDef):
                class_id = f"{module_name}.{node.name}" if module_name else node.name
                G.add_node(
                    class_id,
                    id=class_id,
                    kind="class",
                    file=rel_str,
                    line_start=node.lineno
                )
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        method_id = f"{class_id}.{item.name}"
                        G.add_node(
                            method_id,
                            id=method_id,
                            kind="method",
                            file=rel_str,
                            line_start=item.lineno
                        )

    # Pass 2: Edge Extraction (Imports & Calls)
    for rel_str, (source, tree) in file_asts.items():
        module_name = file_modules[rel_str]
        imported_symbols = {}  # local_name -> symbol_id

        # Collect imports and import edges
        for node in tree.body:
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported_mod = alias.name
                    as_name = alias.asname or alias.name
                    imported_symbols[as_name] = imported_mod
                    if G.has_node(imported_mod):
                        G.add_edge(module_name, imported_mod, kind="imports")

            elif isinstance(node, ast.ImportFrom):
                target_mod = node.module or ""
                # Handle relative imports if needed
                if node.level > 0:
                    mod_parts = module_name.split(".")
                    if len(mod_parts) >= node.level:
                        base_parts = mod_parts[:-node.level]
                        if target_mod:
                            base_parts.append(target_mod)
                        target_mod = ".".join(base_parts)

                for alias in node.names:
                    name_in_mod = alias.name
                    local_as = alias.asname or name_in_mod
                    
                    possible_sym_id = f"{target_mod}.{name_in_mod}" if target_mod else name_in_mod
                    possible_mod_id = target_mod

                    if G.has_node(possible_sym_id):
                        imported_symbols[local_as] = possible_sym_id
                        G.add_edge(module_name, possible_sym_id, kind="imports")
                    elif G.has_node(possible_mod_id):
                        imported_symbols[local_as] = f"{possible_mod_id}.{name_in_mod}"
                        G.add_edge(module_name, possible_mod_id, kind="imports")

        # Function/Method Scope Call Resolution
        def process_scope(scope_node, scope_id):
            visitor = _CallVisitor()
            visitor.visit(scope_node)
            for called_name in visitor.calls:
                target_id = None
                # Check imported symbols map
                if called_name in imported_symbols:
                    target_id = imported_symbols[called_name]
                # Check same module functions/classes
                elif G.has_node(f"{module_name}.{called_name}"):
                    target_id = f"{module_name}.{called_name}"

                if target_id and G.has_node(target_id) and target_id != scope_id:
                    G.add_edge(scope_id, target_id, kind="calls")

        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                sym_id = f"{module_name}.{node.name}" if module_name else node.name
                process_scope(node, sym_id)
            elif isinstance(node, ast.ClassDef):
                class_id = f"{module_name}.{node.name}" if module_name else node.name
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        method_id = f"{class_id}.{item.name}"
                        process_scope(item, method_id)

    return G
