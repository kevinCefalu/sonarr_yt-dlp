"""
Simple working test file for the sonarr_yt-dlp application.

This test file can be run immediately and demonstrates basic functionality.
"""
import sys
from pathlib import Path
from unittest.mock import Mock

# Add the app/src directory to Python path
project_root = Path(__file__).parent.parent
app_src_dir = project_root / 'app' / 'src'
sys.path.insert(0, str(app_src_dir))


def test_imports():
    """Test that we can import our modules."""
    try:
        from models import Series, Episode
        from utils.text_utils import escape_title_for_search
        from utils.date_utils import apply_time_offset
        print("✓ All imports successful")
        return True
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False


def test_text_utils():
    """Test text utility functions."""
    try:
        from utils.text_utils import escape_title_for_search

        # Test basic escaping
        result = escape_title_for_search("Test Episode")
        assert "TEST" in result
        assert "EPISODE" in result
        print("✓ Text utils working")
        return True

    except Exception as e:
        print(f"✗ Text utils test failed: {e}")
        return False


def test_date_utils():
    """Test date utility functions."""
    try:
        from utils.date_utils import apply_time_offset
        from datetime import datetime

        # Test time offset
        base_date = datetime(2023, 1, 1, 12, 0, 0)
        offset = {'days': 1, 'hours': 2}
        result = apply_time_offset(base_date, offset)

        expected = datetime(2023, 1, 2, 14, 0, 0)
        assert result == expected
        print("✓ Date utils working")
        return True

    except Exception as e:
        print(f"✗ Date utils test failed: {e}")
        return False


def test_models():
    """Test data models."""
    try:
        from models import Series, Episode
        from datetime import datetime

        # Test Series creation
        series = Series(id=1, title='Test Series', path='/test')
        assert series.title == 'Test Series'
        assert series.id == 1

        # Test Episode creation
        episode_data = {
            'id': 123,
            'title': 'Test Episode',
            'seasonNumber': 1,
            'episodeNumber': 5,
            'seriesId': 456,
            'airDateUtc': '2023-01-15T20:00:00Z',
            'monitored': True,
            'hasFile': False
        }

        episode = Episode.from_sonarr_data(episode_data)
        assert episode.title == 'Test Episode'
        assert episode.season_number == 1
        assert episode.episode_number == 5

        print("✓ Models working")
        return True

    except Exception as e:
        print(f"✗ Models test failed: {e}")
        return False


def run_all_tests():
    """Run all tests and report results."""
    print("Running simple tests for sonarr_yt-dlp...")
    print("=" * 50)

    tests = [
        test_imports,
        test_text_utils,
        test_date_utils,
        test_models
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"✗ {test.__name__} failed with exception: {e}")

    print("=" * 50)
    print(f"Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed!")
        return True
    else:
        print("❌ Some tests failed")
        return False


if __name__ == "__main__":
    import sys
    success = run_all_tests()
    sys.exit(0 if success else 1)
