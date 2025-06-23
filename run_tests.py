#!/usr/bin/env python3
"""
Test runner script for the sonarr_yt-dlp application.
"""
import sys
import os
from pathlib import Path

# Add the src directory to Python path
project_root = Path(__file__).parent
src_dir = project_root / 'app' / 'src'
sys.path.insert(0, str(src_dir))

# Also add the app directory for any legacy imports
app_dir = project_root / 'app'
sys.path.insert(0, str(app_dir))

# Set environment variable for config path (for testing)
os.environ.setdefault('CONFIGPATH', str(project_root / 'app' / 'config.yml'))

if __name__ == "__main__":
    # Check if we want to run the simple tests first
    if len(sys.argv) > 1 and sys.argv[1] == '--simple':
        print("Running simple tests...")
        test_file = project_root / 'tests' / 'test_simple.py'
        exit_code = os.system(f'python "{test_file}"')
        sys.exit(exit_code)

    try:
        import pytest
    except ImportError:
        print("Error: pytest is not installed. Please run:")
        print("pip install pytest")
        print("\nAlternatively, run simple tests with:")
        print("python run_tests.py --simple")
        sys.exit(1)

    # Run the tests
    test_files = [
        project_root / 'tests' / 'test_simple.py',
        project_root / 'tests' / 'test_example.py'
    ]

    print(f"Running tests from: {[str(f) for f in test_files]}")
    print(f"Python path includes:")
    print(f"  - {src_dir}")
    print(f"  - {app_dir}")
    print(f"Config path: {os.environ.get('CONFIGPATH')}")
    print("-" * 50)

    # Run pytest with verbose output
    exit_code = pytest.main([
        str(project_root / 'tests'),
        '-v',
        '--tb=short',
        '--no-header',
        '--disable-warnings'
    ])

    sys.exit(exit_code)
