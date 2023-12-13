# Copyright (c) Meta Platforms, Inc. and affiliates.

"""
Helpers for duration and times
"""

from dateutil.relativedelta import relativedelta


def duration_to_human_str(sec: int, *, terse: bool = False) -> str:
    """
    Convert a span of time into a simple human string.

    Examples:

      15 -> 15s
    """

    delta = relativedelta(seconds=sec)

    if delta.years > 0:
        return "More than a year"

    parts: list[str] = []

    for label, val in [
        (" months", delta.months),
        (" days", delta.days),
        (" hours", delta.hours),
        (" minutes", delta.minutes),
        (" seconds", delta.seconds),
    ]:
        if terse:
            label = label[1]
        elif val == 1:
            label = label[:-1]
        final = bool(parts)
        if val > 0:
            parts.append(f"{val}{label}")
        if final:
            break

    return " ".join(parts)
