import math

from pulp import LpStatus, value

from refinery_lp import (
    FUEL,
    LIM_CRACK,
    LIM_DISTILL,
    LIM_REFORM,
    LUBE,
    NAPHTHA,
    OIL,
    PETROL,
    REFORM_PROD,
    RESID,
    LO_LUBE,
    UP_LUBE,
    solve_model,
)


def test_model_solves_to_optimality():
    model, _ = solve_model(msg=False)
    assert LpStatus[model.status] == "Optimal"
    assert math.isfinite(value(model.objective))


def test_distillation_capacity_is_respected():
    _, v = solve_model(msg=False)
    total_crude = sum(var.value() for var in v.crude.values())
    assert total_crude <= LIM_DISTILL + 1e-6


def test_global_reformer_capacity_is_respected():
    _, v = solve_model(msg=False)
    total_reformer_feed = sum(var.value() for var in v.naphtha_to_reformer.values())
    assert total_reformer_feed <= LIM_REFORM + 1e-6


def test_global_cracker_capacity_is_respected():
    _, v = solve_model(msg=False)
    total_cracker_feed = sum(v.oil_to_cracker[o].value() for o in OIL)
    assert total_cracker_feed <= LIM_CRACK + 1e-6


def test_naphtha_balances_close():
    _, v = solve_model(msg=False)
    for n in NAPHTHA:
        used = sum(v.naphtha_to_reformer[n, rp].value() for rp in REFORM_PROD)
        used += sum(v.naphtha_to_petrol[n, p].value() for p in PETROL)
        assert abs(used - v.naphtha[n].value()) <= 1e-6


def test_oil_balances_close():
    _, v = solve_model(msg=False)
    for o in OIL:
        used = v.oil_to_cracker[o].value()
        used += sum(v.oil_to_fuel[o, f].value() for f in FUEL)
        assert abs(used - v.oil[o].value()) <= 1e-6


def test_residue_balances_close():
    _, v = solve_model(msg=False)
    for r in RESID:
        used = sum(v.resid_to_lube[r, l].value() for l in LUBE)
        used += sum(v.resid_to_fuel[r, f].value() for f in FUEL)
        assert abs(used - v.resid[r].value()) <= 1e-6


def test_final_petrol_is_linked_to_component_flows():
    _, v = solve_model(msg=False)
    for p in PETROL:
        components = sum(v.naphtha_to_petrol[n, p].value() for n in NAPHTHA)
        components += sum(v.reform_to_petrol[rp, p].value() for rp in REFORM_PROD)
        components += v.crack_to_petrol[p].value()
        assert abs(components - v.final_petrol[p].value()) <= 1e-6


def test_final_fuel_is_linked_to_component_flows():
    _, v = solve_model(msg=False)
    for f in FUEL:
        components = sum(v.oil_to_fuel[o, f].value() for o in OIL)
        components += v.crack_to_fuel[f].value()
        components += sum(v.resid_to_fuel[r, f].value() for r in RESID)
        assert abs(components - v.final_fuel[f].value()) <= 1e-6


def test_lubricant_bounds_apply_to_final_products():
    _, v = solve_model(msg=False)
    for l in LUBE:
        produced = v.final_lube[l].value()
        assert LO_LUBE[l] - 1e-6 <= produced <= UP_LUBE[l] + 1e-6
        components = sum(v.resid_to_lube[r, l].value() for r in RESID)
        assert abs(components - produced) <= 1e-6
