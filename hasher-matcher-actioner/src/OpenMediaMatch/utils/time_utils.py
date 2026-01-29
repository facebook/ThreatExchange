# Copyright (c) Meta Platforms, Inc. and affiliates.

"""
Helpers for duration and times
"""

from dateutil.relativedelta import relativedelta


def duration_to_human_str(sec: float, *, terse: bool = False) -> str:
    """
    Convert a span of time into a simple human string.

    Examples:

      15 -> 15s
    """

    if sec < 0.001:
        return "0 seconds"
    
    if sec < 1:
        ms = sec * 1000
        suffix = "ms" if terse else "milliseconds"
        ms_str = f"{ms:.1f}" if ms < 10 else f"{ms:.0f}" 
        return f"{ms_str} {suffix}"

    delta = relativedelta(microsecond=int(sec))

    if delta.years > 0:
        return "More than a year"

    parts: list[str] = []

    durations = [
        (" months", delta.months),
        (" days", delta.days),
        (" hours", delta.hours),
        (" minutes", delta.minutes),
        (" seconds", delta.seconds),
    ]

    for i, (label, val) in enumerate(durations):
        if terse:
            label = label[1]
        elif val == 1:
            label = label[:-1]
        final = bool(parts)
        if val > 0 or (i == len(durations) - 1 and not final):
            parts.append(f"{val}{label}")
        if final:
            break

    return " ".join(parts)
