import unittest
from scullery import units
from scullery import snake_compat


class TestMisc(unittest.TestCase):
    def test_snake_compat(self):
        assert snake_compat.camel_to_snake("CamelCase") == "camel_case"
        assert snake_compat.camel_to_snake("camelCase") == "camel_case"
        assert snake_compat.camel_to_snake("/camelCase") == "/camel_case"
        assert snake_compat.snake_to_camel("camel_case") == "camelCase"

    def test_conversions(self):
        "Test with a longer requested result"
        self.assertEqual(units.convert(12, "in", "ft"), 1)
        self.assertEqual(units.convert(1, "km", "m"), 1000)
        self.assertAlmostEqual(units.convert(50, "degC", "degF"), 122)
        self.assertAlmostEqual(units.convert(122, "degF", "degC"), 50)
        self.assertAlmostEqual(units.convert(1, "kft", "in"), 12000)
        # Milli-inches?
        self.assertAlmostEqual(units.convert(1, "ft", "min"), 12000)

        self.assertEqual(units.si_format_number(12), "12")
        self.assertEqual(units.si_format_number(2000), "2K")
        self.assertEqual(units.si_format_number(2000_000), "2M")
        self.assertEqual(units.si_format_number(2000_000_000), "2G")
        self.assertEqual(units.si_format_number(1 / 1000), "1m")
        self.assertEqual(units.si_format_number(1 / 1000_000), "1u")
        self.assertEqual(units.si_format_number(1 / 1000_000_000), "1n")

    def test_nonsense_convert(self):
        with self.assertRaises(Exception):
            units.convert("80", "trashpiles", "garbages")
        # Can't use SI prefixes with nonlinear units like degrees
        with self.assertRaises(Exception):
            units.convert("80", "mdegC", "K")
