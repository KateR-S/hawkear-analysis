BELL_CHARS = "1234567890ET"  # index+1 = bell number


def parse_bell_char(c: str) -> int:
    """Convert character to bell number. '0'->10, 'E'->11, 'T'->12."""
    idx = BELL_CHARS.index(c.upper())
    return idx + 1


def parse_method_file(content: str) -> list[list[int]]:
    """Parse txt file: each line is a row, return list of bell orderings as ints."""
    rows = []
    for line in content.splitlines():
        line = line.strip()
        if not line:
            continue
        row = [parse_bell_char(c) for c in line]
        if row:
            rows.append(row)
    return rows


def parse_timing_file(content: str) -> list[tuple[int, float]]:
    """Parse csv: skip header 'Bell No,Actual Time', return (bell_number, time_ms) tuples."""
    results = []
    lines = content.splitlines()
    for line in lines:
        line = line.strip()
        if not line or line.lower().startswith("bell"):
            continue
        parts = line.split(",")
        if len(parts) < 2:
            continue
        try:
            bell = parse_bell_char(parts[0].strip())
            time_ms = float(parts[1].strip())
            results.append((bell, time_ms))
        except (ValueError, IndexError):
            continue
    return results


def detect_n_bells(rows: list[list[int]]) -> int:
    """Return number of bells from the first row."""
    if not rows:
        return 0
    return len(rows[0])


def separate_rounds_and_changes(method_rows: list[list[int]], n_bells: int) -> tuple[int, int]:
    """
    Returns (rounds_end_index, changes_start_index).
    Rounds row = bells in order 1..n_bells.
    Find where sequence first deviates from rounds.
    """
    rounds_row = list(range(1, n_bells + 1))
    rounds_end = 0
    for i, row in enumerate(method_rows):
        if row == rounds_row:
            rounds_end = i + 1
        else:
            break
    return rounds_end, rounds_end
