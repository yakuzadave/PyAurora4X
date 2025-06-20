"""Ship Design Panel Widget.

Provides a simple interface for creating ship designs from available
components. This is an early stub implementation and only supports
basic functionality."""

from typing import List, Optional
from textual.widgets import Static, DataTable, Button, Label
from textual.containers import Vertical, Horizontal, Container
from textual.app import ComposeResult

from pyaurora4x.core.models import Empire, ShipDesign, ShipComponent
from pyaurora4x.data.ship_components import ShipComponentManager


class ShipDesignPanel(Static):
    """Widget for managing ship designs."""

    def __init__(self, component_manager: ShipComponentManager, **kwargs):
        super().__init__(**kwargs)
        self.component_manager = component_manager
        self.empire: Optional[Empire] = None
        self.selected_components: List[str] = []

    def compose(self) -> ComposeResult:
        with Container(id="design_container"):
            with Horizontal():
                with Vertical(id="component_list"):
                    yield Label("Components")
                    yield DataTable(id="component_table")
                with Vertical(id="design_controls"):
                    yield Label("Selected Components")
                    yield DataTable(id="selected_table")
                    yield Button("Create Design", id="create_design", variant="primary")

    def on_mount(self) -> None:
        table = self.query_one("#component_table", DataTable)
        table.add_columns("Component", "Type")
        for comp in self.component_manager.components.values():
            table.add_row(comp.name, comp.component_type, key=comp.id)

        sel_table = self.query_one("#selected_table", DataTable)
        sel_table.add_columns("Component", "Type")

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        if event.data_table.id == "component_table":
            comp_id = event.row_key
            if comp_id not in self.selected_components:
                self.selected_components.append(comp_id)
                comp = self.component_manager.get_component(comp_id)
                sel = self.query_one("#selected_table", DataTable)
                sel.add_row(comp.name, comp.component_type, key=comp.id)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "create_design" and self.empire:
            design_id = f"design_{len(self.empire.ship_designs)}"
            design = self.component_manager.create_ship_design(
                design_id,
                design_id.title(),
                ShipDesign.model_fields['ship_type'].default,
                self.selected_components,
            )
            if design:
                self.empire.ship_designs.append(design.id)
                self.selected_components.clear()
                sel = self.query_one("#selected_table", DataTable)
                sel.clear()

