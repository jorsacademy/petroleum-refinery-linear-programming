"""Chemical batch process design as a mixed-integer nonlinear program.

The model is inspired by classical batch-process design formulations, but all
numerical data in this repository are synthetic and differ from the reference
instance. The formulation uses logarithmic variables to obtain a convexified
continuous structure while retaining discrete parallel-unit choices.
"""

from __future__ import annotations

import math
from typing import Dict, Tuple

from pyomo.environ import (
    Binary,
    ConcreteModel,
    Constraint,
    Objective,
    Reals,
    Set,
    SolverFactory,
    Var,
    exp,
    minimize,
    value,
)


PRODUCTS = ("alpha", "beta")
STAGES = ("blender", "converter", "separator")
UNIT_CHOICES = (1, 2, 3)

HORIZON_HOURS = 7200.0
VOLUME_LOWER = 320.0
VOLUME_UPPER = 2800.0

DEMAND: Dict[str, float] = {
    "alpha": 185000.0,
    "beta": 142000.0,
}

COST_COEFFICIENT: Dict[str, float] = {
    "blender": 290.0,
    "converter": 545.0,
    "separator": 375.0,
}

COST_EXPONENT: Dict[str, float] = {
    "blender": 0.58,
    "converter": 0.62,
    "separator": 0.60,
}

SIZE_FACTOR: Dict[Tuple[str, str], float] = {
    ("alpha", "blender"): 2.4,
    ("alpha", "converter"): 3.2,
    ("alpha", "separator"): 4.5,
    ("beta", "blender"): 3.7,
    ("beta", "converter"): 5.4,
    ("beta", "separator"): 3.4,
}

PROCESSING_TIME: Dict[Tuple[str, str], float] = {
    ("alpha", "blender"): 7.5,
    ("alpha", "converter"): 18.0,
    ("alpha", "separator"): 4.8,
    ("beta", "blender"): 9.0,
    ("beta", "converter"): 13.5,
    ("beta", "separator"): 3.6,
}

LOG_UNIT_CHOICE = {k: math.log(k) for k in UNIT_CHOICES}


def build_model() -> ConcreteModel:
    """Build and return the Pyomo MINLP model."""
    model = ConcreteModel(name="chemical_batch_process_design")

    model.products = Set(initialize=PRODUCTS, ordered=True)
    model.stages = Set(initialize=STAGES, ordered=True)
    model.unit_choices = Set(initialize=UNIT_CHOICES, ordered=True)

    max_log_units = math.log(max(UNIT_CHOICES))

    batch_lower = {}
    batch_upper = {}
    cycle_lower = {}
    cycle_upper = {}

    for product in PRODUCTS:
        longest_parallelized_time = max(
            PROCESSING_TIME[product, stage] / max(UNIT_CHOICES)
            for stage in STAGES
        )
        longest_single_unit_time = max(
            PROCESSING_TIME[product, stage] for stage in STAGES
        )

        cycle_lower[product] = math.log(longest_parallelized_time)
        cycle_upper[product] = math.log(longest_single_unit_time)

        minimum_batch = DEMAND[product] * longest_parallelized_time / HORIZON_HOURS
        maximum_batch = min(
            DEMAND[product],
            min(VOLUME_UPPER / SIZE_FACTOR[product, stage] for stage in STAGES),
        )

        if minimum_batch <= 0 or maximum_batch <= 0 or minimum_batch > maximum_batch:
            raise ValueError(f"Invalid batch bounds for product {product}.")

        batch_lower[product] = math.log(minimum_batch)
        batch_upper[product] = math.log(maximum_batch)

    model.y = Var(model.unit_choices, model.stages, domain=Binary)
    model.log_volume = Var(
        model.stages,
        domain=Reals,
        bounds=(math.log(VOLUME_LOWER), math.log(VOLUME_UPPER)),
    )
    model.log_batch = Var(
        model.products,
        domain=Reals,
        bounds=lambda m, i: (batch_lower[i], batch_upper[i]),
    )
    model.log_cycle = Var(
        model.products,
        domain=Reals,
        bounds=lambda m, i: (cycle_lower[i], cycle_upper[i]),
    )
    model.log_units = Var(
        model.stages,
        domain=Reals,
        bounds=(0.0, max_log_units),
    )

    def volume_requirement_rule(m, product, stage):
        return m.log_volume[stage] >= (
            math.log(SIZE_FACTOR[product, stage]) + m.log_batch[product]
        )

    model.volume_requirement = Constraint(
        model.products, model.stages, rule=volume_requirement_rule
    )

    def cycle_requirement_rule(m, product, stage):
        return m.log_units[stage] + m.log_cycle[product] >= math.log(
            PROCESSING_TIME[product, stage]
        )

    model.cycle_requirement = Constraint(
        model.products, model.stages, rule=cycle_requirement_rule
    )

    def horizon_rule(m):
        return sum(
            DEMAND[product] * exp(m.log_cycle[product] - m.log_batch[product])
            for product in m.products
        ) <= HORIZON_HOURS

    model.production_horizon = Constraint(rule=horizon_rule)

    def unit_link_rule(m, stage):
        return m.log_units[stage] == sum(
            LOG_UNIT_CHOICE[k] * m.y[k, stage] for k in m.unit_choices
        )

    model.unit_link = Constraint(model.stages, rule=unit_link_rule)

    def one_unit_choice_rule(m, stage):
        return sum(m.y[k, stage] for k in m.unit_choices) == 1

    model.one_unit_choice = Constraint(model.stages, rule=one_unit_choice_rule)

    def total_cost_rule(m):
        return sum(
            COST_COEFFICIENT[stage]
            * exp(
                m.log_units[stage]
                + COST_EXPONENT[stage] * m.log_volume[stage]
            )
            for stage in m.stages
        )

    model.total_cost = Objective(rule=total_cost_rule, sense=minimize)

    # Initial values reproduce the intent of the reference GAMS model without
    # fixing the binary design decisions.
    for stage in STAGES:
        for k in UNIT_CHOICES:
            model.y[k, stage].value = 1.0 if k == 3 else 0.0
        model.log_units[stage].value = math.log(3.0)

    for product in PRODUCTS:
        model.log_batch[product].value = 0.5 * (
            batch_lower[product] + batch_upper[product]
        )

    for stage in STAGES:
        model.log_volume[stage].value = max(
            math.log(SIZE_FACTOR[product, stage])
            + value(model.log_batch[product])
            for product in PRODUCTS
        )

    for product in PRODUCTS:
        model.log_cycle[product].value = max(
            math.log(PROCESSING_TIME[product, stage])
            - value(model.log_units[stage])
            for stage in STAGES
        )

    return model


def solve_model(model: ConcreteModel, tee: bool = False):
    """Solve the MINLP with MindtPy using HiGHS for MILP and Ipopt for NLP.

    Required external solvers:
      - HiGHS (MILP master problems)
      - Ipopt (nonlinear subproblems)
    """
    highs = SolverFactory("highs")
    ipopt = SolverFactory("ipopt")

    if not highs.available(exception_flag=False):
        raise RuntimeError(
            "HiGHS is not available. Install highspy before solving this model."
        )
    if not ipopt.available(exception_flag=False):
        raise RuntimeError(
            "Ipopt is not available. Install an Ipopt executable before solving this model."
        )

    solver = SolverFactory("mindtpy")
    if not solver.available(exception_flag=False):
        raise RuntimeError("Pyomo MindtPy is not available in this environment.")

    return solver.solve(
        model,
        strategy="OA",
        mip_solver="highs",
        nlp_solver="ipopt",
        init_strategy="rNLP",
        tee=tee,
    )


def print_solution(model: ConcreteModel) -> None:
    """Print the optimal design in the original physical units."""
    print(f"Total annualized equipment cost: {value(model.total_cost):,.2f}")

    print("\nStage design")
    for stage in STAGES:
        units = round(math.exp(value(model.log_units[stage])))
        volume = math.exp(value(model.log_volume[stage]))
        print(f"  {stage:10s} | units = {units:d} | volume = {volume:,.2f} L")

    print("\nProduct operating variables")
    for product in PRODUCTS:
        batch = math.exp(value(model.log_batch[product]))
        cycle = math.exp(value(model.log_cycle[product]))
        print(
            f"  {product:10s} | batch size = {batch:,.2f} kg "
            f"| cycle time = {cycle:,.3f} h"
        )


if __name__ == "__main__":
    optimization_model = build_model()
    solve_model(optimization_model, tee=True)
    print_solution(optimization_model)
