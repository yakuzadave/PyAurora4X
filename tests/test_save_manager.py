from pathlib import Path


import pyaurora4x.data.save_manager as sm
from pyaurora4x.data.save_manager import SaveManager


def _run_cycle(manager: SaveManager, save_name: str):
    data = {"value": 42}
    path = manager.save_game(data, save_name)
    assert Path(path).exists()

    saves = manager.list_saves()
    assert any(s["save_name"] == save_name for s in saves)

    loaded = manager.load_game(save_name)
    assert loaded == data

    assert manager.delete_save(save_name)
    assert not manager.list_saves()


def test_json_backend(tmp_path, monkeypatch):
    monkeypatch.setattr(sm, "TINYDB_AVAILABLE", False)
    monkeypatch.setattr(sm, "DUCKDB_AVAILABLE", False)
    manager = SaveManager(save_directory=str(tmp_path), use_duckdb=False)
    assert not manager.use_duckdb
    assert not manager.use_tinydb
    _run_cycle(manager, "json_save")


def test_tinydb_backend(tmp_path):
    manager = SaveManager(save_directory=str(tmp_path), use_duckdb=False)
    assert manager.use_tinydb
    _run_cycle(manager, "tinydb_save")


def test_duckdb_backend(tmp_path):
    manager = SaveManager(save_directory=str(tmp_path), use_duckdb=True)
    assert manager.use_duckdb
    _run_cycle(manager, "duckdb_save")


def test_list_and_load_specific_save(tmp_path):
    manager = SaveManager(save_directory=str(tmp_path), use_duckdb=False)

    data1 = {"value": 1}
    data2 = {"value": 2}
    manager.save_game(data1, "first")
    manager.save_game(data2, "second")

    saves = manager.list_saves()
    names = {s["save_name"] for s in saves}
    assert {"first", "second"} <= names

    loaded = manager.load_game("second")
    assert loaded == data2


def test_environment_override(tmp_path, monkeypatch):
    env_path = tmp_path / "env_saves"
    monkeypatch.setenv("PYAURORA_SAVE_DIR", str(env_path))
    manager = SaveManager()
    assert manager.save_directory == env_path
    _run_cycle(manager, "env_save")
