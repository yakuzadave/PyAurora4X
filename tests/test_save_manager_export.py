"""Tests for exporting and importing saves."""

import json
import duckdb

from pyaurora4x.data.save_manager import SaveManager


def test_export_import_json(tmp_path):
    """Save a game, export to JSON, then import back."""
    manager = SaveManager(save_directory=str(tmp_path), use_duckdb=False)

    data = {"value": 42}
    manager.save_game(data, "test_save")

    export_file = tmp_path / "export.json"
    manager.export_save("test_save", str(export_file))
    assert export_file.exists()

    imported_name = manager.import_save(str(export_file), "imported_json")
    assert manager.load_game(imported_name) == data


def test_export_import_duckdb(tmp_path):
    """Save a game, export to DuckDB, then import back."""
    manager = SaveManager(save_directory=str(tmp_path), use_duckdb=False)

    data = {"value": 42}
    manager.save_game(data, "test_save")

    duckdb_file = tmp_path / "export.duckdb"
    manager.export_save("test_save", str(duckdb_file))
    assert duckdb_file.exists()

    with duckdb.connect(str(duckdb_file)) as conn:
        row = conn.execute(
            "SELECT game_state FROM exports WHERE export_name = ?",
            ["test_save"],
        ).fetchone()

    assert row is not None
    exported_state = json.loads(row[0])

    json_file = tmp_path / "from_duckdb.json"
    json_file.write_text(json.dumps({"game_state": exported_state}))

    imported_name = manager.import_save(str(json_file), "imported_duckdb")
    assert manager.load_game(imported_name) == data

