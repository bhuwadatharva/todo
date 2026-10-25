"""
Interactive Test Runner for 60-Minute Challenge.
Runs pytest and formats results with clean console outputs.
"""
import sys
import os
import subprocess
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))


def run_challenge_tests():
    print("=" * 70)
    print("  PYTHON AI ENGINEER – AUTONOMOUS AGENTS – TEST RUNNER")
    print("=" * 70)
    print("\nRunning pytest on test suite...")

    cmd = [sys.executable, "-m", "pytest", "tests/test_agent.py", "-v", "--tb=short"]
    result = subprocess.run(cmd, cwd=str(PROJECT_ROOT))

    print("\n" + "=" * 70)
    if result.returncode == 0:
        print("  >>> ALL TESTS PASSED SUCCESSFULLY! (100% GREEN)")
    else:
        print("  >>> SOME TESTS FAILED. PLEASE REVIEW LOGS ABOVE.")
    print("=" * 70)

    # List output directory
    output_dir = PROJECT_ROOT / "output"
    if output_dir.exists():
        files = list(output_dir.glob("*.docx"))
        print(f"\nGenerated Word Documents in '{output_dir}':")
        for f in files:
            size_kb = round(f.stat().st_size / 1024, 1)
            print(f"  - {f.name} ({size_kb} KB)")
    print()
    return result.returncode


if __name__ == "__main__":
    code = run_challenge_tests()
    sys.exit(code)
