"""
Save/Load Manager for PyAurora 4X

Handles game state serialization and persistence using DuckDB, TinyDB or JSON.
"""

import json
import os
from typing import Any, Dict, List, Optional
from datetime import datetime
from enum import Enum
from pathlib import Path
import logging

try:
    import duckdb

    DUCKDB_AVAILABLE = True
except ImportError:  # pragma: no cover - optional dependency
    DUCKDB_AVAILABLE = False
    logging.warning("DuckDB not available - using TinyDB/JSON for saves")

try:
    from tinydb import TinyDB, Query

    TINYDB_AVAILABLE = True
except ImportError:
    TINYDB_AVAILABLE = False
    logging.warning("TinyDB not available - using JSON fallback for saves")

logger = logging.getLogger(__name__)


class SaveManager:
    """
    Manages game save and load operations.

    Uses DuckDB if available, falling back to TinyDB or JSON files.
    Provides versioning and metadata for saved games.
    """

    def __init__(
        self, save_directory: str = "saves", *, use_duckdb: Optional[bool] = None
    ):
        """
        Initialize the save manager.

        Args:
            save_directory: Directory to store save files
            use_duckdb: Force use of DuckDB if True or disable if False. If None,
                uses DuckDB when available.
        """
        self.save_directory = Path(save_directory)
        self.save_directory.mkdir(exist_ok=True)

        # Determine which backend to use
        if use_duckdb is None:
            self.use_duckdb = DUCKDB_AVAILABLE
        else:
            self.use_duckdb = bool(use_duckdb) and DUCKDB_AVAILABLE

        self.use_tinydb = (not self.use_duckdb) and TINYDB_AVAILABLE

        self.duckdb_path = self.save_directory / "saves.duckdb"
        self.saves_db_path = self.save_directory / "saves.db"

        if self.use_duckdb:
            logger.info("Using DuckDB for save management")
        elif self.use_tinydb:
            logger.info("Using TinyDB for save management")
        else:
            logger.info("Using JSON files for save management")

    def save_game(self, game_state: Dict[str, Any], save_name: str) -> str:
        """
        Save a game state.

        Args:
            game_state: Complete game state dictionary
            save_name: Name for the save file

        Returns:
            Path to the saved file
        """
        # Prepare save metadata
        save_metadata = {
            "save_name": save_name,
            "save_date": datetime.now().isoformat(),
            "game_version": "0.1.0",
            "save_format_version": "1.0",
        }

        # Create complete save data
        save_data = {"metadata": save_metadata, "game_state": game_state}

        if self.use_duckdb:
            return self._save_with_duckdb(save_data, save_name)
        if self.use_tinydb:
            return self._save_with_tinydb(save_data, save_name)
        return self._save_with_json(save_data, save_name)

    def _save_with_tinydb(self, save_data: Dict[str, Any], save_name: str) -> str:
        """Save using TinyDB."""
        try:
            with TinyDB(self.saves_db_path) as db:
                saves_table = db.table("saves")

                # Remove existing save with same name
                SaveQuery = Query()
                saves_table.remove(SaveQuery.metadata.save_name == save_name)

                # Insert new save
                saves_table.insert(self._convert_keys_to_strings(save_data))

            logger.info(f"Game saved to TinyDB: {save_name}")
            return str(self.saves_db_path)

        except Exception as e:
            logger.error(f"Error saving with TinyDB: {e}")
            # Fallback to JSON
            return self._save_with_json(save_data, save_name)

    def _save_with_duckdb(self, save_data: Dict[str, Any], save_name: str) -> str:
        """Save using DuckDB."""
        try:
            with duckdb.connect(str(self.duckdb_path)) as conn:
                conn.execute(
                    "CREATE TABLE IF NOT EXISTS saves ("
                    "save_name TEXT, save_date TEXT, game_version TEXT, "
                    "save_format_version TEXT, game_state JSON)"
                )
                conn.execute("DELETE FROM saves WHERE save_name = ?", [save_name])
                meta = save_data["metadata"]
                game_json = json.dumps(
                    self._convert_keys_to_strings(save_data["game_state"]),
                    default=self._json_serializer,
                )
                conn.execute(
                    "INSERT INTO saves VALUES (?, ?, ?, ?, ?)",
                    [
                        meta["save_name"],
                        meta["save_date"],
                        meta["game_version"],
                        meta["save_format_version"],
                        game_json,
                    ],
                )
            logger.info(f"Game saved to DuckDB: {save_name}")
            return str(self.duckdb_path)
        except Exception as e:  # pragma: no cover - runtime safety
            logger.error(f"Error saving with DuckDB: {e}")
            if self.use_tinydb:
                return self._save_with_tinydb(save_data, save_name)
            return self._save_with_json(save_data, save_name)

    def _save_with_json(self, save_data: Dict[str, Any], save_name: str) -> str:
        """Save using JSON files."""
        save_file = self.save_directory / f"{save_name}.json"

        try:
            with open(save_file, "w") as f:
                json.dump(
                    self._convert_keys_to_strings(save_data),
                    f,
                    indent=2,
                    default=self._json_serializer,
                )

            logger.info(f"Game saved to JSON: {save_file}")
            return str(save_file)

        except Exception as e:
            logger.error(f"Error saving to JSON: {e}")
            raise

    def load_game(self, save_identifier: str) -> Dict[str, Any]:
        """
        Load a game state.

        Args:
            save_identifier: Save name or file path

        Returns:
            Game state dictionary
        """
        if self.use_duckdb:
            try:
                return self._load_with_duckdb(save_identifier)
            except Exception as e:  # pragma: no cover - runtime safety
                logger.warning(f"DuckDB load failed, trying TinyDB/JSON: {e}")

        if self.use_tinydb:
            try:
                return self._load_with_tinydb(save_identifier)
            except Exception as e:  # pragma: no cover - runtime safety
                logger.warning(f"TinyDB load failed, trying JSON: {e}")

        return self._load_with_json(save_identifier)

    def _load_with_tinydb(self, save_name: str) -> Dict[str, Any]:
        """Load using TinyDB."""
        with TinyDB(self.saves_db_path) as db:
            saves_table = db.table("saves")
            SaveQuery = Query()

            save_records = saves_table.search(SaveQuery.metadata.save_name == save_name)

            if not save_records:
                raise FileNotFoundError(f"Save '{save_name}' not found in database")

            # Get the most recent save if multiple exist
            save_data = save_records[-1]

            logger.info(f"Game loaded from TinyDB: {save_name}")
            return save_data["game_state"]

    def _load_with_duckdb(self, save_name: str) -> Dict[str, Any]:
        """Load using DuckDB."""
        with duckdb.connect(str(self.duckdb_path)) as conn:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS saves ("
                "save_name TEXT, save_date TEXT, game_version TEXT, "
                "save_format_version TEXT, game_state JSON)"
            )
            row = conn.execute(
                "SELECT game_state FROM saves WHERE save_name = ? ORDER BY save_date DESC LIMIT 1",
                [save_name],
            ).fetchone()
        if not row:
            raise FileNotFoundError(f"Save '{save_name}' not found in database")
        logger.info(f"Game loaded from DuckDB: {save_name}")
        return json.loads(row[0])

    def _load_with_json(self, save_identifier: str) -> Dict[str, Any]:
        """Load using JSON files."""
        # Try as direct file path first
        save_file = Path(save_identifier)

        # If not a valid file, try as save name
        if not save_file.exists():
            save_file = self.save_directory / f"{save_identifier}.json"

        if not save_file.exists():
            raise FileNotFoundError(f"Save file not found: {save_identifier}")

        try:
            with open(save_file, "r") as f:
                save_data = json.load(f)

            logger.info(f"Game loaded from JSON: {save_file}")

            # Handle both new format (with metadata) and old format (direct game state)
            if "game_state" in save_data:
                return save_data["game_state"]
            else:
                return save_data

        except Exception as e:
            logger.error(f"Error loading from JSON: {e}")
            raise

    def list_saves(self) -> List[Dict[str, Any]]:
        """
        List all available saves with metadata.

        Returns:
            List of save metadata dictionaries
        """
        saves = []

        if self.use_duckdb and self.duckdb_path.exists():
            saves.extend(self._list_duckdb_saves())

        if self.use_tinydb and self.saves_db_path.exists():
            saves.extend(self._list_tinydb_saves())

        saves.extend(self._list_json_saves())

        # Sort by save date (newest first)
        saves.sort(key=lambda x: x.get("save_date", ""), reverse=True)

        return saves

    def _list_tinydb_saves(self) -> List[Dict[str, Any]]:
        """List saves from TinyDB."""
        saves = []

        try:
            with TinyDB(self.saves_db_path) as db:
                saves_table = db.table("saves")

                for record in saves_table.all():
                    if "metadata" in record:
                        saves.append(record["metadata"])

        except Exception as e:
            logger.error(f"Error listing TinyDB saves: {e}")

        return saves

    def _list_duckdb_saves(self) -> List[Dict[str, Any]]:
        """List saves stored in DuckDB."""
        saves = []
        try:
            with duckdb.connect(str(self.duckdb_path)) as conn:
                conn.execute(
                    "CREATE TABLE IF NOT EXISTS saves ("
                    "save_name TEXT, save_date TEXT, game_version TEXT, "
                    "save_format_version TEXT, game_state JSON)"
                )
                rows = conn.execute(
                    "SELECT save_name, save_date, game_version, save_format_version FROM saves"
                ).fetchall()
            for row in rows:
                saves.append(
                    {
                        "save_name": row[0],
                        "save_date": row[1],
                        "game_version": row[2],
                        "save_format_version": row[3],
                    }
                )
        except Exception as e:  # pragma: no cover - runtime safety
            logger.error(f"Error listing DuckDB saves: {e}")

        return saves

    def _list_json_saves(self) -> List[Dict[str, Any]]:
        """List saves from JSON files."""
        saves = []

        for save_file in self.save_directory.glob("*.json"):
            try:
                with open(save_file, "r") as f:
                    save_data = json.load(f)

                if "metadata" in save_data:
                    metadata = save_data["metadata"]
                else:
                    # Create metadata for old format saves
                    metadata = {
                        "save_name": save_file.stem,
                        "save_date": datetime.fromtimestamp(
                            save_file.stat().st_mtime
                        ).isoformat(),
                        "game_version": "unknown",
                        "save_format_version": "legacy",
                    }

                metadata["file_path"] = str(save_file)
                saves.append(metadata)

            except Exception as e:
                logger.warning(f"Error reading save file {save_file}: {e}")

        return saves

    def delete_save(self, save_identifier: str) -> bool:
        """
        Delete a saved game.

        Args:
            save_identifier: Save name or file path

        Returns:
            True if deletion was successful
        """
        success = False

        if self.use_duckdb:
            success = self._delete_from_duckdb(save_identifier) or success

        if self.use_tinydb:
            success = self._delete_from_tinydb(save_identifier) or success

        success = self._delete_json_save(save_identifier) or success

        return success

    def _delete_from_tinydb(self, save_name: str) -> bool:
        """Delete save from TinyDB."""
        try:
            with TinyDB(self.saves_db_path) as db:
                saves_table = db.table("saves")
                SaveQuery = Query()

                removed = saves_table.remove(SaveQuery.metadata.save_name == save_name)

                if removed:
                    logger.info(f"Deleted save from TinyDB: {save_name}")
                    return True

        except Exception as e:
            logger.error(f"Error deleting from TinyDB: {e}")

        return False

    def _delete_from_duckdb(self, save_name: str) -> bool:
        """Delete save from DuckDB."""
        try:
            with duckdb.connect(str(self.duckdb_path)) as conn:
                conn.execute(
                    "CREATE TABLE IF NOT EXISTS saves ("
                    "save_name TEXT, save_date TEXT, game_version TEXT, "
                    "save_format_version TEXT, game_state JSON)"
                )
                result = conn.execute(
                    "DELETE FROM saves WHERE save_name = ?", [save_name]
                ).rowcount
            if result:
                logger.info(f"Deleted save from DuckDB: {save_name}")
                return True
        except Exception as e:  # pragma: no cover - runtime safety
            logger.error(f"Error deleting from DuckDB: {e}")

        return False

    def _delete_json_save(self, save_identifier: str) -> bool:
        """Delete JSON save file."""
        # Try as direct file path first
        save_file = Path(save_identifier)

        # If not a valid file, try as save name
        if not save_file.exists():
            save_file = self.save_directory / f"{save_identifier}.json"

        if save_file.exists():
            try:
                save_file.unlink()
                logger.info(f"Deleted JSON save: {save_file}")
                return True
            except Exception as e:
                logger.error(f"Error deleting JSON save: {e}")

        return False

    def export_save(self, save_identifier: str, export_path: str) -> str:
        """
        Export a save to a specific location.

        Args:
            save_identifier: Save to export
            export_path: Destination path

        Returns:
            Path to exported file
        """
        game_state = self.load_game(save_identifier)

        # Create export data with metadata
        export_data = {
            "metadata": {
                "export_date": datetime.now().isoformat(),
                "original_save": save_identifier,
                "game_version": "0.1.0",
                "save_format_version": "1.0",
            },
            "game_state": game_state,
        }

        export_file = Path(export_path)

        if export_file.suffix == ".duckdb":
            with duckdb.connect(str(export_file)) as conn:
                conn.execute(
                    "CREATE TABLE IF NOT EXISTS exports ("
                    "export_name TEXT, export_date TEXT, game_version TEXT, "
                    "save_format_version TEXT, game_state JSON)"
                )
                data_json = json.dumps(
                    self._convert_keys_to_strings(export_data["game_state"]),
                    default=self._json_serializer,
                )
                conn.execute(
                    "INSERT INTO exports VALUES (?, ?, ?, ?, ?)",
                    [
                        export_data["metadata"]["original_save"],
                        export_data["metadata"]["export_date"],
                        export_data["metadata"]["game_version"],
                        export_data["metadata"]["save_format_version"],
                        data_json,
                    ],
                )
        else:
            with open(export_file, "w") as f:
                json.dump(export_data, f, indent=2, default=self._json_serializer)

        logger.info(f"Save exported to: {export_file}")
        return str(export_file)

    def import_save(self, import_path: str, save_name: Optional[str] = None) -> str:
        """
        Import a save from a file.

        Args:
            import_path: Path to import file
            save_name: Optional custom name for imported save

        Returns:
            Name of imported save
        """
        import_file = Path(import_path)

        if not import_file.exists():
            raise FileNotFoundError(f"Import file not found: {import_path}")

        with open(import_file, "r") as f:
            import_data = json.load(f)

        # Extract game state
        if "game_state" in import_data:
            game_state = import_data["game_state"]
        else:
            game_state = import_data

        # Generate save name if not provided
        if not save_name:
            save_name = f"imported_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Save the imported game
        self.save_game(game_state, save_name)

        logger.info(f"Save imported as: {save_name}")
        return save_name

    def cleanup_old_saves(self, keep_count: int = 10) -> int:
        """
        Clean up old save files, keeping only the most recent ones.

        Args:
            keep_count: Number of saves to keep

        Returns:
            Number of saves deleted
        """
        saves = self.list_saves()

        if len(saves) <= keep_count:
            return 0

        # Delete oldest saves
        saves_to_delete = saves[keep_count:]
        deleted_count = 0

        for save_metadata in saves_to_delete:
            save_name = save_metadata["save_name"]
            if self.delete_save(save_name):
                deleted_count += 1

        logger.info(f"Cleaned up {deleted_count} old saves")
        return deleted_count

    def _json_serializer(self, obj):
        """Custom JSON serializer for complex objects."""
        if isinstance(obj, Enum):
            return obj.value
        elif hasattr(obj, "dict"):
            return obj.dict()
        elif hasattr(obj, "__dict__"):
            return obj.__dict__
        elif isinstance(obj, datetime):
            return obj.isoformat()
        else:
            return str(obj)

    def _convert_keys_to_strings(self, obj: Any) -> Any:
        """Recursively convert dictionary keys to strings for JSON."""
        if isinstance(obj, dict):
            return {str(k): self._convert_keys_to_strings(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [self._convert_keys_to_strings(v) for v in obj]
        return obj

    def get_save_info(self, save_identifier: str) -> Dict[str, Any]:
        """
        Get detailed information about a save.

        Args:
            save_identifier: Save name or file path

        Returns:
            Save information dictionary
        """
        saves = self.list_saves()

        for save_metadata in saves:
            if (
                save_metadata["save_name"] == save_identifier
                or save_metadata.get("file_path") == save_identifier
            ):
                return save_metadata

        raise FileNotFoundError(f"Save not found: {save_identifier}")
