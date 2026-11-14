"""`python -m researchteam` and `python -m researchteam.cli` run the CLI (P5 finding, 2026-11-14).

Before the fix, `python -m researchteam.cli` imported the module, did nothing and exited 0, so a script that used
it silently skipped every step.
"""
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("mod", ["researchteam", "researchteam.cli"])
def test_module_entry_runs_cli(mod):
    r = subprocess.run([sys.executable, "-m", mod, "--help"], cwd=ROOT, capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, r.stderr
    assert "update" in r.stdout  # the real parser printed its sub-commands


def test_module_entry_unknown_command_fails():
    r = subprocess.run([sys.executable, "-m", "researchteam", "no-such-command"], cwd=ROOT, capture_output=True,
                       text=True, timeout=60)
    assert r.returncode != 0
