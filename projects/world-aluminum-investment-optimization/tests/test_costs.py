from src.data import demo_data
from src.model import build_model


def test_cost_expressions_are_attached():
    model = build_model(demo_data())
    assert hasattr(model, "mine_operating_cost")
    assert hasattr(model, "transport_cost")
    assert hasattr(model, "total_cost")
