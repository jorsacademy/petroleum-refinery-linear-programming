# World Aluminum Investment Optimization

A Python/Pyomo mixed-integer linear programming model for long-term aluminum industry planning. The model represents investment, mining, refining, smelting, electricity supply, transportation, tariffs, levies, and international trade decisions across multiple regions.

## Model scope

The optimization framework includes:

- bauxite mining and reserve limits
- refinery and smelter process balances
- mine, refinery, and smelter capacity expansion
- piecewise investment representation
- electricity supply limits and costs
- bauxite, alumina, and aluminum transportation
- tariffs and production or export levies
- regional trade restrictions
- non-metal bauxite and alumina demand
- aluminum market demand
- total system cost minimization

## Repository structure

```text
.
├── LICENSE.md
├── README.md
├── pyproject.toml
├── requirements.txt
├── main.py
├── src/
│   ├── __init__.py
│   ├── data.py
│   ├── mappings.py
│   ├── costs.py
│   ├── model.py
│   ├── reporting.py
│   └── validation.py
└── tests/
    ├── test_costs.py
    ├── test_data.py
    └── test_model.py
```

## Installation

Python 3.11 or newer is recommended.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

On Windows:

```bash
.venv\Scripts\activate
pip install -r requirements.txt
```

The model requires a MILP solver supported by Pyomo. HiGHS is the recommended open-source solver.

## Running the model

```bash
python main.py
```

## Modeling approach

The implementation uses indexed Pyomo sets, parameters, variables, constraints, and objective components to represent the aluminum production and trade network. Decision variables are restricted to valid commodity-location combinations wherever practical to reduce unnecessary model size.

The codebase separates data definitions, mappings, cost calculations, optimization logic, validation, and reporting so that scenarios and datasets can be modified without changing the mathematical model structure.

## Validation

The validation layer checks structural inconsistencies before solving, including:

- mine capacity without reserves
- production capacity without process mappings
- mines, plants, or markets without transport mappings
- missing electricity prices where electricity resources exist
- missing cost data for active production locations
- invalid tariff or levy mappings

## License

This project is source-available for personal, educational, academic, and non-commercial research use only. Commercial use is prohibited. See `LICENSE.md` for the complete terms.
