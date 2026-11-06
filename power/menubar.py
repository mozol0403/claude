"""SwiftBar output for the menu bar. The Mac never sends notifications."""
import json
import os
import urllib.request
from datetime import datetime, timedelta

from power.schedule import KYIV, FetchError, fetch_raw, normalize
from power.text import day_lines, hhmm

REPO = "mozol0403/claude"
WORKFLOW = "check.yml"
CLOUD_STALE = timedelta(hours=1)
CACHE = os.path.expanduser("~/Library/Caches/kyiv-power-47-1.json")


def _outages(days: dict, now: datetime) -> list:
    """Definite outages today+tomorrow as merged [start, end] minutes from today 00:00."""
    today = now.date()
    spans = []
    for offset in (0, 1):
        day = days.get((today + timedelta(days=offset)).isoformat())
        for s, e, kind in (day or {}).get("off", []):
            if kind == "definite":
                spans.append([s + 1440 * offset, e + 1440 * offset])
    spans.sort()
    merged = []
    for s, e in spans:
        if merged and s <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], e)
        else:
            merged.append([s, e])
    return merged


def _clock(m: int) -> str:
    return hhmm(m if m <= 1440 else m - 1440)


def title(days: dict, now: datetime) -> str:
    nowm = now.hour * 60 + now.minute
    for s, e in _outages(days, now):
        if s <= nowm < e:
            return f"🕯 до {_clock(e)}"
        if s > nowm:
            return f"⚡ до {hhmm(s % 1440)}"
    today = days.get(now.date().isoformat())
    if today and today["status"] == "EmergencyShutdowns":
        return "⚠️ аварійні"
    return "⚡"


def last_cloud_success(repo: str = REPO):
    url = (f"https://api.github.com/repos/{repo}/actions/workflows/{WORKFLOW}/runs"
           "?status=success&per_page=1")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "kyiv-power-47-1"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            runs = json.loads(resp.read()).get("workflow_runs") or []
        if not runs:
            return None
        return datetime.fromisoformat(runs[0]["created_at"].replace("Z", "+00:00")).astimezone(KYIV)
    except Exception:
        return None


def render(days, now: datetime, cloud_ok_at, cache) -> str:
    """cache = (days, fetched_at) of the last good fetch, used when days is None."""
    shown, note = days, None
    if days is None:
        head = "❔"
        if cache:
            shown, note = cache[0], f"оновлено о {cache[1].strftime('%H:%M')}"
    else:
        head = title(days, now)
    out = [head, "---"]
    if shown is None:
        out.append("Немає даних від YASNO")
    else:
        for label, offset in (("Сьогодні", 0), ("Завтра", 1)):
            out.append(f"{label} | size=13")
            out += day_lines(shown.get((now.date() + timedelta(days=offset)).isoformat()))
        if note:
            out.append(f"{note} | color=gray")
    if cloud_ok_at is None:
        out.append("⚠️ Telegram-сповіщення: стан невідомий")
    elif now - cloud_ok_at > CLOUD_STALE:
        out.append(f"⚠️ Telegram-сповіщення не працюють з {cloud_ok_at.strftime('%H:%M')}")
    out += ["---", "Оновити | refresh=true", "YASNO | href=https://yasno.ua"]
    return "\n".join(out)


def main() -> None:
    now = datetime.now(KYIV)
    cache = None
    try:
        with open(CACHE, encoding="utf-8") as f:
            c = json.load(f)
        cache = (c["days"], datetime.fromisoformat(c["at"]))
    except Exception:
        pass
    try:
        days = normalize(fetch_raw())
        try:
            with open(CACHE, "w", encoding="utf-8") as f:
                json.dump({"days": days, "at": now.isoformat()}, f)
        except OSError:
            pass
    except FetchError:
        days = None
    print(render(days, now, last_cloud_success(), cache))


if __name__ == "__main__":
    main()
