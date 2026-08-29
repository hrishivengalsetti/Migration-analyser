import pytest
from pathlib import Path
import networkx as nx
from brain.graph_builder import build_graph, save_graph, load_graph

def test_builds_nodes_for_functions(tmp_path: Path):
    code_dir = tmp_path / "code"
    code_dir.mkdir()
    (code_dir / "utils.py").write_text("def helper():\n    pass")

    G = build_graph(code_dir)
    assert G.has_node("utils")
    assert G.has_node("utils.helper")
    assert G.nodes["utils.helper"]["kind"] == "function"
    assert G.nodes["utils.helper"]["file"] == "utils.py"

def test_builds_nodes_for_classes(tmp_path: Path):
    code_dir = tmp_path / "code"
    code_dir.mkdir()
    (code_dir / "models.py").write_text("class User:\n    def get_name(self):\n        pass")

    G = build_graph(code_dir)
    assert G.has_node("models.User")
    assert G.nodes["models.User"]["kind"] == "class"
    assert G.has_node("models.User.get_name")
    assert G.nodes["models.User.get_name"]["kind"] == "method"

def test_import_edge_from_import_statement(tmp_path: Path):
    code_dir = tmp_path / "code"
    code_dir.mkdir()
    (code_dir / "pkg.py").write_text("")
    (code_dir / "main.py").write_text("import pkg")

    G = build_graph(code_dir)
    assert G.has_edge("main", "pkg")
    assert G.edges["main", "pkg"]["kind"] == "imports"

def test_import_edge_from_from_import(tmp_path: Path):
    code_dir = tmp_path / "code"
    code_dir.mkdir()
    (code_dir / "utils.py").write_text("def helper():\n    pass")
    (code_dir / "main.py").write_text("from utils import helper")

    G = build_graph(code_dir)
    assert G.has_edge("main", "utils.helper")
    assert G.edges["main", "utils.helper"]["kind"] == "imports"

def test_call_edge_for_known_function(tmp_path: Path):
    code_dir = tmp_path / "code"
    code_dir.mkdir()
    (code_dir / "utils.py").write_text("def helper():\n    pass")
    (code_dir / "main.py").write_text("from utils import helper\ndef run():\n    helper()")

    G = build_graph(code_dir)
    assert G.has_edge("main.run", "utils.helper")
    assert G.edges["main.run", "utils.helper"]["kind"] == "calls"

def test_call_chain_dependency_structure(tmp_path: Path):
    code_dir = tmp_path / "code"
    code_dir.mkdir()
    (code_dir / "chain.py").write_text("""
def baz():
    pass

def bar():
    baz()

def foo():
    bar()
""")

    G = build_graph(code_dir)
    assert G.has_edge("chain.foo", "chain.bar")
    assert G.has_edge("chain.bar", "chain.baz")
    
    # Verify nx.ancestors finds callers of baz
    ancestors = nx.ancestors(G, "chain.baz")
    assert "chain.bar" in ancestors
    assert "chain.foo" in ancestors

def test_ignores_unknown_calls(tmp_path: Path):
    code_dir = tmp_path / "code"
    code_dir.mkdir()
    (code_dir / "main.py").write_text("def run():\n    unknown_function()\n    print('hello')")

    G = build_graph(code_dir)
    assert G.has_node("main.run")
    assert G.out_degree("main.run") == 0

def test_graph_serialization_roundtrip(tmp_path: Path):
    code_dir = tmp_path / "code"
    code_dir.mkdir()
    (code_dir / "mod.py").write_text("def func():\n    pass")

    G = build_graph(code_dir)
    file_path = tmp_path / "graph.json"
    save_graph(G, file_path)

    loaded_G = load_graph(file_path)
    assert set(G.nodes) == set(loaded_G.nodes)
    assert set(G.edges) == set(loaded_G.edges)

def test_ignores_pycache(tmp_path: Path):
    code_dir = tmp_path / "code"
    code_dir.mkdir()
    pycache = code_dir / "__pycache__"
    pycache.mkdir()
    (pycache / "cached.py").write_text("def cached_func(): pass")
    (code_dir / "valid.py").write_text("def valid_func(): pass")

    G = build_graph(code_dir)
    assert G.has_node("valid.valid_func")
    assert not G.has_node("cached.cached_func")
