import unittest
from uncertainty_lens import analyze

class LensTests(unittest.TestCase):
    def test_touching_is_ordered_and_overlap_is_uncertain(self):
        out = analyze([{"id":"a","start":0,"end":2}, {"id":"b","start":2,"end":4}, {"id":"c","start":1,"end":3}])
        self.assertIn({"before":"a","after":"b"}, out["definite_orders"])
        self.assertEqual(out["uncertain_pairs"], [{"events":["a","c"],"reason":"intervals overlap"}, {"events":["b","c"],"reason":"intervals overlap"}])
    def test_bad_interval(self):
        with self.assertRaises(ValueError): analyze([{"id":"bad","start":2,"end":1}])

if __name__ == "__main__": unittest.main()
