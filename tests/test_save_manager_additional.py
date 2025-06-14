from pathlib import Path

import pyaurora4x.data.save_manager as sm
from pyaurora4x.data.save_manager import SaveManager


def create_manager(tmp_path, backend, monkeypatch):
    if backend == "json":
        monkeypatch.setattr(sm, "TINYDB_AVAILABLE", False)
        monkeypatch.setattr(sm, "DUCKDB_AVAILABLE", False)
        return SaveManager(save_directory=str(tmp_path), use_duckdb=False)
    if backend == "tinydb":
        monkeypatch.setattr(sm, "DUCKDB_AVAILABLE", False)
        monkeypatch.setattr(sm, "TINYDB_AVAILABLE", True)
        return SaveManager(save_directory=str(tmp_path), use_duckdb=False)
    monkeypatch.setattr(sm, "DUCKDB_AVAILABLE", True)
    return SaveManager(save_directory=str(tmp_path), use_duckdb=True)


def test_cleanup_old_saves(tmp_path, monkeypatch):
    for backend in ["json", "tinydb", "duckdb"]:
        manager = create_manager(tmp_path / backend, backend, monkeypatch)
        for i in range(15):
            manager.save_game({"idx": i}, f"save_{i}")
        assert len(manager.list_saves()) == 15
        deleted = manager.cleanup_old_saves(keep_count=10)
        assert deleted == 5
        assert len(manager.list_saves()) == 10


def test_cleanup_all_when_keep_count_zero_or_negative(tmp_path, monkeypatch):
    for backend in ["json", "tinydb", "duckdb"]:
        manager = create_manager(tmp_path / f"zero_{backend}", backend, monkeypatch)
        for i in range(5):
            manager.save_game({"idx": i}, f"save_zero_{i}")
        assert len(manager.list_saves()) == 5
        deleted = manager.cleanup_old_saves(keep_count=0)
        assert deleted == 5
        assert len(manager.list_saves()) == 0

        for i in range(3):
            manager.save_game({"idx": i}, f"save_neg_{i}")
        assert len(manager.list_saves()) == 3
        deleted = manager.cleanup_old_saves(keep_count=-2)
        assert deleted == 3
        assert len(manager.list_saves()) == 0


def test_get_save_info_json_and_tinydb(tmp_path, monkeypatch):
    for backend in ["json", "tinydb"]:
        manager = create_manager(tmp_path / backend, backend, monkeypatch)
        manager.save_game({"val": 1}, "info_test")
        info = manager.get_save_info("info_test")
        assert info["save_name"] == "info_test"
        if backend == "json":
            assert Path(info["file_path"]).exists()
        else:
            assert "file_path" not in info


def test_import_save_missing_file(tmp_path, monkeypatch):
    for backend in ["json", "tinydb", "duckdb"]:
        manager = create_manager(tmp_path / backend, backend, monkeypatch)
        missing_file = tmp_path / f"missing_{backend}.json"
        try:
            manager.import_save(str(missing_file))
            raise AssertionError("Expected FileNotFoundError")
        except FileNotFoundError:
            pass
