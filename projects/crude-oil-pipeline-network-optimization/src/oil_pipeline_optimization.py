from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict, List, Tuple

import pulp


ROOT = Path(__file__).resolve().parents[1]
NODES_CSV = ROOT / "data" / "nodes.csv"
PIPELINES_CSV = ROOT / "data" / "candidate_pipelines.csv"

Arc = Tuple[str, str]


def load_nodes(path: Path) -> Dict[str, dict]:
    nodes: Dict[str, dict] = {}
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            node_id = row["node_id"]
            nodes[node_id] = {
                "node_type": row["node_type"],
                "supply": float(row["supply_kbbl_day"]),
                "demand": float(row["demand_kbbl_day"]),
                "pump_candidate": int(row["pump_candidate"]),
                "pump_capacity": float(row["pump_capacity_kbbl_day"]),
                "pump_fixed_cost": float(row["pump_fixed_cost_musd_year"]),
            }
    return nodes


def load_arcs(path: Path) -> Dict[Arc, dict]:
    arcs: Dict[Arc, dict] = {}
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            arc = (row["from_node"], row["to_node"])
            arcs[arc] = {
                "distance": float(row["distance_km"]),
                "capacity": float(row["capacity_kbbl_day"]),
                "fixed_cost": float(row["fixed_cost_musd_year"]),
                "variable_cost": float(row["variable_cost_kusd_per_kbbl"]),
                "environmental_penalty": float(row["environmental_penalty_musd_year"]),
                "regulatory_cost": float(row["regulatory_cost_musd_year"]),
                "prohibited": int(row["prohibited"]),
            }
    return arcs


def validate_instance(nodes: Dict[str, dict], arcs: Dict[Arc, dict]) -> None:
    source_nodes = [n for n, d in nodes.items() if d["node_type"] == "source"]
    refinery_nodes = [n for n, d in nodes.items() if d["node_type"] == "refinery"]

    if not source_nodes:
        raise ValueError("The instance must contain at least one source node.")
    if not refinery_nodes:
        raise ValueError("The instance must contain at least one refinery node.")

    total_supply = sum(nodes[n]["supply"] for n in source_nodes)
    total_demand = sum(nodes[n]["demand"] for n in refinery_nodes)
    if abs(total_supply - total_demand) > 1e-9:
        raise ValueError(
            f"Total supply ({total_supply}) must equal total demand ({total_demand}) for this closed-network case."
        )

    for arc, data in arcs.items():
        i, j = arc
        if i not in nodes or j not in nodes:
            raise ValueError(f"Arc {arc} references an undefined node.")
        if data["capacity"] <= 0:
            raise ValueError(f"Arc {arc} must have strictly positive capacity.")
        if data["fixed_cost"] < 0 or data["variable_cost"] < 0:
            raise ValueError(f"Arc {arc} contains a negative cost.")
        if data["prohibited"] not in (0, 1):
            raise ValueError(f"Arc {arc} has an invalid prohibited flag.")

    for n, data in nodes.items():
        if data["pump_candidate"] not in (0, 1):
            raise ValueError(f"Node {n} has an invalid pump_candidate flag.")
        if data["pump_candidate"] == 1 and data["pump_capacity"] <= 0:
            raise ValueError(f"Pump candidate {n} must have positive capacity.")


def build_model(nodes: Dict[str, dict], arcs: Dict[Arc, dict]):
    model = pulp.LpProblem("Crude_Oil_Pipeline_Network_Optimization", pulp.LpMinimize)

    arc_list: List[Arc] = list(arcs.keys())
    pump_nodes = [n for n, d in nodes.items() if d["pump_candidate"] == 1]

    flow = pulp.LpVariable.dicts("Flow_kbbl_day", arc_list, lowBound=0, cat=pulp.LpContinuous)
    build = pulp.LpVariable.dicts("Build_Pipeline", arc_list, lowBound=0, upBound=1, cat=pulp.LpBinary)
    pump = pulp.LpVariable.dicts("Activate_Pump", pump_nodes, lowBound=0, upBound=1, cat=pulp.LpBinary)

    annual_variable_cost = pulp.lpSum(
        (365.0 / 1000.0) * arcs[a]["variable_cost"] * flow[a]
        for a in arc_list
    )
    annual_fixed_pipeline_cost = pulp.lpSum(
        (
            arcs[a]["fixed_cost"]
            + arcs[a]["environmental_penalty"]
            + arcs[a]["regulatory_cost"]
        )
        * build[a]
        for a in arc_list
    )
    annual_pump_cost = pulp.lpSum(nodes[p]["pump_fixed_cost"] * pump[p] for p in pump_nodes)

    model += annual_fixed_pipeline_cost + annual_variable_cost + annual_pump_cost, "Total_Annualized_Cost"

    incoming = {n: [a for a in arc_list if a[1] == n] for n in nodes}
    outgoing = {n: [a for a in arc_list if a[0] == n] for n in nodes}

    for n, data in nodes.items():
        inflow = pulp.lpSum(flow[a] for a in incoming[n])
        outflow = pulp.lpSum(flow[a] for a in outgoing[n])

        if data["node_type"] == "source":
            model += outflow - inflow == data["supply"], f"Source_Balance_{n}"
        elif data["node_type"] == "refinery":
            model += inflow - outflow == data["demand"], f"Refinery_Balance_{n}"
        else:
            model += inflow == outflow, f"Flow_Conservation_{n}"

    for a in arc_list:
        model += flow[a] <= arcs[a]["capacity"] * build[a], f"Capacity_Link_{a[0]}_{a[1]}"
        model += build[a] <= 1 - arcs[a]["prohibited"], f"Prohibited_RightOfWay_{a[0]}_{a[1]}"

    for p in pump_nodes:
        outbound_flow = pulp.lpSum(flow[a] for a in outgoing[p])
        outbound_built = pulp.lpSum(build[a] for a in outgoing[p])
        model += outbound_flow <= nodes[p]["pump_capacity"] * pump[p], f"Pump_Capacity_{p}"
        model += pump[p] <= outbound_built, f"Pump_Relevance_{p}"

    return model, flow, build, pump


def solve_model(model: pulp.LpProblem) -> str:
    solver = pulp.PULP_CBC_CMD(msg=False)
    model.solve(solver)
    return pulp.LpStatus[model.status]


def report_solution(
    model: pulp.LpProblem,
    status: str,
    nodes: Dict[str, dict],
    arcs: Dict[Arc, dict],
    flow,
    build,
    pump,
) -> None:
    print(f"Status: {status}")
    if status != "Optimal":
        print("No optimal solution was found.")
        return

    print(f"Total annualized cost: {pulp.value(model.objective):.3f} million USD/year")
    print("\nSelected pipelines and flows:")
    for a in arcs:
        if build[a].value() > 0.5:
            utilization = 100.0 * flow[a].value() / arcs[a]["capacity"] if arcs[a]["capacity"] > 0 else 0.0
            print(
                f"  {a[0]} -> {a[1]}: flow={flow[a].value():.3f} kbbl/day, "
                f"capacity={arcs[a]['capacity']:.3f}, utilization={utilization:.1f}%"
            )

    print("\nActivated pumping stations:")
    active_pumps = [p for p in pump if pump[p].value() > 0.5]
    if not active_pumps:
        print("  None")
    else:
        for p in active_pumps:
            print(
                f"  {p}: capacity={nodes[p]['pump_capacity']:.3f} kbbl/day, "
                f"fixed cost={nodes[p]['pump_fixed_cost']:.3f} million USD/year"
            )


def verify_solution(
    status: str,
    nodes: Dict[str, dict],
    arcs: Dict[Arc, dict],
    flow,
    build,
    pump,
    tolerance: float = 1e-6,
) -> None:
    if status != "Optimal":
        return

    incoming = {n: [a for a in arcs if a[1] == n] for n in nodes}
    outgoing = {n: [a for a in arcs if a[0] == n] for n in nodes}

    for n, data in nodes.items():
        inflow = sum(flow[a].value() for a in incoming[n])
        outflow = sum(flow[a].value() for a in outgoing[n])

        if data["node_type"] == "source":
            residual = outflow - inflow - data["supply"]
        elif data["node_type"] == "refinery":
            residual = inflow - outflow - data["demand"]
        else:
            residual = inflow - outflow

        if abs(residual) > tolerance:
            raise AssertionError(f"Flow-balance check failed at {n}: residual={residual}")

    for a, data in arcs.items():
        f = flow[a].value()
        y = build[a].value()
        if f - data["capacity"] * y > tolerance:
            raise AssertionError(f"Capacity/build link failed on arc {a}.")
        if data["prohibited"] == 1 and y > tolerance:
            raise AssertionError(f"Prohibited arc {a} was selected.")

    for p in pump:
        outbound = sum(flow[a].value() for a in outgoing[p])
        if outbound - nodes[p]["pump_capacity"] * pump[p].value() > tolerance:
            raise AssertionError(f"Pump-capacity check failed at {p}.")

    print("\nVerification: all flow, capacity, prohibition, and pump checks passed.")


def main() -> None:
    nodes = load_nodes(NODES_CSV)
    arcs = load_arcs(PIPELINES_CSV)
    validate_instance(nodes, arcs)

    model, flow, build, pump = build_model(nodes, arcs)
    status = solve_model(model)
    report_solution(model, status, nodes, arcs, flow, build, pump)
    verify_solution(status, nodes, arcs, flow, build, pump)


if __name__ == "__main__":
    main()
