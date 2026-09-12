import ast
from pathlib import Path


def test_startup_does_not_call_create_all():
    main = Path("app/main.py").read_text(encoding="utf-8")
    database = Path("app/database.py").read_text(encoding="utf-8")
    assert "create_all" not in main
    assert "create_all" not in database
    assert "init_db" not in main


def test_alembic_initial_revision_exists():
    versions = Path("alembic/versions")
    revisions = list(versions.glob("*.py"))
    assert revisions, "expected at least one Alembic revision"
    tree = ast.parse(revisions[0].read_text(encoding="utf-8"))
    names = {node.name for node in tree.body if isinstance(node, ast.FunctionDef)}
    assert "upgrade" in names
    assert "downgrade" in names
