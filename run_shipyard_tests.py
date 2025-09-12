#!/usr/bin/env python3
"""
Test runner for PyAurora4X shipyard system.
"""

import sys
import pytest
import subprocess
from pathlib import Path

def run_shipyard_tests():
    """Run all shipyard-related tests with proper configuration."""
    project_root = Path(__file__).parent
    test_file = project_root / "tests" / "test_shipyard_comprehensive.py"
    
    if not test_file.exists():
        print(f"Test file not found: {test_file}")
        return 1
    
    # Run pytest with shipyard tests
    cmd = [
        sys.executable, "-m", "pytest",
        str(test_file),
        "-v",
        "--tb=short",
        "-m", "shipyard or not slow",
        "--durations=10"
    ]
    
    print("Running shipyard tests...")
    print("Command:", " ".join(cmd))
    print()
    
    try:
        result = subprocess.run(cmd, cwd=project_root)
        return result.returncode
    except Exception as e:
        print(f"Error running tests: {e}")
        return 1

def run_quick_validation():
    """Run a quick validation to check import structure."""
    print("Validating test imports...")
    try:
        # Try importing key modules to validate structure
        from pyaurora4x.core.shipyards import Shipyard, Slipway, BuildOrder
        from pyaurora4x.engine.shipyard_manager import ShipyardManager
        print("✓ Core shipyard imports successful")
        
        from pyaurora4x.engine.simulation import GameSimulation
        print("✓ Simulation import successful")
        
        from pyaurora4x.data.save_manager import SaveManager
        print("✓ Save manager import successful")
        
        # Check if UI module exists (may not be implemented yet)
        try:
            from pyaurora4x.ui.widgets.shipyard_panel import ShipyardPanel
            print("✓ UI panel import successful")
        except ImportError:
            print("⚠ UI panel not yet implemented - UI tests will be skipped")
        
        print("\nImport validation completed successfully!")
        return True
        
    except ImportError as e:
        print(f"✗ Import error: {e}")
        print("Please ensure all shipyard modules are properly implemented.")
        return False

if __name__ == "__main__":
    print("PyAurora4X Shipyard Test Runner")
    print("=" * 40)
    
    # First validate imports
    if not run_quick_validation():
        print("\nImport validation failed. Aborting test run.")
        sys.exit(1)
    
    print()
    
    # Run tests
    exit_code = run_shipyard_tests()
    
    if exit_code == 0:
        print("\n✓ All shipyard tests passed!")
    else:
        print(f"\n✗ Tests failed with exit code {exit_code}")
    
    sys.exit(exit_code)
