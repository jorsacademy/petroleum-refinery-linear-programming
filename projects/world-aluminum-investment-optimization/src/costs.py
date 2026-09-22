"""Cost expressions and helper functions."""

from __future__ import annotations

from pyomo.environ import Expression


def add_cost_expressions(model, data):
    model.mine_operating_cost = Expression(
        expr=sum(
            data.mine_operating_cost.get(mine, 0.0) * model.zm[bauxite, mine]
            for bauxite in data.bauxites
            for mine in data.mines
            if (bauxite, mine) in model.ZM_INDEX
        ) / 1000.0
    )

    model.process_operating_cost = Expression(
        expr=sum(
            data.process_operating_cost.get((plant, process), 0.0) * model.z[process, plant]
            for process, plant in model.Z_INDEX
        ) / 1000.0
    )

    model.electricity_cost = Expression(
        expr=sum(
            data.electricity_price.get((plant, electricity), 0.0) * model.u[electricity, plant]
            for electricity, plant in model.U_INDEX
        ) / 1000.0
    )

    model.transport_cost = Expression(
        expr=(
            sum(
                data.bauxite_transport.get((mine, plant), 0.0) * model.xm[bauxite, mine, plant]
                for bauxite, mine, plant in model.XM_INDEX
            )
            + sum(
                data.alumina_transport.get((origin, destination), 0.0) * model.xi[origin, destination]
                for origin, destination in model.XI_INDEX
            )
            + sum(
                data.aluminum_transport.get((plant, market), 0.0) * model.xf[plant, market]
                for plant, market in model.XF_INDEX
            )
        ) / 1000.0
    )

    model.mine_investment_cost = Expression(
        expr=data.capital_recovery_factor
        * sum(
            data.mine_segment_cost.get((mine, segment), 0.0) * model.sm[segment, mine]
            for segment, mine in model.SM_INDEX
        )
    )

    model.plant_investment_cost = Expression(
        expr=data.capital_recovery_factor
        * sum(
            data.plant_segment_cost.get((unit, segment, plant), 0.0) * model.sr[unit, segment, plant]
            for unit, segment, plant in model.SR_INDEX
        )
    )

    model.tariff_cost = Expression(
        expr=(
            sum(
                data.aluminum_tariff.get((market, plant), 0.0) * model.xf[plant, market]
                for plant, market in model.XF_INDEX
            )
            + sum(
                data.alumina_tariff.get((destination, origin), 0.0) * model.xi[origin, destination]
                for origin, destination in model.XI_INDEX
            )
        ) / 1000.0
    )

    model.levy_cost = Expression(
        expr=(
            sum(
                data.bauxite_levy.get((bauxite, mine, plant), 0.0) * model.xm[bauxite, mine, plant]
                for bauxite, mine, plant in model.XM_INDEX
            )
            + sum(
                data.alumina_levy.get((origin, destination), 0.0) * model.xi[origin, destination]
                for origin, destination in model.XI_INDEX
            )
        ) / 1000.0
    )

    model.total_cost_excluding_tariffs_and_levies = Expression(
        expr=model.mine_operating_cost
        + model.process_operating_cost
        + model.electricity_cost
        + model.transport_cost
        + model.mine_investment_cost
        + model.plant_investment_cost
    )

    model.total_cost = Expression(
        expr=model.total_cost_excluding_tariffs_and_levies
        + model.tariff_cost
        + model.levy_cost
    )
