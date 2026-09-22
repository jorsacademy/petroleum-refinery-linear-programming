# Oil Refinery Optimization with PuLP

A linear programming model for refinery production planning and blending, implemented in Python with [PuLP](https://coin-or.github.io/pulp/).

The model selects crude-oil processing quantities and allocates intermediate streams through distillation, reforming, cracking, blending, and lubricant production to maximize total product margin subject to process capacities and product-quality requirements.

## Model scope

The formulation includes:

- Three crude-oil feeds: Arabian Light, Brent, and WTI
- Distillation into naphtha, oil, and residue streams
- Naphtha reforming into higher-octane blend components
- Oil cracking into cracked gas and cracked oil
- Residue processing into light and heavy lubricants
- Premium and regular motor-fuel blending
- Jet-fuel and fuel-oil blending
- Distillation, reforming, and cracking capacity limits
- Petrol octane constraints
- Jet-fuel vapor-pressure constraint
- Lubricant production bounds
- Profit maximization

## Important corrections from the legacy formulation

This repository contains a cleaned and corrected version of an older refinery LP model.

### 1. Fuel-oil blend ratios

The legacy formulation applied all oil, residue, and cracked-oil ratios directly to total fuel-oil production. Those coefficients summed to 2.15, which was incompatible with the final fuel-oil material balance and could force fuel-oil production to zero.

The corrected formulation treats the supplied oil and residue coefficients as ratios within their respective component groups, while retaining the cracked-oil requirement as a share of total fuel oil.

### 2. Reforming and lubricant-process yields

The legacy formulation used separate process-input variables for individual reformer and lubricant outputs. That structure could effectively duplicate feed allocation across co-products.

The corrected model uses one process-input variable per feed stream. Each processed feed simultaneously generates all specified co-products according to the corresponding yield coefficients, consistent with the cracking formulation.

### 3. Solver and reporting safeguards

The model now:

- uses an explicit CBC solver configuration,
- separates model construction from execution,
- checks that an optimal solution was obtained before reporting values,
- removes unused third-party imports, and
- uses clearer variable names and organized data sections.

## Installation

Python 3.9+ is recommended.

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Run

```bash
python oil_refinery_optimization.py
```

The script prints the optimization status, optimal total margin, crude-oil processing plan, final-product quantities, and utilization of the main refinery units.

## Main formulation

The objective is to maximize total contribution margin from final products:

```text
maximize
    fuel margin
  + petrol margin
  + lubricant margin
```

subject to material balances, process yields, capacity constraints, blending relationships, octane limits, vapor-pressure limits, and lubricant bounds.

## Notes

The numerical values in this repository are illustrative sample data. The model should therefore be treated as an optimization example rather than a calibrated representation of a specific refinery.

Product margins are modeled as contribution margins; explicit crude purchase costs and process operating costs are not included in the current dataset. These can be added directly to the objective if such data are available.

## Files

- `oil_refinery_optimization.py` — optimization model and reporting logic
- `requirements.txt` — Python dependency
- `.gitignore` — Python and solver-generated artifacts
