from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp


@dataclass
class GasPlantResult:
    status: str
    objective_profit: float
    active_mode: str | None
    feed: Dict[str, float]
    production: Dict[str, float]
    sales: Dict[str, float]
    ending_inventory: Dict[str, float]
    revenue: float
    feed_cost: float
    operating_cost: float
    storage_cost: float


class GasPlantMILP:
    """
    Educational gas-processing planning MILP.

    Improvements over the original formulation:
    - no Big-M recovery equations: feed is disaggregated by operating mode
    - product production has explicit mass-balance equations
    - Sales Gas is an equality, not a free lower-bounded variable
    - sales and ending inventory are linked to production by inventory balance
    - market bounds apply to sales rather than production
    - mode-dependent fractionation and refrigeration limits are linear
    - no MILP 'shadow price' claims are reported

    All flow quantities use a common abstract flow unit in this educational
    model. Economic coefficients represent internally consistent
    model units rather than a calibrated real gas-plant accounting system.
    """

    FEED_SOURCES = (
        "Offshore_Field_A",
        "Offshore_Field_B",
        "Onshore_Field_C",
        "Associated_Gas_D",
    )
    MODES = ("High_Recovery", "Standard", "Low_Recovery")
    PRODUCTS = (
        "Sales_Gas",
        "Ethane",
        "Propane",
        "Butane",
        "Pentane_Plus",
        "Condensate",
    )
    FUEL_FRACTION = 0.08
    FLARE_FRACTION = 0.02
    TOTAL_PROCESSING_CAPACITY = 1200.0

    def __init__(self):
        self.feed_capacity = {
            "Offshore_Field_A": 450.0,
            "Offshore_Field_B": 380.0,
            "Onshore_Field_C": 320.0,
            "Associated_Gas_D": 280.0,
        }
        self.feed_costs = {
            "Offshore_Field_A": 1.2,
            "Offshore_Field_B": 1.5,
            "Onshore_Field_C": 0.9,
            "Associated_Gas_D": 0.7,
        }
        self.prices = {
            "Sales_Gas": 4.2,
            "Ethane": 18.5,
            "Propane": 25.0,
            "Butane": 28.0,
            "Pentane_Plus": 42.0,
            "Condensate": 65.0,
        }
        self.mode_costs = {
            "High_Recovery": 15000.0,
            "Standard": 10000.0,
            "Low_Recovery": 7000.0,
        }
        self.storage_costs = {
            "Sales_Gas": 0.05,
            "Ethane": 0.8,
            "Propane": 1.0,
            "Butane": 1.2,
            "Pentane_Plus": 2.0,
            "Condensate": 3.0,
        }
        self.storage_capacity = {
            "Sales_Gas": 50.0,
            "Ethane": 100.0,
            "Propane": 150.0,
            "Butane": 120.0,
            "Pentane_Plus": 80.0,
            "Condensate": 70.0,
        }

        self.demand_min = {
            "Sales_Gas": 700.0,
            "Ethane": 60.0,
            "Propane": 80.0,
            "Butane": 40.0,
            "Pentane_Plus": 20.0,
            "Condensate": 15.0,
        }
        self.demand_max = {
            "Sales_Gas": 1100.0,
            "Ethane": 150.0,
            "Propane": 200.0,
            "Butane": 120.0,
            "Pentane_Plus": 80.0,
            "Condensate": 60.0,
        }

        # C1, C2, C3, C4, C5+, condensate.
        self.composition = {
            "Offshore_Field_A": (0.72, 0.12, 0.08, 0.04, 0.02, 0.02),
            "Offshore_Field_B": (0.68, 0.14, 0.09, 0.05, 0.02, 0.02),
            "Onshore_Field_C": (0.78, 0.10, 0.06, 0.03, 0.02, 0.01),
            "Associated_Gas_D": (0.65, 0.15, 0.10, 0.06, 0.03, 0.01),
        }
        self.recovery = {
            "High_Recovery": {
                "Ethane": 0.90,
                "Propane": 0.98,
                "Butane": 0.99,
                "Pentane_Plus": 0.995,
            },
            "Standard": {
                "Ethane": 0.70,
                "Propane": 0.95,
                "Butane": 0.98,
                "Pentane_Plus": 0.99,
            },
            "Low_Recovery": {
                "Ethane": 0.40,
                "Propane": 0.85,
                "Butane": 0.95,
                "Pentane_Plus": 0.98,
            },
        }

        self.fractionation_min = {
            "High_Recovery": 200.0,
            "Standard": 180.0,
            "Low_Recovery": 150.0,
        }
        self.fractionation_max = {
            "High_Recovery": 280.0,
            "Standard": 250.0,
            "Low_Recovery": 200.0,
        }
        self.refrigeration_factor = {
            "High_Recovery": 0.85,
            "Standard": 0.70,
            "Low_Recovery": 0.55,
        }
        self.refrigeration_capacity = {
            "High_Recovery": 950.0,
            "Standard": 850.0,
            "Low_Recovery": 700.0,
        }
        self.compression_factor = {
            "Offshore_Field_A": 1.15,
            "Offshore_Field_B": 1.20,
            "Onshore_Field_C": 1.00,
            "Associated_Gas_D": 0.95,
        }

        self.initial_inventory = {
            p: 0.20 * self.storage_capacity[p] for p in self.PRODUCTS
        }
        self.safety_stock = {
            p: 0.10 * self.storage_capacity[p] for p in self.PRODUCTS
        }

        self._build_indices()

    def _build_indices(self):
        idx = 0
        self.fm_idx: Dict[Tuple[str, str], int] = {}
        for s in self.FEED_SOURCES:
            for m in self.MODES:
                self.fm_idx[s, m] = idx
                idx += 1

        self.prod_idx = {}
        for p in self.PRODUCTS:
            self.prod_idx[p] = idx
            idx += 1

        self.sales_idx = {}
        for p in self.PRODUCTS:
            self.sales_idx[p] = idx
            idx += 1

        self.inv_idx = {}
        for p in self.PRODUCTS:
            self.inv_idx[p] = idx
            idx += 1

        self.mode_idx = {}
        for m in self.MODES:
            self.mode_idx[m] = idx
            idx += 1

        self.nvars = idx

    def _row(self):
        return np.zeros(self.nvars, dtype=float)

    def solve(self, *, time_limit: float = 60.0, fixed_mode: str | None = None) -> GasPlantResult:
        if fixed_mode is not None and fixed_mode not in self.MODES:
            raise ValueError(f"unknown processing mode: {fixed_mode}")

        c = np.zeros(self.nvars, dtype=float)

        for s in self.FEED_SOURCES:
            for m in self.MODES:
                c[self.fm_idx[s, m]] = self.feed_costs[s]

        for p in self.PRODUCTS:
            c[self.sales_idx[p]] = -self.prices[p]
            c[self.inv_idx[p]] = self.storage_costs[p]

        for m in self.MODES:
            c[self.mode_idx[m]] = self.mode_costs[m]

        lower = np.zeros(self.nvars, dtype=float)
        upper = np.full(self.nvars, np.inf, dtype=float)

        for p in self.PRODUCTS:
            lower[self.sales_idx[p]] = self.demand_min[p]
            upper[self.sales_idx[p]] = self.demand_max[p]
            lower[self.inv_idx[p]] = self.safety_stock[p]
            upper[self.inv_idx[p]] = self.storage_capacity[p]

        for m in self.MODES:
            upper[self.mode_idx[m]] = 1.0
            if fixed_mode is not None:
                fixed = 1.0 if m == fixed_mode else 0.0
                lower[self.mode_idx[m]] = fixed
                upper[self.mode_idx[m]] = fixed

        integrality = np.zeros(self.nvars, dtype=int)
        for m in self.MODES:
            integrality[self.mode_idx[m]] = 1

        rows: List[np.ndarray] = []
        lbs: List[float] = []
        ubs: List[float] = []

        def add(row, lb=-np.inf, ub=np.inf):
            rows.append(row)
            lbs.append(lb)
            ubs.append(ub)

        row = self._row()
        for m in self.MODES:
            row[self.mode_idx[m]] = 1.0
        add(row, 1.0, 1.0)

        for s in self.FEED_SOURCES:
            for m in self.MODES:
                row = self._row()
                row[self.fm_idx[s, m]] = 1.0
                row[self.mode_idx[m]] = -self.feed_capacity[s]
                add(row, ub=0.0)

        for s in self.FEED_SOURCES:
            row = self._row()
            for m in self.MODES:
                row[self.fm_idx[s, m]] = 1.0
            add(row, ub=self.feed_capacity[s])

        component_col = {
            "Ethane": 1,
            "Propane": 2,
            "Butane": 3,
            "Pentane_Plus": 4,
        }
        for product, col in component_col.items():
            row = self._row()
            row[self.prod_idx[product]] = 1.0
            for s in self.FEED_SOURCES:
                for m in self.MODES:
                    row[self.fm_idx[s, m]] -= (
                        self.composition[s][col] * self.recovery[m][product]
                    )
            add(row, 0.0, 0.0)

        row = self._row()
        row[self.prod_idx["Condensate"]] = 1.0
        for s in self.FEED_SOURCES:
            for m in self.MODES:
                row[self.fm_idx[s, m]] -= self.composition[s][5]
        add(row, 0.0, 0.0)

        row = self._row()
        row[self.prod_idx["Sales_Gas"]] = 1.0
        for s in self.FEED_SOURCES:
            for m in self.MODES:
                row[self.fm_idx[s, m]] -= (
                    1.0 - self.FUEL_FRACTION - self.FLARE_FRACTION
                )
        for product in ("Ethane", "Propane", "Butane", "Pentane_Plus", "Condensate"):
            row[self.prod_idx[product]] += 1.0
        add(row, 0.0, 0.0)

        for p in self.PRODUCTS:
            row = self._row()
            row[self.prod_idx[p]] = 1.0
            row[self.sales_idx[p]] = -1.0
            row[self.inv_idx[p]] = -1.0
            add(row, -self.initial_inventory[p], -self.initial_inventory[p])

        row = self._row()
        for s in self.FEED_SOURCES:
            for m in self.MODES:
                row[self.fm_idx[s, m]] = 1.0
        add(row, 600.0, self.TOTAL_PROCESSING_CAPACITY)

        row = self._row()
        for s in self.FEED_SOURCES:
            for m in self.MODES:
                row[self.fm_idx[s, m]] = self.compression_factor[s]
        add(row, ub=1350.0)

        row = self._row()
        for s in self.FEED_SOURCES:
            for m in self.MODES:
                row[self.fm_idx[s, m]] = 0.95
        add(row, ub=1100.0)

        row = self._row()
        for s in self.FEED_SOURCES:
            for m in self.MODES:
                row[self.fm_idx[s, m]] = 0.88
        add(row, ub=1000.0)

        row = self._row()
        for p in ("Ethane", "Propane", "Butane", "Pentane_Plus"):
            row[self.prod_idx[p]] = 1.0
        for m in self.MODES:
            row[self.mode_idx[m]] -= self.fractionation_max[m]
        add(row, ub=0.0)

        row = self._row()
        for p in ("Ethane", "Propane", "Butane", "Pentane_Plus"):
            row[self.prod_idx[p]] = -1.0
        for m in self.MODES:
            row[self.mode_idx[m]] += self.fractionation_min[m]
        add(row, ub=0.0)

        for m in self.MODES:
            row = self._row()
            for s in self.FEED_SOURCES:
                row[self.fm_idx[s, m]] = self.refrigeration_factor[m]
            row[self.mode_idx[m]] = -self.refrigeration_capacity[m]
            add(row, ub=0.0)

        row = self._row()
        for s in self.FEED_SOURCES:
            for m in self.MODES:
                row[self.fm_idx[s, m]] += 0.20
        for m in self.MODES:
            row[self.fm_idx["Offshore_Field_A", m]] -= 1.0
        add(row, ub=0.0)

        row = self._row()
        for s in self.FEED_SOURCES:
            for m in self.MODES:
                row[self.fm_idx[s, m]] -= 0.30
        for m in self.MODES:
            row[self.fm_idx["Associated_Gas_D", m]] += 1.0
        add(row, ub=0.0)

        row = self._row()
        for s in self.FEED_SOURCES:
            for m in self.MODES:
                row[self.fm_idx[s, m]] = self.FLARE_FRACTION
        add(row, ub=25.0)

        constraints = LinearConstraint(
            np.vstack(rows),
            np.asarray(lbs),
            np.asarray(ubs),
        )

        result = milp(
            c=c,
            integrality=integrality,
            bounds=Bounds(lower, upper),
            constraints=constraints,
            options={"time_limit": float(time_limit)},
        )

        if result.x is None:
            status = {
                1: "TIME_LIMIT_OR_ITERATION_LIMIT",
                2: "INFEASIBLE",
                3: "UNBOUNDED",
            }.get(result.status, "NO_SOLUTION")
            return GasPlantResult(
                status=status,
                objective_profit=float("-inf"),
                active_mode=None,
                feed={},
                production={},
                sales={},
                ending_inventory={},
                revenue=0.0,
                feed_cost=0.0,
                operating_cost=0.0,
                storage_cost=0.0,
            )

        x = result.x
        feed = {
            s: sum(x[self.fm_idx[s, m]] for m in self.MODES)
            for s in self.FEED_SOURCES
        }
        production = {p: x[self.prod_idx[p]] for p in self.PRODUCTS}
        sales = {p: x[self.sales_idx[p]] for p in self.PRODUCTS}
        ending_inventory = {p: x[self.inv_idx[p]] for p in self.PRODUCTS}
        active_mode = max(self.MODES, key=lambda m: x[self.mode_idx[m]])

        revenue = sum(self.prices[p] * sales[p] for p in self.PRODUCTS)
        feed_cost = sum(self.feed_costs[s] * feed[s] for s in self.FEED_SOURCES)
        operating_cost = self.mode_costs[active_mode]
        storage_cost = sum(
            self.storage_costs[p] * ending_inventory[p] for p in self.PRODUCTS
        )
        profit = revenue - feed_cost - operating_cost - storage_cost

        status = "OPTIMAL" if result.status == 0 else "FEASIBLE_LIMIT"

        return GasPlantResult(
            status=status,
            objective_profit=float(profit),
            active_mode=active_mode,
            feed={k: float(v) for k, v in feed.items()},
            production={k: float(v) for k, v in production.items()},
            sales={k: float(v) for k, v in sales.items()},
            ending_inventory={k: float(v) for k, v in ending_inventory.items()},
            revenue=float(revenue),
            feed_cost=float(feed_cost),
            operating_cost=float(operating_cost),
            storage_cost=float(storage_cost),
        )

    def solve_fixed_mode(self, mode: str, *, time_limit: float = 60.0) -> GasPlantResult:
        """Solve the model with one processing mode fixed for validation/sensitivity checks."""
        return self.solve(time_limit=time_limit, fixed_mode=mode)


if __name__ == "__main__":
    model = GasPlantMILP()
    result = model.solve()
    print("status:", result.status)
    print("mode:", result.active_mode)
    print("profit:", round(result.objective_profit, 2))
    print("feed:", result.feed)
    print("production:", result.production)
