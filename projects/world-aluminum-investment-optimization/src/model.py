"""Pyomo formulation of the aluminum investment optimization model."""

from __future__ import annotations

from pyomo.environ import (
    Binary,
    ConcreteModel,
    Constraint,
    NonNegativeReals,
    Objective,
    Set,
    Var,
    minimize,
)

from .costs import add_cost_expressions
from .data import AluminumData
from .mappings import valid_bauxite_shipments, valid_processes_at_plant, valid_unit_process_pairs


def build_model(data: AluminumData):
    model = ConcreteModel(name="World Aluminum Investment Optimization")

    model.MINES = Set(initialize=list(data.mines))
    model.PLANTS = Set(initialize=list(data.plants))
    model.MARKETS = Set(initialize=list(data.markets))
    model.BAUXITES = Set(initialize=list(data.bauxites))
    model.PROCESSES = Set(initialize=list(data.processes))
    model.UNITS = Set(initialize=list(data.units))
    model.ELECTRICITY = Set(initialize=list(data.electricity_types))
    model.SEGMENTS = Set(initialize=list(data.segments))

    model.XM_INDEX = Set(dimen=3, initialize=valid_bauxite_shipments(data))
    model.XI_INDEX = Set(dimen=2, initialize=[(a, b) for a in data.plants for b in data.plants])
    model.XF_INDEX = Set(dimen=2, initialize=[(plant, market) for plant in data.plants for market in data.markets])
    model.Z_INDEX = Set(dimen=2, initialize=valid_processes_at_plant(data))
    model.ZM_INDEX = Set(
        dimen=2,
        initialize=[
            (bauxite, mine)
            for mine in data.mines
            for bauxite in data.bauxites
            if data.mine_bauxite.get((mine, bauxite), 0)
        ],
    )
    model.U_INDEX = Set(dimen=2, initialize=[(e, plant) for e in data.electricity_types for plant in data.plants])
    model.SM_INDEX = Set(dimen=2, initialize=[(segment, mine) for segment in data.segments for mine in data.mines])
    model.SR_INDEX = Set(dimen=3, initialize=[(unit, segment, plant) for unit in data.units for segment in data.segments for plant in data.plants])
    model.HR_INDEX = Set(dimen=2, initialize=[(plant, unit) for plant in data.plants for unit in data.units])

    model.xm = Var(model.XM_INDEX, domain=NonNegativeReals)
    model.xi = Var(model.XI_INDEX, domain=NonNegativeReals)
    model.xf = Var(model.XF_INDEX, domain=NonNegativeReals)
    model.z = Var(model.Z_INDEX, domain=NonNegativeReals)
    model.zm = Var(model.ZM_INDEX, domain=NonNegativeReals)
    model.u = Var(model.U_INDEX, domain=NonNegativeReals)
    model.hm = Var(model.MINES, domain=NonNegativeReals)
    model.hr = Var(model.HR_INDEX, domain=NonNegativeReals)
    model.sm = Var(model.SM_INDEX, domain=NonNegativeReals)
    model.sr = Var(model.SR_INDEX, domain=NonNegativeReals)
    model.ym = Var(model.MINES, domain=Binary)
    model.yr = Var(model.HR_INDEX, domain=Binary)

    def mine_balance_rule(m, bauxite, mine):
        shipments = sum(
            m.xm[bauxite, mine, plant]
            for plant in data.plants
            if (bauxite, mine, plant) in m.XM_INDEX
        )
        return m.zm[bauxite, mine] >= shipments + data.nonmetal_bauxite.get(mine, 0.0)

    model.mine_balance = Constraint(model.ZM_INDEX, rule=mine_balance_rule)

    def bauxite_reserve_rule(m, bauxite, mine):
        return data.reserve_interval * m.zm[bauxite, mine] <= data.mine_reserves.get(mine, 0.0)

    model.bauxite_reserve = Constraint(model.ZM_INDEX, rule=bauxite_reserve_rule)

    def mine_capacity_rule(m, mine):
        production = sum(m.zm[bauxite, mine] for bauxite in data.bauxites if (bauxite, mine) in m.ZM_INDEX)
        return production <= data.mine_utilization * (data.mine_capacity.get(mine, 0.0) + m.hm[mine])

    model.mine_capacity = Constraint(model.MINES, rule=mine_capacity_rule)

    def mine_expansion_rule(m, mine):
        return m.hm[mine] == sum(
            data.mine_segment_size.get((mine, segment), 0.0) * m.sm[segment, mine]
            for segment in data.segments
        )

    model.mine_expansion = Constraint(model.MINES, rule=mine_expansion_rule)

    def mine_convexity_rule(m, mine):
        return m.ym[mine] == sum(m.sm[segment, mine] for segment in data.segments)

    model.mine_convexity = Constraint(model.MINES, rule=mine_convexity_rule)

    def plant_expansion_rule(m, plant, unit):
        return m.hr[plant, unit] == sum(
            data.plant_segment_size.get((unit, segment, plant), 0.0) * m.sr[unit, segment, plant]
            for segment in data.segments
        )

    model.plant_expansion = Constraint(model.HR_INDEX, rule=plant_expansion_rule)

    def plant_convexity_rule(m, plant, unit):
        return m.yr[plant, unit] == sum(m.sr[unit, segment, plant] for segment in data.segments)

    model.plant_convexity = Constraint(model.HR_INDEX, rule=plant_convexity_rule)

    active_unit_process = valid_unit_process_pairs(data)

    def plant_capacity_rule(m, plant, unit):
        activity = sum(
            data.unit_process.get((unit, process), 0.0) * m.z[process, plant]
            for u, process in active_unit_process
            if u == unit and (process, plant) in m.Z_INDEX
        )
        return activity <= data.unit_utilization.get(unit, 1.0) * (
            data.plant_capacity.get((plant, unit), 0.0) + m.hr[plant, unit]
        )

    model.plant_capacity = Constraint(model.HR_INDEX, rule=plant_capacity_rule)

    commodities = list(data.bauxites) + ["alumina", "aluminum", "electr"]
    model.COMMODITIES = Set(initialize=commodities)

    def plant_material_balance_rule(m, commodity, plant):
        process_net = sum(
            data.process_coeff.get((commodity, process), 0.0) * m.z[process, plant]
            for process in data.processes
            if (process, plant) in m.Z_INDEX
        )

        bauxite_in = 0.0
        if commodity in data.bauxites:
            bauxite_in = sum(
                m.xm[commodity, mine, plant]
                for mine in data.mines
                if (commodity, mine, plant) in m.XM_INDEX
            )

        alumina_in = 0.0
        alumina_out = 0.0
        if commodity == "alumina":
            alumina_in = sum(m.xi[origin, plant] for origin in data.plants)
            alumina_out = sum(m.xi[plant, destination] for destination in data.plants)

        electricity_in = 0.0
        if commodity == "electr":
            electricity_in = sum(m.u[electricity, plant] for electricity in data.electricity_types)

        aluminum_out = 0.0
        if commodity == "aluminum":
            aluminum_out = sum(m.xf[plant, market] for market in data.markets)

        nonmetal_alumina = data.nonmetal_alumina.get(plant, 0.0) if commodity == "alumina" else 0.0

        return process_net + bauxite_in + alumina_in + electricity_in >= alumina_out + aluminum_out + nonmetal_alumina

    model.plant_material_balance = Constraint(model.COMMODITIES, model.PLANTS, rule=plant_material_balance_rule)

    def demand_rule(m, market):
        return sum(m.xf[plant, market] for plant in data.plants) >= data.demand.get(market, 0.0)

    model.market_demand = Constraint(model.MARKETS, rule=demand_rule)

    def electricity_capacity_rule(m, electricity, plant):
        return m.u[electricity, plant] <= data.electricity_capacity.get((plant, electricity), 0.0)

    model.electricity_capacity = Constraint(model.U_INDEX, rule=electricity_capacity_rule)

    add_cost_expressions(model, data)

    # Mirrors the original scenario objective phi4: tariffs and levies are excluded.
    model.objective = Objective(expr=model.total_cost_excluding_tariffs_and_levies, sense=minimize)

    return model
