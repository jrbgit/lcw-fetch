#!/usr/bin/env python
"""Simple test runner to check pytest functionality."""

import sys
import subprocess
import os

# Add src to Python path
src_path = os.path.join(os.path.dirname(__file__), 'src')
sys.path.insert(0, src_path)

def run_tests():
    """Run pytest and capture output."""
    try:
        # Try to import pytest first
        import pytest
        print(f"Pytest version: {pytest.__version__}")
        
        # Run a simple test to check if everything works
        result = subprocess.run([
            sys.executable, '-m', 'pytest', 
            '--version'
        ], capture_output=True, text=True, cwd=os.path.dirname(__file__))
        
        print("Return code:", result.returncode)
        print("STDOUT:", result.stdout)
        print("STDERR:", result.stderr)
        
        # Now try running actual tests
        print("\n" + "="*50)
        print("Running actual tests...")
        
        result = subprocess.run([
            sys.executable, '-m', 'pytest', 
            'tests/', '-v', '--tb=short'
        ], capture_output=True, text=True, cwd=os.path.dirname(__file__))
        
        print("Return code:", result.returncode)
        print("STDOUT:", result.stdout)
        print("STDERR:", result.stderr)
        
    except ImportError as e:
        print(f"Failed to import pytest: {e}")
    except Exception as e:
        print(f"Error running tests: {e}")

if __name__ == "__main__":
    run_tests()
