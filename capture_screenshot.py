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
import asyncio
from pathlib import Path
from datetime import datetime

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from pyaurora4x.ui.main_app import PyAurora4XApp


async def capture_screenshot_async(output_path: str, wait_seconds: int = 3):
    """
    Capture a screenshot of the application in SVG format.
    
    Args:
        output_path: Path where the screenshot will be saved
        wait_seconds: Seconds to wait for UI to fully render before capture
    """
    print(f"Initializing PyAurora4X for screenshot capture...")
    
    # Create the application with a new game
    # Use minimal settings for quick initialization
    app = PyAurora4XApp(
        new_game_systems=2,  # Minimal number of systems for quick load
        new_game_empires=2,  # Minimal empires
    )
    
    # Flag to track if screenshot was saved
    screenshot_saved = False
    screenshot_error = None
    
    async def take_screenshot():
        """Internal function to take the screenshot after app is ready."""
        nonlocal screenshot_saved, screenshot_error
        try:
            # Wait for the application to be fully initialized and rendered
            print(f"Waiting {wait_seconds} seconds for UI to fully render...")
            await asyncio.sleep(wait_seconds)
            
            # Save the screenshot using Textual's export_svg
            print(f"Capturing screenshot to {output_path}...")
            svg_content = app.export_screenshot()
            
            # Write to file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(svg_content)
            
            print(f"✓ Screenshot successfully saved to {output_path}")
            screenshot_saved = True
            
            # Exit the app after capturing
            app.exit()
            
        except Exception as e:
            screenshot_error = str(e)
            print(f"✗ Error capturing screenshot: {e}")
            app.exit(1)
    
    # Schedule screenshot capture after app starts
    app.set_timer(0.1, take_screenshot)
    
    # Run the application
    try:
        app.run()
    except Exception as e:
        print(f"✗ Error running application: {e}")
        return False
    
    # Check if screenshot was successful
    if screenshot_error:
        raise RuntimeError(f"Screenshot capture failed: {screenshot_error}")
    
    return screenshot_saved


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
        type=int,
        default=3,
        help="Seconds to wait before capturing (default: 3)"
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
        # Run the async screenshot capture
        success = asyncio.run(capture_screenshot_async(str(output_path), args.wait))
        
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
