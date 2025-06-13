import asyncio
from pathlib import Path

from pyaurora4x.ui.main_app import PyAurora4XApp


async def autopilot(app: PyAurora4XApp, output: Path) -> None:
    """Capture a screenshot once the UI has rendered and quit."""
    # Give Textual a moment to lay out widgets
    await app.wait_one_tick()
    await app.wait_one_tick()
    svg = app.export_screenshot(title="PyAurora4X UI")
    output.write_text(svg, encoding="utf-8")
    await app.action_quit()


def main() -> None:
    """Run the UI in headless mode and save a screenshot."""
    import argparse

    parser = argparse.ArgumentParser(description="Generate a UI screenshot")
    parser.add_argument(
        "--output",
        default="docs/images/ui_example.svg",
        help="Path where the screenshot SVG will be saved",
    )
    args = parser.parse_args()
    output = Path(args.output)

    async def _auto(app: PyAurora4XApp) -> None:
        await autopilot(app, output)

    app = PyAurora4XApp()
    app.run(headless=True, auto_pilot=_auto)


if __name__ == "__main__":
    main()
