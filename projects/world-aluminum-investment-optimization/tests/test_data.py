from src.data import demo_data
from src.validation import validate_data


def test_demo_data_validates():
    validate_data(demo_data())
