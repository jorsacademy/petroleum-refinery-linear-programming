"""Pre-solve structural validation."""

from __future__ import annotations

from .data import AluminumData


class DataValidationError(ValueError):
    pass


def validate_data(data: AluminumData) -> None:
    errors: list[str] = []

    for mine in data.mines:
        if data.mine_capacity.get(mine, 0.0) > 0 and data.mine_reserves.get(mine, 0.0) <= 0:
            errors.append(f"Mine {mine!r} has capacity but no reserves.")
        if not any(data.mine_bauxite.get((mine, bauxite), 0) for bauxite in data.bauxites):
            errors.append(f"Mine {mine!r} has no bauxite mapping.")

    for plant in data.plants:
        for unit in data.units:
            capacity = data.plant_capacity.get((plant, unit), 0.0)
            if capacity > 0 and not any(
                data.unit_process.get((unit, process), 0.0) != 0.0 for process in data.processes
            ):
                errors.append(f"Plant unit {unit!r} at {plant!r} has capacity but no process mapping.")

    for market in data.markets:
        if data.demand.get(market, 0.0) < 0:
            errors.append(f"Market {market!r} has negative demand.")

    for (plant, electricity), capacity in data.electricity_capacity.items():
        if capacity > 0 and (plant, electricity) not in data.electricity_price:
            errors.append(f"Electricity source {electricity!r} at {plant!r} has capacity but no price.")

    if not (0 < data.mine_utilization <= 1):
        errors.append("Mine utilization must lie in (0, 1].")

    for unit, utilization in data.unit_utilization.items():
        if not (0 < utilization <= 1):
            errors.append(f"Utilization for {unit!r} must lie in (0, 1].")

    if data.reserve_interval <= 0:
        errors.append("Reserve interval must be positive.")

    if errors:
        raise DataValidationError("\n".join(errors))
