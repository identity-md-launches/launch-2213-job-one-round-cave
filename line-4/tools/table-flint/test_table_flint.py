"""Regression checks for the portable CSV calculator."""
import json
from fractions import Fraction
from pathlib import Path
import random
import subprocess
import sys
import unittest

import table_flint


class TableFlintTests(unittest.TestCase):
    def test_mixed_units_and_weighted_mean(self):
        raw = b"distance,weight,note\n1 km,2,first\n500 m,1,second\n25000 cm,0,ignored\n"
        result = table_flint.compute(raw, "distance", "weight", "m", {
            "sum": "1750 m", "mean": "1750 m / 3", "weighted_mean": "2500 m / 3"})
        self.assertTrue(result["passes"])
        self.assertEqual(result["values"]["minimum"]["value"], "250")
        self.assertEqual(result["values"]["maximum"]["value"], "1000")
        self.assertEqual(result["total_weight"], "3")

    def test_fraction_oracle_random_tables(self):
        rng = random.Random(101)
        factors = {"m": Fraction(1), "cm": Fraction(1, 100), "km": Fraction(1000)}
        for _ in range(100):
            values, weights, rows = [], [], ["value,weight"]
            for _ in range(rng.randint(1, 20)):
                amount = rng.randint(-100, 100)
                unit = rng.choice(tuple(factors))
                weight = rng.randint(0, 5)
                rows.append(f"{amount} {unit},{weight}")
                values.append(amount * factors[unit])
                weights.append(weight)
            if sum(weights) == 0:
                weights[-1] = 1
                rows[-1] = rows[-1].rsplit(",", 1)[0] + ",1"
            actual = table_flint.compute(("\n".join(rows) + "\n").encode(), weight_column="weight")
            expected = {"sum": sum(values), "mean": sum(values) / len(values),
                        "minimum": min(values), "maximum": max(values),
                        "weighted_mean": sum(v*w for v, w in zip(values, weights)) / sum(weights)}
            for name, value in expected.items():
                self.assertEqual(Fraction(actual["values"][name]["base_value"]), value)

    def test_unit_conversion_and_dimension_rejection(self):
        result = table_flint.compute(b"value\n1 km\n500 m\n", to="km")
        self.assertEqual(result["values"]["sum"]["value"], "1.5")
        with self.assertRaisesRegex(table_flint.TableError, "row 2: dimension"):
            table_flint.compute(b"value\n1 km\n2 s\n")
        with self.assertRaisesRegex(table_flint.TableError, "target unit"):
            table_flint.compute(b"value\n1 km\n", to="s")

    def test_header_and_row_shape(self):
        for data in (b"", b"value,value\n1 m,2 m\n", b"x\n1 m\n",
                     b"value\n", b"value,weight\n1 m\n", b"value\n\"broken\n"):
            with self.subTest(data=data), self.assertRaises(table_flint.TableError):
                table_flint.compute(data)

    def test_weights(self):
        for data in (b"value,weight\n1 m,-1\n", b"value,weight\n1 m,1 s\n",
                     b"value,weight\n1 m,0\n"):
            with self.subTest(data=data), self.assertRaises(table_flint.TableError):
                table_flint.compute(data, weight_column="weight")
        with self.assertRaisesRegex(table_flint.TableError, "not name an available result"):
            table_flint.compute(b"value\n1 m\n", claims={"weighted_mean": "1 m"})

    def test_claim_failure_is_result(self):
        result = table_flint.compute(b"value\n1 m\n2 m\n", claims={"sum": "4 m"})
        self.assertFalse(result["passes"])
        self.assertEqual(result["checks"]["sum"]["difference_base_value"], "-1")
        with self.assertRaisesRegex(table_flint.TableError, "incompatible dimensions"):
            table_flint.compute(b"value\n1 m\n", claims={"sum": "1 s"})

    def test_bounds_and_encoding(self):
        with self.assertRaisesRegex(table_flint.TableError, "exceeds 262144"):
            table_flint.compute(b"x" * 262145)
        with self.assertRaisesRegex(table_flint.TableError, "UTF-8"):
            table_flint.compute(b"value\n\xff\n")
        with self.assertRaisesRegex(table_flint.TableError, "exceeds 4096"):
            table_flint.compute(b"value\n" + b"1 m\n" * 4097)

    def test_cli_streams_and_status(self):
        script = Path(__file__).with_name("table_flint.py")
        def run(*args, data=b""):
            return subprocess.run([sys.executable, "-B", str(script), *args],
                                  input=data, capture_output=True, check=False)
        demo = run("demo")
        self.assertEqual(demo.returncode, 0, demo.stderr)
        self.assertTrue(json.loads(demo.stdout)["passes"])
        fail = run("check", "--expect-sum", "4 m", data=b"value\n1 m\n2 m\n")
        self.assertEqual(fail.returncode, 1)
        self.assertFalse(json.loads(fail.stdout)["passes"])
        invalid = run("check", data=b"value\n1 s\n2 m\n")
        self.assertEqual(invalid.returncode, 2)
        self.assertEqual(invalid.stdout, b"")
        self.assertIn(b"row 2", invalid.stderr)


if __name__ == "__main__":
    unittest.main()
