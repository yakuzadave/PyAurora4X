import json
import duckdb
from pyaurora4x.data.save_manager import SaveManager


def test_export_import_json_and_duckdb(tmp_path):
    """Save a game then export and re-import using both formats."""
    manager = SaveManager(save_directory=str(tmp_path), use_duckdb=False)

    data = {"value": 42}
    manager.save_game(data, "test_save")

    # Export to JSON and re-import
    json_export = tmp_path / "export.json"
    manager.export_save("test_save", str(json_export))
    assert json_export.exists()

    imported_json = manager.import_save(str(json_export), "imported_json")
    assert manager.load_game(imported_json) == data

    # Export to DuckDB and re-import
    duckdb_export = tmp_path / "export.duckdb"
    manager.export_save("test_save", str(duckdb_export))
    assert duckdb_export.exists()

    with duckdb.connect(str(duckdb_export)) as conn:
        row = conn.execute(
            "SELECT game_state FROM exports WHERE export_name = ?",
            ["test_save"],
        ).fetchone()
    assert row is not None
    exported_state = json.loads(row[0])
    assert exported_state == data

    json_from_duckdb = tmp_path / "from_duckdb.json"
    with open(json_from_duckdb, "w") as f:
        json.dump({"game_state": exported_state}, f)

    imported_duckdb = manager.import_save(str(json_from_duckdb), "imported_duckdb")
    assert manager.load_game(imported_duckdb) == data
