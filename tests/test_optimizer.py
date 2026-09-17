import unittest

from scripts.common import rank_probabilities, read_matches
from scripts.optimize_ticket import TARGET_RANKS, TARGET_SIZES, counts, optimize, validate


class OptimizerTest(unittest.TestCase):
    def test_tie_break_is_one_then_two_then_draw(self):
        self.assertEqual(rank_probabilities({"1": .4, "X": .2, "2": .4}), ("1", "2", "X"))
        self.assertEqual(rank_probabilities({"1": 1/3, "X": 1/3, "2": 1/3}), ("1", "2", "X"))

    def test_generated_ticket_obeys_hard_constraints(self):
        ticket = optimize(read_matches("data/proximo_concurso.csv"))
        validate(ticket)
        sizes, ranks, _ = counts(ticket)
        self.assertEqual(sizes, TARGET_SIZES)
        self.assertEqual(ranks, TARGET_RANKS)
        flamengo = ticket.matches.index(next(m for m in ticket.matches if "FLAMENGO/RJ" in (m.home, m.away)))
        self.assertIn("1", ticket.selections[flamengo])
        self.assertGreaterEqual(ticket.probability_at_least(13), ticket.probability_at_least(14))


if __name__ == "__main__":
    unittest.main()
