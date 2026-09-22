from __future__ import annotations

from pyomo.environ import SolverFactory
from pyomo.opt import TerminationCondition

from src.data import demo_data
from src.model import build_model
from src.reporting import print_solution_summary
from src.validation import validate_data


def main() -> None:
    data = demo_data()
    validate_data(data)
    model = build_model(data)

    solver = SolverFactory("appsi_highs")
    results = solver.solve(model)

    if results.solver.termination_condition != TerminationCondition.optimal:
        raise RuntimeError(
            f"Optimization did not terminate optimally: "
            f"{results.solver.termination_condition}"
        )

    print_solution_summary(model)


if __name__ == "__main__":
    main()
