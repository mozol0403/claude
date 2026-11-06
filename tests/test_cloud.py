import json
import unittest
from datetime import datetime
from unittest import mock

from power import telegram
from power.cloud import FAIL_TEXT, OK_TEXT, new_state, run
from power.schedule import KYIV, FetchError

EMER = {"status": "EmergencyShutdowns", "off": []}
WAIT = {"status": "WaitingForSchedule", "off": []}
SCHED = {"status": "ScheduleApplies", "off": [[480, 720, "definite"]]}


def at(y, m, d, h, mi=0):
    return datetime(y, m, d, h, mi, tzinfo=KYIV)


class Sender:
    def __init__(self, fail=False):
        self.sent, self.fail = [], fail

    def __call__(self, text):
        if self.fail:
            raise RuntimeError("telegram down")
        self.sent.append(text)


def fetch_of(days):
    return lambda: dict(days)


def failing():
    raise FetchError("down")


class CloudRunTest(unittest.TestCase):
    def test_first_run_silent(self):
        s, st = Sender(), new_state()
        run(st, at(2026, 11, 6, 15), fetch_of({"2026-11-06": SCHED, "2026-11-07": WAIT}), s)
        self.assertEqual(s.sent, [])
        self.assertEqual(set(st["days"]), {"2026-11-06", "2026-11-07"})

    def test_daily_once_at_22(self):
        s, st = Sender(), new_state()
        st["days"] = {"2026-11-06": EMER, "2026-11-07": SCHED}
        st["daily_sent"] = "2026-11-06"
        days = {"2026-11-06": EMER, "2026-11-07": SCHED}
        run(st, at(2026, 11, 6, 22, 7), fetch_of(days), s)
        self.assertEqual(len(s.sent), 1)
        self.assertTrue(s.sent[0].startswith("🗓 Графік на завтра, сб 7 листопада"))
        self.assertEqual(st["daily_sent"], "2026-11-07")
        run(st, at(2026, 11, 6, 22, 17), fetch_of(days), s)
        self.assertEqual(len(s.sent), 1)

    def test_no_daily_before_22(self):
        s, st = Sender(), new_state()
        st["days"] = {"2026-11-06": EMER}
        run(st, at(2026, 11, 6, 21, 59), fetch_of({"2026-11-06": EMER}), s)
        self.assertEqual(s.sent, [])

    def test_change_then_daily(self):
        s, st = Sender(), new_state()
        st["days"] = {"2026-11-06": EMER, "2026-11-07": WAIT}
        run(st, at(2026, 11, 6, 22, 5), fetch_of({"2026-11-06": EMER, "2026-11-07": SCHED}), s)
        self.assertEqual(len(s.sent), 2)
        self.assertTrue(s.sent[0].startswith("🔄 Графік на завтра змінився"))
        self.assertTrue(s.sent[1].startswith("🗓"))

    def test_change_today_label(self):
        s, st = Sender(), new_state()
        st["days"] = {"2026-11-06": EMER}
        run(st, at(2026, 11, 6, 10), fetch_of({"2026-11-06": SCHED}), s)
        self.assertTrue(s.sent[0].startswith("🔄 Графік на сьогодні змінився"))

    def test_failure_notified_once_then_recovery(self):
        s, st = Sender(), new_state()
        st["days"] = {"2026-11-06": EMER}
        for _ in range(4):
            run(st, at(2026, 11, 6, 10), failing, s)
        self.assertEqual(s.sent, [FAIL_TEXT])
        self.assertEqual(st["days"], {"2026-11-06": EMER})
        run(st, at(2026, 11, 6, 10, 40), fetch_of({"2026-11-06": EMER}), s)
        self.assertEqual(s.sent, [FAIL_TEXT, OK_TEXT])
        self.assertEqual(st["fail_count"], 0)
        self.assertFalse(st["fail_notified"])

    def test_two_failures_silent(self):
        s, st = Sender(), new_state()
        for _ in range(2):
            run(st, at(2026, 11, 6, 10), failing, s)
        run(st, at(2026, 11, 6, 10, 30), fetch_of({"2026-11-06": EMER}), s)
        self.assertEqual(s.sent, [])

    def test_send_failure_keeps_old_day_for_retry(self):
        st = new_state()
        st["days"] = {"2026-11-06": EMER}
        with self.assertRaises(RuntimeError):
            run(st, at(2026, 11, 6, 10), fetch_of({"2026-11-06": SCHED}), Sender(fail=True))
        self.assertEqual(st["days"]["2026-11-06"], EMER)
        s = Sender()
        run(st, at(2026, 11, 6, 10, 10), fetch_of({"2026-11-06": SCHED}), s)
        self.assertEqual(len(s.sent), 1)

    def test_daily_send_failure_retried(self):
        st = new_state()
        st["days"] = {"2026-11-07": SCHED}
        with self.assertRaises(RuntimeError):
            run(st, at(2026, 11, 6, 22), fetch_of({"2026-11-07": SCHED}), Sender(fail=True))
        self.assertIsNone(st["daily_sent"])

    def test_dst_evening(self):
        s, st = Sender(), new_state()
        st["days"] = {"2026-10-25": EMER}
        run(st, at(2026, 10, 25, 22, 5), fetch_of({"2026-10-25": EMER, "2026-10-26": EMER}), s)
        self.assertEqual(st["daily_sent"], "2026-10-26")

    def test_past_dates_dropped(self):
        s, st = Sender(), new_state()
        st["days"] = {"2026-11-05": SCHED, "2026-11-06": EMER}
        run(st, at(2026, 11, 6, 0, 5), fetch_of({"2026-11-05": EMER, "2026-11-06": EMER}), s)
        self.assertEqual(s.sent, [])
        self.assertEqual(set(st["days"]), {"2026-11-06"})


class TelegramTest(unittest.TestCase):
    def test_error_does_not_leak_token(self):
        with mock.patch("urllib.request.urlopen", side_effect=OSError("boom SECRET123")):
            with self.assertRaises(RuntimeError) as cm:
                telegram.send("hi", "SECRET123", "42")
        self.assertNotIn("SECRET123", str(cm.exception))

    def test_not_ok_raises(self):
        class R:
            def __enter__(self): return self
            def __exit__(self, *a): return False
            def read(self): return json.dumps({"ok": False, "description": "chat not found"}).encode()
        with mock.patch("urllib.request.urlopen", return_value=R()):
            with self.assertRaises(RuntimeError):
                telegram.send("hi", "T", "42")


if __name__ == "__main__":
    unittest.main()
