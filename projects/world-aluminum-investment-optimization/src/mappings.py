"""Mapping helpers for valid model combinations."""

from __future__ import annotations

from .data import AluminumData


def valid_bauxite_shipments(data: AluminumData):
    return [
        (bauxite, mine, plant)
        for mine in data.mines
        for bauxite in data.bauxites
        if data.mine_bauxite.get((mine, bauxite), 0)
        for plant in data.plants
    ]


def valid_processes_at_plant(data: AluminumData):
    active_units = {
        (unit, process)
        for unit in data.units
        for process in data.processes
        if data.unit_process.get((unit, process), 0.0) != 0.0
    }
    active_processes = {process for _, process in active_units}
    return [(process, plant) for process in active_processes for plant in data.plants]


def valid_unit_process_pairs(data: AluminumData):
    return [
        (unit, process)
        for unit in data.units
        for process in data.processes
        if data.unit_process.get((unit, process), 0.0) != 0.0
    ]
