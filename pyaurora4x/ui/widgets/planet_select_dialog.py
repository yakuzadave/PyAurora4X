from typing import Callable, List

from textual.app import ComposeResult
from textual.widgets import Static, OptionList, Button
from textual.widgets._option_list import Option
from textual.containers import Vertical

from pyaurora4x.core.models import Planet


class PlanetSelectDialog(Static):
    """Modal dialog for selecting a destination planet."""

    def __init__(self, planets: List[Planet], on_select: Callable[[str], None], **kwargs):
        super().__init__(**kwargs)
        self.planets = planets
        self.on_select = on_select

    def compose(self) -> ComposeResult:
        with Vertical(id="planet_select_dialog"):
            yield Static("Select Destination", id="planet_select_title")
            option_list = OptionList(id="planet_options")
            for planet in self.planets:
                option_list.add_option(Option(planet.name, id=planet.id))
            yield option_list
            yield Button("Cancel", id="cancel_planet_select")

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:  # type: ignore[override]
        if self.on_select and event.option.id is not None:
            self.on_select(event.option.id)
        self.remove()

    def on_button_pressed(self, event: Button.Pressed) -> None:  # type: ignore[override]
        if event.button.id == "cancel_planet_select":
            self.remove()
