import unittest

from power.diff import changes

EMER = {"status": "EmergencyShutdowns", "off": []}
WAIT = {"status": "WaitingForSchedule", "off": []}
SCHED = {"status": "ScheduleApplies", "off": [[480, 720, "definite"]]}
SCHED2 = {"status": "ScheduleApplies", "off": [[480, 720, "definite"], [900, 960, "definite"]]}


class DiffTest(unittest.TestCase):
    def test_first_run_is_silent(self):
        self.assertEqual(changes({}, {"2026-11-06": SCHED, "2026-11-07": SCHED}), [])

    def test_same_content_no_change(self):
        self.assertEqual(changes({"2026-11-06": SCHED}, {"2026-11-06": dict(SCHED)}), [])

    def test_slot_added_today(self):
        self.assertEqual(changes({"2026-11-06": SCHED}, {"2026-11-06": SCHED2}),
                         [("2026-11-06", SCHED, SCHED2)])

    def test_new_date_waiting_is_silent(self):
        self.assertEqual(changes({"2026-11-06": SCHED}, {"2026-11-06": SCHED, "2026-11-07": WAIT}), [])

    def test_new_date_emergency_is_silent(self):
        self.assertEqual(changes({"2026-11-06": EMER}, {"2026-11-06": EMER, "2026-11-07": EMER}), [])

    def test_new_date_with_slots_is_change(self):
        self.assertEqual(changes({"2026-11-06": SCHED}, {"2026-11-06": SCHED, "2026-11-07": SCHED}),
                         [("2026-11-07", None, SCHED)])

    def test_waiting_to_published(self):
        self.assertEqual(changes({"2026-11-07": WAIT}, {"2026-11-07": SCHED}),
                         [("2026-11-07", WAIT, SCHED)])

    def test_midnight_rollover_is_silent(self):
        old = {"2026-11-06": SCHED, "2026-11-07": SCHED2}
        new = {"2026-11-07": SCHED2, "2026-11-08": WAIT}
        self.assertEqual(changes(old, new), [])

    def test_sorted_by_date(self):
        old = {"2026-11-06": SCHED, "2026-11-07": SCHED}
        new = {"2026-11-07": SCHED2, "2026-11-06": SCHED2}
        self.assertEqual([c[0] for c in changes(old, new)], ["2026-11-06", "2026-11-07"])


if __name__ == "__main__":
    unittest.main()
