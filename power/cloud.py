"""One cloud run: fetch, diff against state, send Telegram messages, return state.

`run` mutates `state` step by step, so if a send raises, everything already
sent is recorded and everything not sent is retried on the next run.
"""
import json
import os
import sys
from datetime import datetime, timedelta

from power import telegram
from power.diff import changes
from power.schedule import KYIV, FetchError, fetch_raw, normalize
from power.text import change_message, daily_message, human_date

FAIL_TEXT = "❗ Не можу отримати графік з YASNO (група 47.1). Напишу, коли знову запрацює."
OK_TEXT = "✅ Графік з YASNO знову доступний (група 47.1)."
FAIL_THRESHOLD = 3
DAILY_HOUR = 22
STATE_FILE = "state.json"


def new_state() -> dict:
    return {"days": {}, "daily_sent": None, "fail_count": 0, "fail_notified": False}


def run(state: dict, now: datetime, fetch, send) -> dict:
    today = now.date().isoformat()
    tomorrow = (now.date() + timedelta(days=1)).isoformat()
    try:
        days = fetch()
    except FetchError as e:
        print(f"fetch failed: {e}")
        state["fail_count"] += 1
        if state["fail_count"] >= FAIL_THRESHOLD and not state["fail_notified"]:
            send(FAIL_TEXT)
            state["fail_notified"] = True
        return state

    if state["fail_notified"]:
        send(OK_TEXT)
        state["fail_notified"] = False
    state["fail_count"] = 0

    days = {d: v for d, v in days.items() if d >= today}
    old = {d: v for d, v in state["days"].items() if d >= today}
    for d, before, after in changes(old, days):
        label = "сьогодні" if d == today else "завтра" if d == tomorrow else human_date(d)
        send(change_message(label, before, after))
        state["days"][d] = after

    if now.hour >= DAILY_HOUR and state["daily_sent"] != tomorrow:
        send(daily_message(tomorrow, days.get(tomorrow)))
        state["daily_sent"] = tomorrow

    state["days"] = days
    return state


def main() -> int:
    try:
        with open(STATE_FILE, encoding="utf-8") as f:
            state = {**new_state(), **json.load(f)}
    except (FileNotFoundError, ValueError):
        state = new_state()
    now = datetime.now(KYIV)
    if os.environ.get("FORCE_DAILY") == "1":
        state["daily_sent"] = None
        now = now.replace(hour=DAILY_HOUR, minute=0)
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")
    if not token or not chat_id:
        print("TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID are not set")
        return 1

    def send(text):
        telegram.send(text, token, chat_id)
        print("sent:", text.splitlines()[0])

    code = 0
    try:
        run(state, now, lambda: normalize(fetch_raw()), send)
    except RuntimeError as e:
        print(f"send failed: {e}")
        code = 1
    finally:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=1, sort_keys=True)
            f.write("\n")
    return code


if __name__ == "__main__":
    sys.exit(main())
