"""Ukrainian text for days, the daily message and change messages."""
from datetime import date

GROUP_LABEL = "група 47.1"
WEEKDAYS = ["пн", "вт", "ср", "чт", "пт", "сб", "нд"]
MONTHS = ["січня", "лютого", "березня", "квітня", "травня", "червня", "липня",
          "серпня", "вересня", "жовтня", "листопада", "грудня"]
WAITING = {"WaitingForSchedule"}


def hhmm(minutes: int) -> str:
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


def _is_waiting(day) -> bool:
    return day is None or (day["status"] in WAITING and not day["off"])


def day_lines(day) -> list:
    if _is_waiting(day):
        return ["⏳ Графіка ще немає"]
    if day["off"]:
        return [f"{'🕯' if k == 'definite' else '❓'} {hhmm(s)}–{hhmm(e)}" for s, e, k in day["off"]]
    if day["status"] == "EmergencyShutdowns":
        return ["⚠️ Аварійні відключення, графіка немає"]
    if day["status"] == "ScheduleApplies":
        return ["⚡ Відключень немає"]
    return [f"Статус YASNO: {day['status']}"]


def human_date(iso: str) -> str:
    d = date.fromisoformat(iso)
    return f"{WEEKDAYS[d.weekday()]} {d.day} {MONTHS[d.month - 1]}"


def daily_message(iso: str, day) -> str:
    head = f"🗓 Графік на завтра, {human_date(iso)} ({GROUP_LABEL})"
    body = ["⏳ Графіка на завтра ще немає"] if _is_waiting(day) else day_lines(day)
    return "\n".join([head] + body)


def change_message(label: str, old, new) -> str:
    return "\n".join([f"🔄 Графік на {label} змінився ({GROUP_LABEL})", "Було:"]
                     + day_lines(old) + ["Стало:"] + day_lines(new))
