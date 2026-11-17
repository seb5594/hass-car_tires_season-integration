"""Season windows and movable holidays."""
import unittest
from datetime import date

from support import load

calendar_utils = load("calendar_utils")
Window, fixed, easter = calendar_utils.Window, calendar_utils.fixed, calendar_utils.easter


class EasterDates(unittest.TestCase):
    def test_known_easter_sundays(self):
        known = {2024: date(2024, 3, 31), 2025: date(2025, 4, 20), 2026: date(2026, 4, 5),
                 2027: date(2027, 3, 28), 2038: date(2038, 4, 25)}
        for year, expected in known.items():
            self.assertEqual(calendar_utils.easter_sunday(year), expected, year)


class Windows(unittest.TestCase):
    def test_window_reaching_into_the_next_year(self):
        window = Window(fixed(12, 1), fixed(2, 29))
        self.assertEqual(window.span_starting_in(2026), (date(2026, 12, 1), date(2027, 2, 28)))
        self.assertEqual(window.span_starting_in(2027), (date(2027, 12, 1), date(2028, 2, 29)))

    def test_window_inside_one_year(self):
        window = Window(fixed(6, 1), fixed(9, 30))
        self.assertEqual(window.span_starting_in(2026), (date(2026, 6, 1), date(2026, 9, 30)))

    def test_easter_window_follows_the_holiday(self):
        window = Window(fixed(10, 1), easter())
        self.assertEqual(window.span_starting_in(2025), (date(2025, 10, 1), date(2026, 4, 5)))

    def test_current_or_next(self):
        window = Window(fixed(11, 15), fixed(3, 15))
        self.assertEqual(window.current_or_next(date(2027, 1, 10)), (date(2026, 11, 15), date(2027, 3, 15)))
        self.assertEqual(window.current_or_next(date(2027, 7, 1)), (date(2027, 11, 15), date(2028, 3, 15)))

    def test_contains_with_and_without_margin(self):
        window = Window(fixed(11, 15), fixed(3, 15))
        self.assertTrue(window.contains(date(2027, 3, 15)))
        self.assertFalse(window.contains(date(2027, 3, 16)))
        self.assertTrue(window.contains(date(2027, 3, 16), margin_days=1))
        self.assertTrue(window.contains(date(2026, 11, 1), margin_days=14))
        self.assertFalse(window.contains(date(2026, 7, 1), margin_days=31))


if __name__ == "__main__":
    unittest.main()
