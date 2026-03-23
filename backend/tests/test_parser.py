import pytest
from backend.services.parser import (
    parse_bell_char,
    parse_method_file,
    parse_timing_file,
    detect_n_bells,
    separate_rounds_and_changes,
    BELL_CHARS,
)


def test_parse_bell_char_digits():
    assert parse_bell_char("1") == 1
    assert parse_bell_char("9") == 9
    assert parse_bell_char("0") == 10


def test_parse_bell_char_E_T():
    assert parse_bell_char("E") == 11
    assert parse_bell_char("T") == 12


def test_parse_bell_char_all_valid():
    for i, c in enumerate(BELL_CHARS):
        assert parse_bell_char(c) == i + 1


def test_parse_method_file_basic():
    content = "12345678\n21436587\n"
    rows = parse_method_file(content)
    assert len(rows) == 2
    assert rows[0] == [1, 2, 3, 4, 5, 6, 7, 8]
    assert rows[1] == [2, 1, 4, 3, 6, 5, 8, 7]


def test_parse_method_file_empty_lines():
    content = "12345678\n\n21436587\n"
    rows = parse_method_file(content)
    assert len(rows) == 2


def test_parse_method_file_12_bells():
    content = "1234567890ET\n"
    rows = parse_method_file(content)
    assert rows[0] == list(range(1, 13))


def test_parse_timing_file_basic():
    content = "Bell No,Actual Time\n1,10000.0\n2,10200.0\n"
    data = parse_timing_file(content)
    assert len(data) == 2
    assert data[0] == (1, 10000.0)
    assert data[1] == (2, 10200.0)


def test_parse_timing_file_skips_header():
    content = "Bell No,Actual Time\n3,5000.5\n"
    data = parse_timing_file(content)
    assert len(data) == 1
    assert data[0][0] == 3


def test_detect_n_bells():
    rows = [[1, 2, 3, 4, 5, 6, 7, 8], [2, 1, 4, 3, 6, 5, 8, 7]]
    assert detect_n_bells(rows) == 8


def test_detect_n_bells_empty():
    assert detect_n_bells([]) == 0


def test_separate_rounds_and_changes_basic():
    rows = [
        [1, 2, 3, 4],
        [1, 2, 3, 4],
        [2, 1, 4, 3],
        [1, 2, 3, 4],
    ]
    rounds_end, changes_start = separate_rounds_and_changes(rows, 4)
    assert rounds_end == 2
    assert changes_start == 2


def test_separate_rounds_and_changes_all_rounds():
    rows = [[1, 2, 3, 4]] * 5
    rounds_end, changes_start = separate_rounds_and_changes(rows, 4)
    assert rounds_end == 5
