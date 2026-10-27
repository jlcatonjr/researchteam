"""Run the literature-library build + integrity gate's bash scenario suite under pytest, so CI gates it."""
import shutil
import subprocess
from pathlib import Path

import pytest

SUITE = Path(__file__).resolve().parents[1] / "scripts" / "tests" / "test_literature_library.sh"


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash not available")
def test_literature_library_suite_passes():
    assert SUITE.exists(), SUITE
    r = subprocess.run(["bash", str(SUITE)], capture_output=True, text=True, timeout=300)
    assert r.returncode == 0, r.stdout[-4000:] + r.stderr[-4000:]
