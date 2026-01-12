#!/usr/bin/env python3
"""
Screenshot Capture Script for PyAurora4X

This script captures a screenshot of the PyAurora4X UI in SVG format.
It can be run manually or as part of a CI/CD workflow.

Usage:
    python capture_screenshot.py [--output OUTPUT_PATH] [--wait SECONDS]

Options:
    --output    Path to save the screenshot (default: screenshot.svg)
    --wait      Seconds to wait before capturing (default: 3)
    --help      Show this help message
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from pyaurora4x.ui.main_app import PyAurora4XApp


def capture_screenshot_sync(output_path: str, wait_seconds: float = 3.0):
    """
    Capture a screenshot of the application in SVG format using test mode.
    
    Args:
        output_path: Path where the screenshot will be saved
        wait_seconds: Seconds to wait for UI to fully render before capture
    """
    import asyncio
    
    print(f"Initializing PyAurora4X for screenshot capture...")
    
    # Create the application with a new game
    # Use minimal settings for quick initialization
    app = PyAurora4XApp(
        new_game_systems=2,  # Minimal number of systems for quick load
        new_game_empires=2,  # Minimal empires
    )
    
    async def run_capture():
        """Async function to run the capture."""
        try:
            # Use run_test which works in headless environments (CI/CD)
            # Use a larger terminal size for better screenshot quality
            async with app.run_test(headless=True, size=(120, 40)) as pilot:
                # Wait for the application to be fully initialized and rendered
                print(f"Waiting {wait_seconds} seconds for UI to fully render...")
                await pilot.pause(wait_seconds)
                
                # Capture the screenshot using Textual's export_screenshot
                print(f"Capturing screenshot to {output_path}...")
                svg_content = app.export_screenshot(title="PyAurora4X Game Interface")
                
                # Write to file
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(svg_content)
                
                print(f"✓ Screenshot successfully saved to {output_path}")
                return True
                
        except Exception as e:
            print(f"✗ Error during capture: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    try:
        # Run the async capture function
        return asyncio.run(run_capture())
        
    except Exception as e:
        print(f"✗ Error capturing screenshot: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main entry point for screenshot capture."""
    parser = argparse.ArgumentParser(
        description="Capture a screenshot of PyAurora4X UI in SVG format"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="screenshot.svg",
        help="Path to save the screenshot (default: screenshot.svg)"
    )
    parser.add_argument(
        "--wait",
        type=float,
        default=3.0,
        help="Seconds to wait before capturing (default: 3.0)"
    )
    
    args = parser.parse_args()
    
    # Convert to absolute path
    output_path = Path(args.output).resolve()
    
    print("=" * 60)
    print("PyAurora4X Screenshot Capture Tool")
    print("=" * 60)
    print(f"Output: {output_path}")
    print(f"Wait time: {args.wait} seconds")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("=" * 60)
    print()
    
    try:
        # Run the screenshot capture
        success = capture_screenshot_sync(str(output_path), args.wait)
        
        if success:
            # Verify the file was created and has content
            if output_path.exists() and output_path.stat().st_size > 0:
                size_kb = output_path.stat().st_size / 1024
                print()
                print("=" * 60)
                print(f"✓ Screenshot capture completed successfully!")
                print(f"  File: {output_path}")
                print(f"  Size: {size_kb:.2f} KB")
                print("=" * 60)
                return 0
            else:
                print()
                print("=" * 60)
                print(f"✗ Screenshot file was not created or is empty")
                print("=" * 60)
                return 1
        else:
            print()
            print("=" * 60)
            print("✗ Screenshot capture did not complete")
            print("=" * 60)
            return 1
            
    except KeyboardInterrupt:
        print()
        print("=" * 60)
        print("Screenshot capture interrupted by user")
        print("=" * 60)
        return 130
    except Exception as e:
        print()
        print("=" * 60)
        print(f"✗ Fatal error: {e}")
        print("=" * 60)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
