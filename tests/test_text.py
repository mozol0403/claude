import unittest

from power.text import change_message, daily_message, day_lines, hhmm

SCHED = {"status": "ScheduleApplies", "off": [[480, 720, "definite"], [1080, 1320, "possible"]]}


class TextTest(unittest.TestCase):
    def test_hhmm(self):
        self.assertEqual(hhmm(480), "08:00")
        self.assertEqual(hhmm(0), "00:00")
        self.assertEqual(hhmm(1440), "24:00")
        self.assertEqual(hhmm(90), "01:30")

    def test_daily_with_slots(self):
        self.assertEqual(daily_message("2026-11-07", SCHED),
                         "🗓 Графік на завтра, сб 7 листопада (група 47.1)\n"
                         "🕯 08:00–12:00\n❓ 18:00–22:00")

    def test_daily_emergency(self):
        self.assertEqual(daily_message("2026-11-07", {"status": "EmergencyShutdowns", "off": []}),
                         "🗓 Графік на завтра, сб 7 листопада (група 47.1)\n"
                         "⚠️ Аварійні відключення, графіка немає")

    def test_daily_waiting_and_none(self):
        expected = ("🗓 Графік на завтра, сб 7 листопада (група 47.1)\n"
                    "⏳ Графіка на завтра ще немає")
        self.assertEqual(daily_message("2026-11-07", None), expected)
        self.assertEqual(daily_message("2026-11-07", {"status": "WaitingForSchedule", "off": []}),
                         expected)

    def test_day_lines_variants(self):
        self.assertEqual(day_lines({"status": "ScheduleApplies", "off": []}), ["⚡ Відключень немає"])
        self.assertEqual(day_lines({"status": "Weird", "off": []}), ["Статус YASNO: Weird"])
        self.assertEqual(day_lines(None), ["⏳ Графіка ще немає"])

    def test_month_and_weekday(self):
        self.assertTrue(daily_message("2027-01-04", None).startswith("🗓 Графік на завтра, пн 4 січня"))

    def test_change_message(self):
        msg = change_message("сьогодні", {"status": "EmergencyShutdowns", "off": []}, SCHED)
        self.assertEqual(msg,
                         "🔄 Графік на сьогодні змінився (група 47.1)\n"
                         "Було:\n⚠️ Аварійні відключення, графіка немає\n"
                         "Стало:\n🕯 08:00–12:00\n❓ 18:00–22:00")

    def test_change_message_from_none(self):
        self.assertIn("Було:\n⏳ Графіка ще немає", change_message("завтра", None, SCHED))


if __name__ == "__main__":
    unittest.main()
