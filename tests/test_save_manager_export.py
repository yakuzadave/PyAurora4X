import json

import duckdb

import pyaurora4x.data.save_manager as sm
from pyaurora4x.data.save_manager import SaveManager


def _setup_json_manager(tmp_path, monkeypatch):
    monkeypatch.setattr(sm, "TINYDB_AVAILABLE", False)
    monkeypatch.setattr(sm, "DUCKDB_AVAILABLE", False)
    return SaveManager(save_directory=str(tmp_path), use_duckdb=False)


def test_export_import_json(tmp_path, monkeypatch):
    manager = _setup_json_manager(tmp_path, monkeypatch)

    data = {"value": 123}
    manager.save_game(data, "save1")

    export_file = tmp_path / "export.json"
    manager.export_save("save1", str(export_file))
    assert export_file.exists()

    imported_name = manager.import_save(str(export_file), "imported_json")
    loaded = manager.load_game(imported_name)
    assert loaded == data


def test_export_import_duckdb(tmp_path, monkeypatch):
    manager = _setup_json_manager(tmp_path, monkeypatch)

    data = {"value": 321}
    manager.save_game(data, "save1")

    export_file = tmp_path / "export.duckdb"
    manager.export_save("save1", str(export_file))
    assert export_file.exists()

    with duckdb.connect(str(export_file)) as conn:
        row = conn.execute(
            "SELECT game_state FROM exports WHERE export_name = ?",
            ["save1"],
        ).fetchone()
    assert row is not None
    exported_state = json.loads(row[0])
    assert exported_state == data

    json_file = tmp_path / "export_from_duckdb.json"
    with open(json_file, "w") as f:
        json.dump({"game_state": exported_state}, f)

    imported_name = manager.import_save(str(json_file), "imported_duckdb")
    loaded = manager.load_game(imported_name)
    assert loaded == data
