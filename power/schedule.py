"""Fetch the YASNO outage schedule and normalize it to Days keyed by date."""
import json
import urllib.request
from zoneinfo import ZoneInfo

URL = ("https://app.yasno.ua/api/blackout-service/public/shutdowns/"
       "regions/25/dsos/902/planned-outages")
GROUP = "47.1"
KYIV = ZoneInfo("Europe/Kyiv")


class FetchError(Exception):
    """YASNO could not be read or returned something that is not a schedule."""


def fetch_raw(url: str = URL, timeout: int = 20) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "kyiv-power-47-1",
                                               "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            status = getattr(resp, "status", 200)
            body = resp.read()
    except Exception as e:  # network, HTTP error, timeout
        raise FetchError(f"request failed: {e.__class__.__name__}: {e}") from e
    if status != 200:
        raise FetchError(f"HTTP {status}")
    try:
        data = json.loads(body)
    except ValueError as e:
        raise FetchError("response is not JSON") from e
    if not isinstance(data, dict):
        raise FetchError("response JSON is not an object")
    return data


def _kind(slot_type: str):
    if slot_type == "NotPlanned":
        return None
    if slot_type == "Definite":
        return "definite"
    return "possible"


def normalize(raw: dict, group: str = GROUP) -> dict:
    g = raw.get(group)
    if not isinstance(g, dict):
        raise FetchError(f"group {group} missing from response")
    days = {}
    for key in ("today", "tomorrow"):
        d = g.get(key)
        if d is None:
            continue
        if not isinstance(d, dict) or "date" not in d or "status" not in d:
            raise FetchError(f"{key} lacks date/status")
        off = []
        try:
            for s in d.get("slots") or []:
                kind = _kind(s.get("type"))
                if kind:
                    off.append([int(s["start"]), int(s["end"]), kind])
        except (KeyError, TypeError, ValueError, AttributeError) as e:
            raise FetchError(f"{key} has a malformed slot: {e!r}") from e
        off.sort()
        days[str(d["date"])[:10]] = {"status": str(d["status"]), "off": off}
    if not days:
        raise FetchError(f"group {group} has no days")
    return days
