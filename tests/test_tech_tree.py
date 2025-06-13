"""Unit tests for the TechTreeManager."""

import logging

from pyaurora4x.data.tech_tree import TechTreeManager
from pyaurora4x.core.models import Technology
from pyaurora4x.core.enums import TechnologyType


class TestTechTreeManager:
    """Tests for the TechTreeManager."""

    def test_load_default_tree(self):
        """Default tech tree should load from JSON data."""
        manager = TechTreeManager(data_directory="data")

        assert manager.tech_tree_loaded
        assert "basic_propulsion" in manager.technologies

    def test_validate_default_prerequisites(self, caplog):
        """Validation should report any invalid prerequisites."""
        manager = TechTreeManager(data_directory="data")

        with caplog.at_level(logging.ERROR):
            manager._validate_tech_tree()

        # No circular dependencies expected in default tree
        for tech in manager.technologies.values():
            assert not manager._has_circular_dependency(tech.id)

        # Some technologies intentionally reference unknown prerequisites
        assert any("Invalid prerequisite" in r.message for r in caplog.records)

    def test_get_research_path(self):
        """Research path should include all prerequisites in order."""
        manager = TechTreeManager(data_directory="data")

        path = manager.get_research_path("antimatter_drive", set())

        expected = [
            "basic_propulsion",
            "basic_energy",
            "advanced_propulsion",
            "nuclear_power",
            "magnetic_confinement",
            "fusion_power",
            "fusion_drive",
            "particle_physics",
            "antimatter_drive",
        ]

        assert path == expected

    def test_validation_edge_cases(self, caplog):
        """Validation should detect missing and circular prerequisites."""
        manager = TechTreeManager(data_directory="data")
        manager.technologies = {
            "a": Technology(
                id="a",
                name="A",
                description="",
                tech_type=TechnologyType.PHYSICS,
                research_cost=1,
                prerequisites=["b"],
                unlocks=[],
            ),
            "b": Technology(
                id="b",
                name="B",
                description="",
                tech_type=TechnologyType.PHYSICS,
                research_cost=1,
                prerequisites=["a"],
                unlocks=[],
            ),
            "c": Technology(
                id="c",
                name="C",
                description="",
                tech_type=TechnologyType.PHYSICS,
                research_cost=1,
                prerequisites=["missing"],
                unlocks=[],
            ),
        }

        with caplog.at_level(logging.ERROR):
            manager._validate_tech_tree()

        messages = "\n".join(record.message for record in caplog.records)
        assert "Circular dependency detected" in messages
        assert "Invalid prerequisite missing" in messages
