import unittest

from transco_optimization import DEMAND, MAX_INITIAL_PRODUCTION, solve_transco


class TestTranscoOptimization(unittest.TestCase):
    def test_optimal_solution_is_feasible(self):
        result, diagnostics = solve_transco()

        self.assertTrue(result.success)
        self.assertLessEqual(
            diagnostics["total_initial_production"],
            MAX_INITIAL_PRODUCTION + 1e-7,
        )

        for quality, required in DEMAND.items():
            self.assertGreaterEqual(
                diagnostics["final_quality"][quality] + 1e-7,
                required,
            )

    def test_reference_optimum(self):
        _, diagnostics = solve_transco()
        self.assertAlmostEqual(diagnostics["minimum_cost"], 641725.352112676, places=5)
        self.assertAlmostEqual(diagnostics["method_1"], 10563.38028169014, places=5)
        self.assertAlmostEqual(diagnostics["method_2"], 0.0, places=7)


if __name__ == "__main__":
    unittest.main()
