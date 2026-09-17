import unittest
from dataclasses import replace

from scripts.common import rank_probabilities, read_matches
from scripts.constraints import constraint_errors, team_win
from scripts.metrics import hit_distribution, probability_at_least
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

    def test_independent_validator_detects_each_structural_violation(self):
        ticket = optimize(read_matches("data/proximo_concurso.csv"))
        broken = list(ticket.selections)
        broken[0] = frozenset()
        errors = constraint_errors(ticket.matches, broken)
        self.assertTrue(any("palpite inválido" in error for error in errors))
        self.assertTrue(any("estrutura" in error for error in errors))
        self.assertTrue(any("marcações" in error for error in errors))
        self.assertTrue(any("Flamengo" in error for error in errors))

    def test_flamengo_visitor_win_is_outcome_two(self):
        match = read_matches("data/proximo_concurso.csv")[0]
        visitor_match = replace(match, home="OUTRO/XX", away="flamengo/rj")
        self.assertEqual(team_win(visitor_match, "FLAMENGO/RJ"), "2")

    def test_exact_probability_distribution(self):
        distribution = hit_distribution([.5, .5])
        self.assertEqual(distribution, (.25, .5, .25))
        self.assertEqual(probability_at_least([.5, .5], 1), .75)
        self.assertAlmostEqual(sum(distribution), 1.0)

    def test_probability_metric_rejects_invalid_coverage(self):
        with self.assertRaisesRegex(ValueError, "Cobertura inválida"):
            hit_distribution([1.01])


if __name__ == "__main__":
    unittest.main()
