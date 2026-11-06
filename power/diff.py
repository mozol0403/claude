"""Compare stored and fetched schedules by calendar date."""


def changes(old: dict, new: dict) -> list:
    """Return [(date, old_day_or_None, new_day)] sorted by date.

    A date seen for the first time is a change only if it already carries outage
    slots; rollover and dropped dates are silent. The caller skips the very first run.
    """
    out = []
    for d in sorted(new):
        if d in old:
            if old[d] != new[d]:
                out.append((d, old[d], new[d]))
        elif new[d]["off"]:
            out.append((d, None, new[d]))
    return out
