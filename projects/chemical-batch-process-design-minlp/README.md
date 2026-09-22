# Chemical Batch Process Design MINLP

This repository contains a Pyomo implementation of a mixed-integer nonlinear programming (MINLP) model for the design of a multi-stage chemical batch process.

The model determines:

- the number of parallel units installed at each processing stage,
- the equipment volume required at each stage,
- the batch size assigned to each product,
- the product cycle times,
- and the minimum annualized equipment cost.

All numerical data in this repository are synthetic and intentionally differ from the classical reference instance that motivated the formulation. No real company, plant, or proprietary industrial dataset is represented.

## Model structure

The process contains two synthetic products and three generic processing stages:

- blender,
- converter,
- separator.

Each stage may operate with one, two, or three parallel units. Binary variables select exactly one parallel-unit configuration for every stage.

The continuous decision variables are represented in logarithmic form. This transformation preserves the structure of the classical convexified batch-design formulation while allowing nonlinear expressions such as production-time and equipment-cost relationships to be handled explicitly.

## Mathematical formulation

Let:

- `i` index products,
- `j` index processing stages,
- `k` index candidate numbers of parallel units.

The main transformed variables are:

- `log_volume[j]`: logarithm of stage volume,
- `log_batch[i]`: logarithm of product batch size,
- `log_cycle[i]`: logarithm of product cycle time,
- `log_units[j]`: logarithm of the selected number of parallel units,
- `y[k,j]`: binary configuration variable.

The main constraints are:

### Equipment volume requirement

For every product and stage,

```text
log_volume[j] >= log(size_factor[i,j]) + log_batch[i]
```

### Cycle-time requirement

```text
log_units[j] + log_cycle[i] >= log(processing_time[i,j])
```

### Production horizon

```text
sum_i demand[i] * exp(log_cycle[i] - log_batch[i]) <= horizon
```

### Parallel-unit selection

```text
log_units[j] = sum_k log(k) * y[k,j]
```

with

```text
sum_k y[k,j] = 1
```

for every stage.

### Objective

The model minimizes the annualized equipment cost:

```text
sum_j cost_coefficient[j]
      * exp(log_units[j] + cost_exponent[j] * log_volume[j])
```

## Corrections relative to a naive Pyomo translation

A nonlinear mixed-integer model cannot be solved directly with GLPK. GLPK is a linear/MILP solver and does not support the exponential nonlinear expressions used here.

This implementation instead uses Pyomo MindtPy with:

- HiGHS as the MILP solver,
- Ipopt as the NLP solver.

The binary variables are initialized to the three-unit design but are not fixed. This is important: an initial value is only a starting point, whereas fixing the binary variables would eliminate the discrete design decision.

The implementation also includes tight lower and upper bounds for batch sizes and cycle times, following the structure of the transformed formulation.

## Repository structure

```text
chemical-batch-process-design-minlp/
├── README.md
├── LICENSE.md
├── requirements.txt
├── batch_process_design.py
└── .gitignore
```

## Requirements

Python 3.10 or newer is recommended.

Python packages:

```bash
pip install -r requirements.txt
```

The model additionally requires an Ipopt executable available on the system path. HiGHS is provided through the `highspy` Python package.

You can verify solver availability from Python with:

```python
from pyomo.environ import SolverFactory

print(SolverFactory("highs").available(exception_flag=False))
print(SolverFactory("ipopt").available(exception_flag=False))
```

Both should return `True` before solving the model.

## Running the model

```bash
python batch_process_design.py
```

The script builds the MINLP, solves it with MindtPy using outer approximation, and reports:

- total equipment cost,
- selected parallel-unit count by stage,
- equipment volume by stage,
- product batch size,
- product cycle time.

## Notes on optimality

MindtPy is a decomposition framework for MINLP. The quality and guarantees of the final solution depend on the mathematical assumptions of the problem, the selected strategy, solver behavior, tolerances, and the properties of the nonlinear subproblems.

The repository is intended primarily as an educational and research example of process-design optimization rather than as production engineering software.

## References

The formulation is conceptually related to classical work on chemical batch-process design and mixed-integer nonlinear process synthesis, including work by Grossmann, Kocis, and collaborators. The numerical instance in this repository is independently defined and does not reproduce the original benchmark data.

## License

This project is available for educational, academic, and other non-commercial purposes only. Commercial use is prohibited. See `LICENSE.md` for the complete terms.
