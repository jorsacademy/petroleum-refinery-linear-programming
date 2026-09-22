# Crude Oil Pipeline Network Optimization

This repository contains a synthetic operations research case study for planning a crude-oil pipeline network. The model is formulated as a mixed-integer linear program (MILP) and solved with PuLP.

The case is intentionally fictional. All fields, junctions, pumping stations, environmental zones, and refinery names are synthetic. No real company, private operator, public authority, or proprietary dataset is represented.

## Problem scope

The model determines:

- which candidate pipeline segments should be constructed,
- how much crude oil should flow through each selected segment,
- which pumping stations should be activated,
- how to satisfy refinery demand from multiple production fields,
- how to respect pipeline and pumping capacities,
- how to avoid prohibited rights-of-way,
- how to account for construction cost, pumping cost, environmental exposure, and regulatory crossing cost.

The objective is to minimize total annualized system cost while maintaining a feasible transport network.

## Repository structure

```text
.
├── README.md
├── LICENSE.md
├── requirements.txt
├── .gitignore
├── data/
│   ├── nodes.csv
│   └── candidate_pipelines.csv
├── docs/
│   └── mathematical_model.md
└── src/
    └── oil_pipeline_optimization.py
```

## Model units

- Flow: thousand barrels per day (kbbl/day)
- Distance: km
- Fixed pipeline cost: million USD per year, annualized
- Variable transport cost: thousand USD per kbbl transported
- Pumping-station fixed cost: million USD per year, annualized
- Environmental penalty: million USD-equivalent per year
- Regulatory crossing cost: million USD per year

The numerical values are synthetic but internally consistent for teaching and research purposes.

## Installation

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Run

```bash
python src/oil_pipeline_optimization.py
```

The script loads the CSV data, validates the instance, solves the MILP, prints the selected network and flows, and performs post-solution consistency checks.

## Mathematical formulation

See `docs/mathematical_model.md` for the full notation, objective function, and constraints.

## License

This repository is source-available for non-commercial educational, research, and personal use only. Commercial use is prohibited without prior written permission. See `LICENSE.md`.
