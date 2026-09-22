"""Minimum-cost germanium refining and reheating model for the Transco problem.

This is a linear programming (LP) model. The Turkish abbreviation "DP" in the
problem statement refers to Doğrusal Programlama (Linear Programming), not
Dynamic Programming.
"""

from __future__ import annotations

import numpy as np
from scipy.optimize import linprog


# Decision-vector order:
# [x1, x2, v_defective, v_q1, v_q2, v_q3]
#
# x1, x2: amount of germanium initially melted with methods 1 and 2.
# v_j: amount of initial quality j sent to reheating.

MELTING_COST = np.array([50.0, 70.0])
REHEATING_COST = 25.0
MAX_INITIAL_PRODUCTION = 20_000.0

# Rows: defective, quality 1, quality 2, quality 3, quality 4
# Columns: melting method 1, melting method 2
INITIAL_YIELD = np.array(
    [
        [0.30, 0.20],
        [0.30, 0.20],
        [0.20, 0.25],
        [0.15, 0.20],
        [0.05, 0.15],
    ]
)

# Rows: quality obtained AFTER reheating
#       defective, quality 1, quality 2, quality 3, quality 4
# Columns: quality sent INTO reheating
#          defective, quality 1, quality 2, quality 3
#
# The columns sum to 1.00, matching Table 2 in the problem statement.
REHEAT_YIELD = np.array(
    [
        [0.30, 0.00, 0.00, 0.00],
        [0.25, 0.30, 0.00, 0.00],
        [0.15, 0.30, 0.40, 0.00],
        [0.20, 0.20, 0.30, 0.50],
        [0.10, 0.20, 0.30, 0.50],
    ]
)

# Monthly demand for saleable transistor qualities 1..4.
DEMAND = {
    1: 3000.0,
    2: 3000.0,
    3: 2000.0,
    4: 1000.0,
}


def build_lp():
    """Build c, A_ub, b_ub, bounds for scipy.optimize.linprog."""
    # Objective: 50*x1 + 70*x2 + 25*sum(v_j)
    c = np.array(
        [
            MELTING_COST[0],
            MELTING_COST[1],
            REHEATING_COST,
            REHEATING_COST,
            REHEATING_COST,
            REHEATING_COST,
        ]
    )

    A_ub: list[np.ndarray] = []
    b_ub: list[float] = []

    # Reheating availability constraints:
    # v_j <= amount of quality j created by the initial melting stage.
    for j in range(4):
        row = np.zeros(6)
        row[2 + j] = 1.0
        row[0] -= INITIAL_YIELD[j, 0]
        row[1] -= INITIAL_YIELD[j, 1]
        A_ub.append(row)
        b_ub.append(0.0)

    # Initial production limit.
    row = np.zeros(6)
    row[0] = 1.0
    row[1] = 1.0
    A_ub.append(row)
    b_ub.append(MAX_INITIAL_PRODUCTION)

    # Demand constraints.
    # Final quality q = initial q - amount of q reheated (q=1..3)
    #                   + output of all reheating streams that become q.
    # We convert final_q >= demand_q into -final_q <= -demand_q.
    for q in range(1, 5):
        row = np.zeros(6)

        # - initial production of quality q
        row[0] = -INITIAL_YIELD[q, 0]
        row[1] = -INITIAL_YIELD[q, 1]

        # If quality q itself can be reheated, removing v_q from direct supply
        # contributes +v_q to -final_q.
        if q <= 3:
            row[2 + q] += 1.0

        # Reheating contributes positively to final_q, hence negatively here.
        for j in range(4):
            row[2 + j] -= REHEAT_YIELD[q, j]

        A_ub.append(row)
        b_ub.append(-DEMAND[q])

    bounds = [(0.0, None)] * 6
    return c, np.array(A_ub), np.array(b_ub), bounds


def solve_transco():
    """Solve the Transco LP and return the scipy result plus diagnostics."""
    c, A_ub, b_ub, bounds = build_lp()

    result = linprog(
        c,
        A_ub=A_ub,
        b_ub=b_ub,
        bounds=bounds,
        method="highs",
    )

    if not result.success:
        raise RuntimeError(f"Optimization failed: {result.message}")

    x1, x2 = result.x[:2]
    reheated = result.x[2:]

    initial_quality = INITIAL_YIELD @ np.array([x1, x2])

    final_quality = initial_quality.copy()
    # Quantities of defective/Q1/Q2/Q3 that are removed from the initial pool
    # and sent through reheating.
    final_quality[:4] -= reheated
    # Add the distribution obtained after reheating.
    final_quality += REHEAT_YIELD @ reheated

    diagnostics = {
        "method_1": x1,
        "method_2": x2,
        "total_initial_production": x1 + x2,
        "reheated": reheated,
        "initial_quality": initial_quality,
        "final_quality": final_quality,
        "minimum_cost": result.fun,
    }
    return result, diagnostics


def print_solution() -> None:
    _, d = solve_transco()

    labels = ["Defective", "Quality 1", "Quality 2", "Quality 3", "Quality 4"]
    reheated_labels = ["Defective", "Quality 1", "Quality 2", "Quality 3"]

    print("Optimal Transco production plan")
    print("-" * 36)
    print(f"Method 1 initial melting : {d['method_1']:.3f}")
    print(f"Method 2 initial melting : {d['method_2']:.3f}")
    print(f"Total initial production : {d['total_initial_production']:.3f}")
    print(f"Minimum monthly cost      : {d['minimum_cost']:.2f} TL")

    print("\nAmounts sent to reheating:")
    for label, value in zip(reheated_labels, d["reheated"]):
        print(f"  {label:10s}: {value:.3f}")

    print("\nFinal quality quantities:")
    for label, value in zip(labels, d["final_quality"]):
        print(f"  {label:10s}: {value:.3f}")

    print("\nDemand check:")
    for q in range(1, 5):
        produced = d["final_quality"][q]
        required = DEMAND[q]
        status = "OK" if produced + 1e-7 >= required else "NOT MET"
        print(
            f"  Quality {q}: produced={produced:.3f}, "
            f"required={required:.3f} -> {status}"
        )


if __name__ == "__main__":
    print_solution()
