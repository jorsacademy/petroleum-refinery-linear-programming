"""Data definitions for the aluminum investment optimization model."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Mapping, Sequence, Tuple


@dataclass(frozen=True)
class AluminumData:
    mines: Sequence[str]
    plants: Sequence[str]
    markets: Sequence[str]
    bauxites: Sequence[str]
    processes: Sequence[str]
    units: Sequence[str]
    electricity_types: Sequence[str]
    segments: Sequence[str]

    mine_bauxite: Mapping[Tuple[str, str], int]
    process_coeff: Mapping[Tuple[str, str], float]
    unit_process: Mapping[Tuple[str, str], float]

    demand: Mapping[str, float]
    nonmetal_bauxite: Mapping[str, float]
    nonmetal_alumina: Mapping[str, float]

    mine_capacity: Mapping[str, float]
    mine_reserves: Mapping[str, float]
    plant_capacity: Mapping[Tuple[str, str], float]
    electricity_capacity: Mapping[Tuple[str, str], float]

    mine_utilization: float
    unit_utilization: Mapping[str, float]
    reserve_interval: float

    mine_segment_size: Mapping[Tuple[str, str], float]
    plant_segment_size: Mapping[Tuple[str, str, str], float]
    mine_segment_cost: Mapping[Tuple[str, str], float]
    plant_segment_cost: Mapping[Tuple[str, str, str], float]

    mine_operating_cost: Mapping[str, float]
    process_operating_cost: Mapping[Tuple[str, str], float]
    electricity_price: Mapping[Tuple[str, str], float]

    bauxite_transport: Mapping[Tuple[str, str], float]
    alumina_transport: Mapping[Tuple[str, str], float]
    aluminum_transport: Mapping[Tuple[str, str], float]

    aluminum_tariff: Mapping[Tuple[str, str], float] = field(default_factory=dict)
    alumina_tariff: Mapping[Tuple[str, str], float] = field(default_factory=dict)
    bauxite_levy: Mapping[Tuple[str, str, str], float] = field(default_factory=dict)
    alumina_levy: Mapping[Tuple[str, str], float] = field(default_factory=dict)

    capital_recovery_factor: float = 0.1174596248


def demo_data() -> AluminumData:
    """Return a small, internally consistent instance for smoke tests and examples.

    The demo is intentionally synthetic. It validates the Python model architecture
    without claiming to reproduce the complete historical dataset.
    """

    mines = ["mine-a"]
    plants = ["plant-a", "plant-b"]
    markets = ["market-a"]
    bauxites = ["tri-bauxite"]
    processes = ["refining", "smelting"]
    units = ["refinery", "smelter"]
    electricity_types = ["el-actual", "el-locost", "el-hicost"]
    segments = ["1", "2"]

    process_coeff = {
        ("tri-bauxite", "refining"): -2.0,
        ("alumina", "refining"): 1.0,
        ("alumina", "smelting"): -1.93,
        ("aluminum", "smelting"): 1.0,
        ("electr", "smelting"): -12.6,
    }

    return AluminumData(
        mines=mines,
        plants=plants,
        markets=markets,
        bauxites=bauxites,
        processes=processes,
        units=units,
        electricity_types=electricity_types,
        segments=segments,
        mine_bauxite={("mine-a", "tri-bauxite"): 1},
        process_coeff=process_coeff,
        unit_process={
            ("refinery", "refining"): 1.0,
            ("smelter", "smelting"): 1.0,
        },
        demand={"market-a": 120.0},
        nonmetal_bauxite={"mine-a": 0.0},
        nonmetal_alumina={"plant-a": 0.0, "plant-b": 0.0},
        mine_capacity={"mine-a": 300.0},
        mine_reserves={"mine-a": 10000.0},
        plant_capacity={
            ("plant-a", "refinery"): 250.0,
            ("plant-a", "smelter"): 0.0,
            ("plant-b", "refinery"): 0.0,
            ("plant-b", "smelter"): 150.0,
        },
        electricity_capacity={
            ("plant-a", "el-actual"): 0.0,
            ("plant-a", "el-locost"): 0.0,
            ("plant-a", "el-hicost"): 0.0,
            ("plant-b", "el-actual"): 2000.0,
            ("plant-b", "el-locost"): 500.0,
            ("plant-b", "el-hicost"): 1_000_000.0,
        },
        mine_utilization=0.90,
        unit_utilization={"refinery": 0.92, "smelter": 0.95},
        reserve_interval=20.0,
        mine_segment_size={
            ("mine-a", "1"): 0.0,
            ("mine-a", "2"): 200.0,
        },
        plant_segment_size={
            ("refinery", "1", "plant-a"): 0.0,
            ("refinery", "2", "plant-a"): 200.0,
            ("refinery", "1", "plant-b"): 0.0,
            ("refinery", "2", "plant-b"): 200.0,
            ("smelter", "1", "plant-a"): 0.0,
            ("smelter", "2", "plant-a"): 100.0,
            ("smelter", "1", "plant-b"): 0.0,
            ("smelter", "2", "plant-b"): 100.0,
        },
        mine_segment_cost={
            ("mine-a", "1"): 0.0,
            ("mine-a", "2"): 30.0,
        },
        plant_segment_cost={
            ("refinery", "1", "plant-a"): 0.0,
            ("refinery", "2", "plant-a"): 150.0,
            ("refinery", "1", "plant-b"): 0.0,
            ("refinery", "2", "plant-b"): 150.0,
            ("smelter", "1", "plant-a"): 0.0,
            ("smelter", "2", "plant-a"): 120.0,
            ("smelter", "1", "plant-b"): 0.0,
            ("smelter", "2", "plant-b"): 120.0,
        },
        mine_operating_cost={"mine-a": 18.0},
        process_operating_cost={
            ("plant-a", "refining"): 95.0,
            ("plant-a", "smelting"): 0.0,
            ("plant-b", "refining"): 0.0,
            ("plant-b", "smelting"): 560.0,
        },
        electricity_price={
            ("plant-a", "el-actual"): 0.0,
            ("plant-a", "el-locost"): 0.0,
            ("plant-a", "el-hicost"): 0.0,
            ("plant-b", "el-actual"): 20.0,
            ("plant-b", "el-locost"): 30.0,
            ("plant-b", "el-hicost"): 50.0,
        },
        bauxite_transport={("mine-a", "plant-a"): 12.0, ("mine-a", "plant-b"): 18.0},
        alumina_transport={
            ("plant-a", "plant-a"): 0.0,
            ("plant-a", "plant-b"): 20.0,
            ("plant-b", "plant-a"): 20.0,
            ("plant-b", "plant-b"): 0.0,
        },
        aluminum_transport={("plant-a", "market-a"): 35.0, ("plant-b", "market-a"): 25.0},
    )
