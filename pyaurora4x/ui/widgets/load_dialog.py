from typing import Callable, List, Dict, Any

from textual.app import ComposeResult
from textual.widgets import Static, OptionList, Button
from textual.widgets._option_list import Option
from textual.containers import Vertical


class LoadGameDialog(Static):
    """Modal dialog to choose a save file to load."""

    def __init__(self, saves: List[Dict[str, Any]], on_select: Callable[[str], None], **kwargs):
        super().__init__(**kwargs)
        self.saves = saves
        self.on_select = on_select

    def compose(self) -> ComposeResult:
        with Vertical(id="load_dialog"):
            yield Static("Select Save to Load", id="load_title")
            option_list = OptionList(id="save_options")
            for meta in self.saves:
                label = f"{meta['save_name']} {meta.get('save_date', '')}".strip()
                option_list.add_option(Option(label, id=meta['save_name']))
            yield option_list
            yield Button("Cancel", id="cancel_load")

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        if self.on_select:
            if event.option.id is not None:
                self.on_select(event.option.id)
        self.remove()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cancel_load":
            self.remove()
