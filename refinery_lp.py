from __future__ import annotations

from dataclasses import dataclass

from pulp import (
    LpMaximize,
    LpProblem,
    LpStatus,
    LpVariable,
    PULP_CBC_CMD,
    lpSum,
    value,
)


CRUDE = ["Crude1", "Crude2", "Crude3"]
NAPHTHA = ["Naptha1", "Naptha2"]
RESID = ["Resid1", "Resid2"]
OIL = ["Oil1", "Oil2"]
REFORM_PROD = ["ReformProd1", "ReformProd2"]
CRACK_PROD = ["CrackProd1", "CrackProd2"]
PETROL = ["Petrol1", "Petrol2"]
FUEL = ["Fuel1", "Fuel2"]
LUBE = ["Lube1", "Lube2"]

DISTILL_NAPHTHA = {
    ("Crude1", "Naptha1"): 0.30,
    ("Crude1", "Naptha2"): 0.20,
    ("Crude2", "Naptha1"): 0.25,
    ("Crude2", "Naptha2"): 0.15,
    ("Crude3", "Naptha1"): 0.35,
    ("Crude3", "Naptha2"): 0.25,
}

DISTILL_OIL = {
    ("Crude1", "Oil1"): 0.40,
    ("Crude1", "Oil2"): 0.30,
    ("Crude2", "Oil1"): 0.30,
    ("Crude2", "Oil2"): 0.20,
    ("Crude3", "Oil1"): 0.50,
    ("Crude3", "Oil2"): 0.40,
}

DISTILL_RESID = {
    ("Crude1", "Resid1"): 0.20,
    ("Crude1", "Resid2"): 0.10,
    ("Crude2", "Resid1"): 0.15,
    ("Crude2", "Resid2"): 0.10,
    ("Crude3", "Resid1"): 0.25,
    ("Crude3", "Resid2"): 0.15,
}

REFORM_PROCESS = {
    ("Naptha1", "ReformProd1"): 0.50,
    ("Naptha1", "ReformProd2"): 0.30,
    ("Naptha2", "ReformProd1"): 0.40,
    ("Naptha2", "ReformProd2"): 0.20,
}

CRACK_PROCESS = {
    ("Oil1", "CrackProd1"): 0.40,
    ("Oil1", "CrackProd2"): 0.30,
    ("Oil2", "CrackProd1"): 0.30,
    ("Oil2", "CrackProd2"): 0.20,
}

LIM_DISTILL = 1000.0
LIM_REFORM = 500.0
LIM_CRACK = 700.0

LO_LUBE = {"Lube1": 100.0, "Lube2": 50.0}
UP_LUBE = {"Lube1": 200.0, "Lube2": 100.0}

PROFIT_PETROL = {"Petrol1": 10.0, "Petrol2": 8.0}
PROFIT_FUEL = {"Fuel1": 5.0, "Fuel2": 4.0}
PROFIT_LUBE = {"Lube1": 12.0, "Lube2": 10.0}


@dataclass
class RefineryVariables:
    crude: dict
    naphtha: dict
    naphtha_to_reformer: dict
    naphtha_to_petrol: dict
    reform_product: dict
    reform_to_petrol: dict
    oil: dict
    oil_to_cracker: dict
    oil_to_fuel: dict
    crack_product: dict
    crack_to_petrol: dict
    crack_to_fuel: dict
    resid: dict
    resid_to_lube: dict
    resid_to_fuel: dict
    final_petrol: dict
    final_fuel: dict
    final_lube: dict


def build_model() -> tuple[LpProblem, RefineryVariables]:
    model = LpProblem(name="Petroleum_Refinery_Linear_Programming", sense=LpMaximize)

    crude = {c: LpVariable(f"Cr_{c}", lowBound=0) for c in CRUDE}
    naphtha = {n: LpVariable(f"Nap_{n}", lowBound=0) for n in NAPHTHA}
    naphtha_to_reformer = {
        (n, rp): LpVariable(f"NapRef_{n}_{rp}", lowBound=0)
        for n in NAPHTHA
        for rp in REFORM_PROD
    }
    naphtha_to_petrol = {
        (n, p): LpVariable(f"NapBlend_{n}_{p}", lowBound=0)
        for n in NAPHTHA
        for p in PETROL
    }

    reform_product = {rp: LpVariable(f"Ref_{rp}", lowBound=0) for rp in REFORM_PROD}
    reform_to_petrol = {
        (rp, p): LpVariable(f"RefBlend_{rp}_{p}", lowBound=0)
        for rp in REFORM_PROD
        for p in PETROL
    }

    oil = {o: LpVariable(f"Oil_{o}", lowBound=0) for o in OIL}
    oil_to_cracker = {o: LpVariable(f"OilCrack_{o}", lowBound=0) for o in OIL}
    oil_to_fuel = {
        (o, f): LpVariable(f"OilBlend_{o}_{f}", lowBound=0)
        for o in OIL
        for f in FUEL
    }

    crack_product = {cp: LpVariable(f"Crk_{cp}", lowBound=0) for cp in CRACK_PROD}
    crack_to_petrol = {p: LpVariable(f"CrkPetrol_{p}", lowBound=0) for p in PETROL}
    crack_to_fuel = {f: LpVariable(f"CrkFuel_{f}", lowBound=0) for f in FUEL}

    resid = {r: LpVariable(f"Resid_{r}", lowBound=0) for r in RESID}
    resid_to_lube = {
        (r, l): LpVariable(f"ResidLube_{r}_{l}", lowBound=0)
        for r in RESID
        for l in LUBE
    }
    resid_to_fuel = {
        (r, f): LpVariable(f"ResidFuel_{r}_{f}", lowBound=0)
        for r in RESID
        for f in FUEL
    }

    final_petrol = {p: LpVariable(f"FinalPetrol_{p}", lowBound=0) for p in PETROL}
    final_fuel = {f: LpVariable(f"FinalFuel_{f}", lowBound=0) for f in FUEL}
    final_lube = {
        l: LpVariable(f"FinalLube_{l}", lowBound=LO_LUBE[l], upBound=UP_LUBE[l])
        for l in LUBE
    }

    variables = RefineryVariables(
        crude=crude,
        naphtha=naphtha,
        naphtha_to_reformer=naphtha_to_reformer,
        naphtha_to_petrol=naphtha_to_petrol,
        reform_product=reform_product,
        reform_to_petrol=reform_to_petrol,
        oil=oil,
        oil_to_cracker=oil_to_cracker,
        oil_to_fuel=oil_to_fuel,
        crack_product=crack_product,
        crack_to_petrol=crack_to_petrol,
        crack_to_fuel=crack_to_fuel,
        resid=resid,
        resid_to_lube=resid_to_lube,
        resid_to_fuel=resid_to_fuel,
        final_petrol=final_petrol,
        final_fuel=final_fuel,
        final_lube=final_lube,
    )

    model += (
        lpSum(PROFIT_FUEL[f] * final_fuel[f] for f in FUEL)
        + lpSum(PROFIT_PETROL[p] * final_petrol[p] for p in PETROL)
        + lpSum(PROFIT_LUBE[l] * final_lube[l] for l in LUBE)
    ), "Total_Product_Value"

    model += lpSum(crude[c] for c in CRUDE) <= LIM_DISTILL, "Distillation_Capacity"

    for n in NAPHTHA:
        model += (
            naphtha[n] == lpSum(DISTILL_NAPHTHA[c, n] * crude[c] for c in CRUDE)
        ), f"Naphtha_Production_{n}"

    for o in OIL:
        model += (
            oil[o] == lpSum(DISTILL_OIL[c, o] * crude[c] for c in CRUDE)
        ), f"Oil_Production_{o}"

    for r in RESID:
        model += (
            resid[r] == lpSum(DISTILL_RESID[c, r] * crude[c] for c in CRUDE)
        ), f"Resid_Production_{r}"

    for n in NAPHTHA:
        model += (
            lpSum(naphtha_to_reformer[n, rp] for rp in REFORM_PROD)
            + lpSum(naphtha_to_petrol[n, p] for p in PETROL)
            == naphtha[n]
        ), f"Naphtha_Balance_{n}"

    model += (
        lpSum(naphtha_to_reformer[n, rp] for n in NAPHTHA for rp in REFORM_PROD)
        <= LIM_REFORM
    ), "Reformer_Capacity"

    for rp in REFORM_PROD:
        model += (
            reform_product[rp]
            == lpSum(REFORM_PROCESS[n, rp] * naphtha_to_reformer[n, rp] for n in NAPHTHA)
        ), f"Reformer_Output_{rp}"
        model += (
            lpSum(reform_to_petrol[rp, p] for p in PETROL) == reform_product[rp]
        ), f"Reformer_Balance_{rp}"

    for o in OIL:
        model += (
            oil_to_cracker[o] + lpSum(oil_to_fuel[o, f] for f in FUEL) == oil[o]
        ), f"Oil_Balance_{o}"

    model += lpSum(oil_to_cracker[o] for o in OIL) <= LIM_CRACK, "Cracker_Capacity"

    for cp in CRACK_PROD:
        model += (
            crack_product[cp]
            == lpSum(CRACK_PROCESS[o, cp] * oil_to_cracker[o] for o in OIL)
        ), f"Cracker_Output_{cp}"

    model += (
        lpSum(crack_to_petrol[p] for p in PETROL) == crack_product["CrackProd1"]
    ), "Crack_Product1_Allocation"
    model += (
        lpSum(crack_to_fuel[f] for f in FUEL) == crack_product["CrackProd2"]
    ), "Crack_Product2_Allocation"

    for r in RESID:
        model += (
            lpSum(resid_to_lube[r, l] for l in LUBE)
            + lpSum(resid_to_fuel[r, f] for f in FUEL)
            == resid[r]
        ), f"Resid_Balance_{r}"

    for p in PETROL:
        model += (
            final_petrol[p]
            == lpSum(naphtha_to_petrol[n, p] for n in NAPHTHA)
            + lpSum(reform_to_petrol[rp, p] for rp in REFORM_PROD)
            + crack_to_petrol[p]
        ), f"Final_Petrol_{p}"

    for f in FUEL:
        model += (
            final_fuel[f]
            == lpSum(oil_to_fuel[o, f] for o in OIL)
            + crack_to_fuel[f]
            + lpSum(resid_to_fuel[r, f] for r in RESID)
        ), f"Final_Fuel_{f}"

    for l in LUBE:
        model += (
            final_lube[l] == lpSum(resid_to_lube[r, l] for r in RESID)
        ), f"Final_Lube_{l}"

    return model, variables


def solve_model(msg: bool = False) -> tuple[LpProblem, RefineryVariables]:
    model, variables = build_model()
    status = model.solve(PULP_CBC_CMD(msg=msg))

    if LpStatus[status] != "Optimal":
        raise RuntimeError(f"Optimization failed with status: {LpStatus[status]}")

    return model, variables


def print_solution(model: LpProblem) -> None:
    print(f"Solver status: {LpStatus[model.status]}")
    print(f"Maximum objective value: {value(model.objective):,.2f}")
    for var in model.variables():
        print(f"{var.name}: {var.value():.4f}")


if __name__ == "__main__":
    solved_model, _ = solve_model(msg=False)
    print_solution(solved_model)
