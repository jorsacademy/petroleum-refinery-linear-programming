# Process Systems and Industrial Process Optimization Research Series

This file maps repositories related to process systems, production-process optimization, and industrial control. It is an index only: each repository remains independent because the underlying process model and optimization paradigm differ.

## Refinery and process-network optimization

- `petroleum-refinery-linear-programming` — corrected refinery LP emphasizing material balances, process capacities, and modeling discipline.
- `oil-refinery-optimization-pulp` — richer refinery blending model with octane, vapor-pressure, and product-quality constraints.
- `gas-processing-plant-milp-optimization-python` — gas-processing plant optimization with a different process-network structure.
- `transco-germanium-optimization-refining` — refining/process allocation in a distinct industrial setting.

The two refinery repositories should remain separate: one is a transparent corrected LP centered on structural modeling issues, while the other adds more detailed product-quality constraints and blending logic.

## Process design and nonlinear optimization

- `chemical-batch-process-design-minlp` — process design with mixed-integer nonlinear structure.
- `cantilever-beam-design-optimization` — not a process plant model, but a related engineering-design optimization example.
- `adaptive-cooling-metal-fabrication-optimization` — adaptive industrial-process parameter optimization.

## Black-box and Bayesian process optimization

- `constrained-bayesian-optimization-chemical-process-python` — expensive constrained process optimization through Bayesian optimization.
- `processoptimizer-industrial-process-optimization` — industrial process tuning through a black-box/sequential optimization toolkit.
- `smac3-simulation-based-optimization` — model-based black-box optimization applicable to expensive process/simulation settings.
- `sambo-sequential-model-based-optimization` — sequential model-based optimization in the same broader family.

## Dynamic control and learning

- `offline-rl-industrial-process-control` — policy learning from logged process-control data.
- `industrial-energy-management-sac` — continuous-control reinforcement learning in an industrial energy setting.
- `production-control-with-mpc-vs-rl` — direct comparison between model-based predictive control and reinforcement learning.
- `safe-rl-constrained-production-control` — constrained/safe reinforcement learning for production control.

## Simulation and digital-twin bridge

- `manufacturing-discrete-event-simulation-optimization-python` — simulation-driven optimization.
- `simulation-model-calibration-uq` — calibration and uncertainty quantification for simulation models.
- `industrial-digital-twin-system-optimization-python` — optimization around a digital-twin workflow.
- `dynamic-manufacturing-digital-twin-rl` — closed-loop/dynamic control with reinforcement learning in a digital-twin context.

## Portfolio rule

Process applications should not be merged merely because they share industrial vocabulary. A refinery LP, a MINLP process-design model, a Bayesian optimization experiment, and an RL control problem differ fundamentally in mathematical structure, information flow, and validation criteria. Cross-linking is useful; forced consolidation is not.
