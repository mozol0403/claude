import io
import unittest
from unittest import mock

from power.schedule import FetchError, fetch_raw, normalize

RAW = {"47.1": {"today": {"slots": [{"start": 480, "end": 720, "type": "Definite"},
                                    {"start": 0, "end": 480, "type": "NotPlanned"}],
                          "date": "2026-11-06T00:00:00+02:00", "status": "ScheduleApplies"},
                "tomorrow": {"slots": [], "date": "2026-11-07T00:00:00+02:00",
                             "status": "WaitingForSchedule"},
                "updatedOn": "2026-11-06T10:31:44+00:00"}}


class FakeResp(io.BytesIO):
    status = 200

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class NormalizeTest(unittest.TestCase):
    def test_normalize_keys_by_date_and_drops_on_slots(self):
        self.assertEqual(normalize(RAW), {
            "2026-11-06": {"status": "ScheduleApplies", "off": [[480, 720, "definite"]]},
            "2026-11-07": {"status": "WaitingForSchedule", "off": []},
        })

    def test_unknown_slot_type_is_possible(self):
        raw = {"47.1": {"today": {"slots": [{"start": 60, "end": 120, "type": "Possible"}],
                                  "date": "2026-11-06T00:00:00+02:00", "status": "ScheduleApplies"}}}
        self.assertEqual(normalize(raw)["2026-11-06"]["off"], [[60, 120, "possible"]])

    def test_slots_sorted_by_start(self):
        raw = {"47.1": {"today": {"slots": [{"start": 600, "end": 660, "type": "Definite"},
                                            {"start": 60, "end": 120, "type": "Definite"}],
                                  "date": "2026-11-06T00:00:00+02:00", "status": "ScheduleApplies"}}}
        self.assertEqual([s[0] for s in normalize(raw)["2026-11-06"]["off"]], [60, 600])

    def test_missing_group_raises_fetcherror(self):
        with self.assertRaises(FetchError):
            normalize({"1.1": RAW["47.1"]})

    def test_day_without_status_raises_fetcherror(self):
        with self.assertRaises(FetchError):
            normalize({"47.1": {"today": {"slots": [], "date": "2026-11-06T00:00:00+02:00"}}})


class FetchTest(unittest.TestCase):
    def test_fetch_raw_html_raises_fetcherror(self):
        with mock.patch("urllib.request.urlopen", return_value=FakeResp(b"<html>blocked</html>")):
            with self.assertRaises(FetchError):
                fetch_raw()

    def test_fetch_raw_list_raises_fetcherror(self):
        with mock.patch("urllib.request.urlopen", return_value=FakeResp(b"[1,2]")):
            with self.assertRaises(FetchError):
                fetch_raw()

    def test_fetch_raw_network_error_raises_fetcherror(self):
        with mock.patch("urllib.request.urlopen", side_effect=OSError("down")):
            with self.assertRaises(FetchError):
                fetch_raw()

    def test_fetch_raw_ok(self):
        with mock.patch("urllib.request.urlopen", return_value=FakeResp(b'{"47.1": {}}')):
            self.assertEqual(fetch_raw(), {"47.1": {}})


if __name__ == "__main__":
    unittest.main()
