from pyomo.environ import value

from src.data import demo_data
from src.model import build_model


def test_model_builds_with_expected_objective():
    model = build_model(demo_data())
    assert model.objective.sense == 1
    assert model.total_cost_excluding_tariffs_and_levies is not None


def test_valid_bauxite_variable_exists():
    model = build_model(demo_data())
    assert ("tri-bauxite", "mine-a", "plant-a") in model.XM_INDEX
