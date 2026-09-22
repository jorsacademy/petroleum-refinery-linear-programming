# Mathematical Model

## Sets

Let:

- \(N\) be the set of nodes.
- \(S \subset N\) be the set of crude-oil production fields.
- \(R \subset N\) be the set of refinery nodes.
- \(J \subset N\) be the set of intermediate junctions.
- \(A \subseteq N \times N\) be the set of candidate directed pipeline segments.
- \(P \subseteq J\) be the set of candidate pumping-station locations.

## Parameters

For each source node \(i \in S\):

- \(s_i\): available crude-oil production, in kbbl/day.

For each refinery node \(r \in R\):

- \(d_r\): required crude-oil intake, in kbbl/day.

For each candidate pipeline \((i,j) \in A\):

- \(u_{ij}\): pipeline capacity, in kbbl/day.
- \(F_{ij}\): annualized fixed construction cost, in million USD/year.
- \(c_{ij}\): variable transport cost coefficient, expressed as million USD/year per kbbl/day of sustained flow after annual conversion.
- \(e_{ij}\): environmental exposure penalty, in million USD/year.
- \(g_{ij}\): regulatory crossing cost, in million USD/year.
- \(h_{ij}\in\{0,1\}\): prohibition indicator; 1 means the right-of-way cannot be selected.

For each pumping-station candidate \(p \in P\):

- \(U_p\): station throughput capacity, in kbbl/day.
- \(K_p\): annualized fixed pumping-station cost, in million USD/year.

The CSV input stores variable transport cost in thousand USD per kbbl transported. The implementation converts this coefficient into an annualized million-USD expression by multiplying sustained daily flow by 365 and dividing by 1000.

## Decision variables

For each \((i,j) \in A\):

- \(x_{ij} \ge 0\): crude-oil flow on candidate pipeline \((i,j)\), in kbbl/day.
- \(y_{ij}\in\{0,1\}\): 1 if candidate pipeline \((i,j)\) is constructed, 0 otherwise.

For each \(p \in P\):

- \(z_p\in\{0,1\}\): 1 if the pumping station at node \(p\) is activated, 0 otherwise.

## Objective function

The objective minimizes annualized fixed pipeline cost, annualized variable transport cost, environmental exposure cost, regulatory crossing cost, and pumping-station fixed cost:

\[
\min Z =
\sum_{(i,j)\in A}\left(F_{ij}+e_{ij}+g_{ij}\right)y_{ij}
+
\sum_{(i,j)\in A}\left(\frac{365}{1000}c_{ij}\right)x_{ij}
+
\sum_{p\in P}K_p z_p.
\]

This is a monetized single-objective formulation. Environmental and regulatory terms are treated as annualized planning penalties rather than physical damage estimates.

## Constraints

### 1. Source production balance

All available production from each field must enter the network:

\[
\sum_{j:(i,j)\in A}x_{ij}
-
\sum_{j:(j,i)\in A}x_{ji}
=
s_i,
\qquad \forall i\in S.
\]

### 2. Refinery demand balance

Each refinery must receive its required crude-oil intake:

\[
\sum_{i:(i,r)\in A}x_{ir}
-
\sum_{j:(r,j)\in A}x_{rj}
=
d_r,
\qquad \forall r\in R.
\]

### 3. Flow conservation at junctions

No crude oil is created, destroyed, or stored at an intermediate junction:

\[
\sum_{i:(i,j)\in A}x_{ij}
=
\sum_{k:(j,k)\in A}x_{jk},
\qquad \forall j\in J.
\]

### 4. Pipeline capacity and build linking

Positive flow is permitted only when the corresponding pipeline is constructed:

\[
0\le x_{ij}\le u_{ij}y_{ij},
\qquad \forall (i,j)\in A.
\]

This constraint eliminates the zero-cost logical error that occurs when flow variables are not linked to binary pipeline-construction variables.

### 5. Prohibited rights-of-way

Candidate segments marked as prohibited cannot be selected:

\[
y_{ij}\le 1-h_{ij},
\qquad \forall(i,j)\in A.
\]

### 6. Pumping-station throughput

For a candidate pumping node, total outbound flow may not exceed the installed station capacity:

\[
\sum_{j:(p,j)\in A}x_{pj}
\le
U_p z_p,
\qquad \forall p\in P.
\]

Thus, any positive throughput through a candidate pumping node forces the corresponding station to be active.

### 7. Pump-station relevance

To avoid activating an unused pumping station, activation is bounded by adjacent selected outbound infrastructure:

\[
z_p\le\sum_{j:(p,j)\in A}y_{pj},
\qquad \forall p\in P.
\]

Together with the throughput constraint and positive fixed station cost, this keeps pumping-station decisions logically consistent.

## Feasibility condition for this instance

The synthetic instance is constructed so that total production equals total refinery demand:

\[
\sum_{i\in S}s_i=95+80+65=240\text{ kbbl/day},
\]

and

\[
\sum_{r\in R}d_r=240\text{ kbbl/day}.
\]

The candidate network contains sufficient non-prohibited aggregate capacity to transport the full 240 kbbl/day while respecting pumping-station capacities.

## Model class

The resulting optimization problem is a mixed-integer linear program (MILP). The binary variables represent discrete infrastructure investment decisions, while continuous variables represent pipeline flows.
