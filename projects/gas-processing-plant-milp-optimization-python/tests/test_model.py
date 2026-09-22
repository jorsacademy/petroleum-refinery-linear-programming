import math
import unittest

from gas_plant_milp_optimization import GasPlantMILP


class GasPlantMILPTests(unittest.TestCase):
    def test_reference_solution_is_optimal_and_balanced(self):
        model = GasPlantMILP()
        result = model.solve()
        self.assertEqual(result.status, "OPTIMAL")
        self.assertEqual(result.active_mode, "Low_Recovery")
        self.assertTrue(math.isclose(result.objective_profit, 3099.231403659234, abs_tol=1e-6))

        for product in model.PRODUCTS:
            lhs = result.production[product] + model.initial_inventory[product]
            rhs = result.sales[product] + result.ending_inventory[product]
            self.assertTrue(math.isclose(lhs, rhs, abs_tol=1e-7))

    def test_sales_gas_is_mass_balanced(self):
        model = GasPlantMILP()
        result = model.solve()
        total_feed = sum(result.feed.values())
        ngl = sum(result.production[p] for p in ["Ethane", "Propane", "Butane", "Pentane_Plus"])
        condensate = result.production["Condensate"]
        expected_sales_gas = total_feed * (1 - model.FUEL_FRACTION - model.FLARE_FRACTION) - ngl - condensate
        self.assertTrue(math.isclose(result.production["Sales_Gas"], expected_sales_gas, abs_tol=1e-7))

    def test_source_and_total_capacities_hold(self):
        model = GasPlantMILP()
        result = model.solve()
        for source, cap in model.feed_capacity.items():
            self.assertLessEqual(result.feed[source], cap + 1e-7)
        self.assertLessEqual(sum(result.feed.values()), model.TOTAL_PROCESSING_CAPACITY + 1e-7)

    def test_fixed_mode_lp_oracle_matches_milp(self):
        model = GasPlantMILP()
        milp_result = model.solve()
        fixed = {mode: model.solve_fixed_mode(mode) for mode in model.MODES}
        best_mode = max(fixed, key=lambda m: fixed[m].objective_profit)
        self.assertEqual(best_mode, milp_result.active_mode)
        self.assertTrue(math.isclose(
            fixed[best_mode].objective_profit,
            milp_result.objective_profit,
            abs_tol=1e-6,
        ))

    def test_inventory_stays_within_bounds(self):
        model = GasPlantMILP()
        result = model.solve()
        for product in model.PRODUCTS:
            self.assertGreaterEqual(
                result.ending_inventory[product],
                model.safety_stock[product] - 1e-7,
            )
            self.assertLessEqual(
                result.ending_inventory[product],
                model.storage_capacity[product] + 1e-7,
            )


if __name__ == "__main__":
    unittest.main()
