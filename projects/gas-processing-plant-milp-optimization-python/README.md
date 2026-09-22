# Gas Processing Plant MILP Optimization in Python

Educational mixed-integer linear programming model for daily gas-processing plant planning.

The model selects one processing mode, allocates feed from multiple sources, computes recoverable products, determines sales and ending inventory, and maximizes daily operating profit.

## Model structure

Decision layers:

- feed allocation by source and processing mode;
- binary processing-mode selection;
- product production;
- product sales;
- ending inventory.

The formulation avoids a loose Big-M recovery linearization by disaggregating feed variables by operating mode.

## Material flow

The model explicitly closes the simplified material balance:

```text
feed -> recovered NGL + condensate + sales gas + fuel + flare/loss
```

Sales Gas is defined by equality rather than a lower bound.

For each product:

```text
production + initial inventory = sales + ending inventory
```

Market limits therefore apply to actual sales, not directly to production.

## Objective

Maximize:

```text
sales revenue
- feed cost
- processing-mode operating cost
- ending-inventory holding cost
```

All flow quantities are intentionally treated as common abstract flow units in this educational model. The economic coefficients should therefore be interpreted as internally consistent example data rather than calibrated plant economics.

## Reference solution

With the bundled data, SciPy/HiGHS returns:

- status: `OPTIMAL`
- active mode: `Low_Recovery`
- daily profit: approximately `3099.23`
- total feed: approximately `1136.36`

Reference feed allocation:

| Source | Flow |
|---|---:|
| Offshore Field A | 450.000 |
| Offshore Field B | 232.973 |
| Onshore Field C | 320.000 |
| Associated Gas D | 133.391 |

## Independent mode check

The test suite fixes each binary processing mode separately and solves the resulting model. The best fixed-mode solve must match the MILP mode and objective.

Reference fixed-mode profits are approximately:

| Mode | Profit/day |
|---|---:|
| High Recovery | -3716.58 |
| Standard | 856.37 |
| Low Recovery | 3099.23 |

This is a useful implementation check; it does not make the simplified plant physics industrially calibrated.

## Validation

Tests check:

- MILP optimal status and reference objective;
- Sales Gas mass balance;
- product inventory balances;
- source and total processing capacities;
- inventory safety-stock/storage bounds;
- MILP agreement with fixed-mode solves.

Run:

```bash
python -m unittest discover -s tests -v
```

## Usage

```python
from gas_plant_milp_optimization import GasPlantMILP

model = GasPlantMILP()
result = model.solve()

print(result.status)
print(result.active_mode)
print(result.objective_profit)
print(result.feed)
print(result.production)
```

## Requirements

- Python 3.10+
- NumPy
- SciPy

## Scope and limitations

This repository is an educational planning model, not a process simulator. It does not represent rigorous thermodynamics, pressure/temperature dependent phase equilibria, detailed sulfur chemistry, compressor curves, pipeline hydraulics, or multi-period startup/shutdown dynamics.

MILP dual values are not reported as economic shadow prices. Sensitivity analysis should instead be performed on a suitable LP with integer decisions fixed, or by explicit parameter perturbation.
