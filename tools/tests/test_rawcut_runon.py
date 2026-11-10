"""rawcut.runons: sound a join slices through that no transcribed word accounts for.

Run from the project root:  python -m pytest tools/tests/test_rawcut_runon.py -q
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import rawcut  # noqa: E402


def audio(loud, secs=10.0):
    """dB per 10 ms: -70 everywhere, -20 inside each (start, end) second range."""
    r = np.full(int(secs * 100), -70.0)
    for a, b in loud:
        r[int(a * 100): int(b * 100)] = -20.0
    return r


def test_number_read_aloud_is_flagged():
    # "$6.72." is timed 2.00-2.04 but he speaks until 4.0; the cut lands at 3.04, mid-speech.
    words = [["costs", 1.5, 1.95], ["$6.72.", 2.0, 2.04], ["Next", 6.0, 6.3]]
    got = rawcut.runons(audio([(1.5, 4.0), (6.0, 6.3)]), words, [[0.0, 3.04], [5.9, 10.0]])
    assert [(g["join"], g["side"]) for g in got] == [(0, "out")]
    assert 0.9 <= got[0]["secs"] <= 1.0


def test_clean_pause_is_quiet():
    words = [["done.", 1.5, 2.0], ["Next", 6.0, 6.3]]
    assert rawcut.runons(audio([(1.5, 2.0), (6.0, 6.3)]), words, [[0.0, 2.1], [5.9, 10.0]]) == []


def test_dropped_retake_covers_its_own_sound():
    # He restarts with no pause: the cut lands in speech, but dropped words account for all of it.
    words = [["done.", 1.5, 2.0], ["and", 2.0, 2.3], ["uh", 2.3, 2.9], ["and", 3.0, 3.4], ["Next", 3.4, 3.8]]
    assert rawcut.runons(audio([(1.5, 3.8)]), words, [[0.0, 2.0], [3.0, 10.0]]) == []


def test_word_already_under_way_at_the_resume():
    # The next word is timed from 6.0 but its sound starts at 5.4; the keep resumes at 5.9.
    words = [["done.", 1.5, 2.0], ["Seventeen", 6.0, 6.5]]
    got = rawcut.runons(audio([(1.5, 2.0), (5.4, 6.5)]), words, [[0.0, 2.1], [5.9, 10.0]])
    assert [(g["join"], g["side"]) for g in got] == [(0, "in")]


def test_short_blip_is_ignored():
    words = [["done.", 1.5, 2.0], ["Next", 6.0, 6.3]]
    assert rawcut.runons(audio([(1.5, 2.0), (2.1, 2.2), (6.0, 6.3)]), words, [[0.0, 2.1], [5.9, 10.0]]) == []
