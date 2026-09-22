"""Reporting helpers for solved Pyomo models."""

from __future__ import annotations

from pyomo.environ import value


def summarize_solution(model) -> dict[str, float]:
    return {
        "mine_operating_cost": value(model.mine_operating_cost),
        "process_operating_cost": value(model.process_operating_cost),
        "electricity_cost": value(model.electricity_cost),
        "transport_cost": value(model.transport_cost),
        "mine_investment_cost": value(model.mine_investment_cost),
        "plant_investment_cost": value(model.plant_investment_cost),
        "tariff_cost": value(model.tariff_cost),
        "levy_cost": value(model.levy_cost),
        "objective_cost": value(model.total_cost_excluding_tariffs_and_levies),
        "total_cost_including_tariffs_and_levies": value(model.total_cost),
    }


def print_solution_summary(model) -> None:
    summary = summarize_solution(model)
    print("Solution cost summary")
    print("---------------------")
    for key, val in summary.items():
        print(f"{key:42s} {val:12.4f}")
