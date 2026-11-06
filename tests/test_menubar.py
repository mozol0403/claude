import unittest
from datetime import datetime, timedelta

from power.menubar import render, title
from power.schedule import KYIV

T, M = "2026-11-06", "2026-11-07"


def at(h, mi=0):
    return datetime(2026, 11, 6, h, mi, tzinfo=KYIV)


def sched(*slots, status="ScheduleApplies"):
    return {"status": status, "off": [list(s) for s in slots]}


class TitleTest(unittest.TestCase):
    def test_inside_outage(self):
        self.assertEqual(title({T: sched((480, 720, "definite"))}, at(10)), "🕯 до 12:00")

    def test_before_next_outage(self):
        self.assertEqual(title({T: sched((480, 720, "definite"), (1080, 1200, "definite"))}, at(13)),
                         "⚡ до 18:00")

    def test_next_outage_tomorrow(self):
        days = {T: sched((480, 720, "definite")), M: sched((0, 240, "definite"))}
        self.assertEqual(title(days, at(23)), "⚡ до 00:00")

    def test_outage_across_midnight_merged(self):
        days = {T: sched((1200, 1440, "definite")), M: sched((0, 120, "definite"))}
        self.assertEqual(title(days, at(21)), "🕯 до 02:00")

    def test_possible_ignored_in_title(self):
        self.assertEqual(title({T: sched((600, 700, "possible"))}, at(10, 30)), "⚡")

    def test_emergency(self):
        self.assertEqual(title({T: {"status": "EmergencyShutdowns", "off": []}}, at(10)), "⚠️ аварійні")

    def test_nothing_ahead(self):
        self.assertEqual(title({T: sched()}, at(10)), "⚡")


class RenderTest(unittest.TestCase):
    DAYS = {T: sched((480, 720, "definite")), M: {"status": "WaitingForSchedule", "off": []}}

    def test_ok(self):
        out = render(self.DAYS, at(10), at(9, 50), None)
        lines = out.splitlines()
        self.assertEqual(lines[0], "🕯 до 12:00")
        self.assertIn("---", lines)
        self.assertIn("🕯 08:00–12:00", out)
        self.assertIn("⏳ Графіка ще немає", out)
        self.assertNotIn("Telegram-сповіщення", out)
        self.assertIn("refresh=true", out)

    def test_cloud_stale(self):
        out = render(self.DAYS, at(12), at(9, 50), None)
        self.assertIn("⚠️ Telegram-сповіщення не працюють з 09:50", out)

    def test_cloud_unknown(self):
        self.assertIn("⚠️ Telegram-сповіщення: стан невідомий", render(self.DAYS, at(12), None, None))

    def test_fetch_failed_uses_cache(self):
        out = render(None, at(12), at(11, 55), (self.DAYS, at(11)))
        self.assertEqual(out.splitlines()[0], "❔")
        self.assertIn("оновлено о 11:00", out)
        self.assertIn("🕯 08:00–12:00", out)

    def test_fetch_failed_no_cache(self):
        out = render(None, at(12), at(11, 55), None)
        self.assertEqual(out.splitlines()[0], "❔")
        self.assertIn("Немає даних від YASNO", out)


if __name__ == "__main__":
    unittest.main()
