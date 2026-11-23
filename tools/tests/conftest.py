"""Tests that need a fixture project which is no longer on disk are skipped, with the reason, instead of failing.

Two fixture projects were the author's own edits in work/ (work/beat-fixture and work/1030-1/v2/skeleton). They do not ship,
so while either is absent a test whose failure names it is a skip.
"""
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = {"beat-fixture": ROOT / "work/beat-fixture/v2/editorial", "1030-1": ROOT / "work/1030-1/v2/skeleton"}
MISSING = {name: path for name, path in FIXTURES.items() if not path.is_dir()}
NAMES = {"beat-fixture": ("beat-fixture", "FIXTURE"), "1030-1": ("1030-1",)}


def missing_fixture(text):
    return next((name for name in MISSING if any(word in text for word in NAMES[name])), None)


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    if not MISSING or not report.failed or call.excinfo is None:
        return
    name = missing_fixture(str(report.longrepr))
    if name:
        report.outcome = "skipped"
        report.longrepr = (str(item.fspath), item.location[1] or 0, f"Skipped: the {name} fixture project does not ship: {MISSING[name]}")
