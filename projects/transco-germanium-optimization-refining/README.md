# Transco Germanium Optimization Refining

A linear programming model for the Transco germanium refining and reheating problem.

The original Turkish problem asks for a **DP (Doğrusal Programlama)** model, i.e. a **Linear Programming (LP)** model. This repository minimizes monthly processing cost while meeting transistor-quality demands.

## Problem data

Initial melting costs per transistor-equivalent:

- Method 1: 50 TL
- Method 2: 70 TL
- Reheating: 25 TL per unit reheated

Initial melting quality distribution:

| Quality | Method 1 | Method 2 |
|---|---:|---:|
| Defective | 30% | 20% |
| Quality 1 | 30% | 20% |
| Quality 2 | 20% | 25% |
| Quality 3 | 15% | 20% |
| Quality 4 | 5% | 15% |

Reheating transition distribution. Columns are the quality sent into reheating; rows are the quality obtained afterward.

| Final quality | Defective input | Q1 input | Q2 input | Q3 input |
|---|---:|---:|---:|---:|
| Defective | 30% | 0% | 0% | 0% |
| Quality 1 | 25% | 30% | 0% | 0% |
| Quality 2 | 15% | 30% | 40% | 0% |
| Quality 3 | 20% | 20% | 30% | 50% |
| Quality 4 | 10% | 20% | 30% | 50% |

Monthly demand:

- Quality 1: 3,000
- Quality 2: 3,000
- Quality 3: 2,000
- Quality 4: 1,000

Initial production is limited to at most 20,000 units per month.

## Mathematical model

Decision variables:

- `x1`, `x2`: quantity initially melted using methods 1 and 2.
- `v0`, `v1`, `v2`, `v3`: quantities of defective, Q1, Q2, and Q3 germanium sent to reheating.

Objective:

```text
min 50*x1 + 70*x2 + 25*(v0 + v1 + v2 + v3)
```

Subject to:

1. Reheated material cannot exceed the quantity initially produced in its source quality.
2. `x1 + x2 <= 20000`.
3. Final amounts of qualities 1 through 4 must meet their respective demands.
4. All decision variables are nonnegative.

The code constructs these constraints directly and solves the LP with SciPy's HiGHS solver.

## Optimal solution

Using the supplied data, the continuous LP optimum is approximately:

```text
Method 1 initial melting : 10563.380
Method 2 initial melting :     0.000
Total initial production : 10563.380

Reheated defective       : 3169.014
Reheated quality 1       : 1373.239
Reheated quality 2       :    0.000
Reheated quality 3       :    0.000

Minimum monthly cost     : 641725.35 TL
```

Final quality quantities are approximately:

```text
Defective :  950.704
Quality 1 : 3000.000
Quality 2 : 3000.000
Quality 3 : 2492.958
Quality 4 : 1119.718
```

All required demands are met. The excess quantities in qualities 3 and 4 arise from the fixed probabilistic yield distributions.

Because the source problem is formulated using percentages, the model uses continuous variables. If individual transistor counts must be integral, a mixed-integer version should be used instead.

## Run

```bash
python -m pip install -r requirements.txt
python transco_optimization.py
```

## License

Licensed under the **PolyForm Noncommercial License 1.0.0**. Commercial use is not permitted under that license. See `LICENSE` for the terms.
