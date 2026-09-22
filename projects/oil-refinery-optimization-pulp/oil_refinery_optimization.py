import pulp

# -----------------------------
# Sets
# -----------------------------
CRUDE = ["Arabian_Light", "Brent", "WTI"]
NAPHTHA = ["Light_Naptha", "Heavy_Naptha"]
RESID = ["Light_Resid", "Heavy_Resid"]
OIL = ["Light_Oil", "Medium_Oil", "Heavy_Oil"]
REFORM_PRODUCTS = ["High_Octane", "Medium_Octane"]
CRACK_PRODUCTS = ["CG", "CO"]  # Cracked Gas, Cracked Oil
PETROL = ["PMF", "RMF"]        # Premium Motor Fuel, Regular Motor Fuel
FUEL = ["JF", "FO"]            # Jet Fuel, Fuel Oil
LUBE = ["Light_Lube", "Heavy_Lube"]

# -----------------------------
# Data
# -----------------------------
DISTILL_NAPHTHA = {
    ("Arabian_Light", "Light_Naptha"): 0.12,
    ("Arabian_Light", "Heavy_Naptha"): 0.08,
    ("Brent", "Light_Naptha"): 0.10,
    ("Brent", "Heavy_Naptha"): 0.09,
    ("WTI", "Light_Naptha"): 0.14,
    ("WTI", "Heavy_Naptha"): 0.07,
}

DISTILL_OIL = {
    ("Arabian_Light", "Light_Oil"): 0.15,
    ("Arabian_Light", "Medium_Oil"): 0.20,
    ("Arabian_Light", "Heavy_Oil"): 0.12,
    ("Brent", "Light_Oil"): 0.18,
    ("Brent", "Medium_Oil"): 0.18,
    ("Brent", "Heavy_Oil"): 0.10,
    ("WTI", "Light_Oil"): 0.20,
    ("WTI", "Medium_Oil"): 0.15,
    ("WTI", "Heavy_Oil"): 0.08,
}

DISTILL_RESID = {
    ("Arabian_Light", "Light_Resid"): 0.18,
    ("Arabian_Light", "Heavy_Resid"): 0.15,
    ("Brent", "Light_Resid"): 0.20,
    ("Brent", "Heavy_Resid"): 0.15,
    ("WTI", "Light_Resid"): 0.21,
    ("WTI", "Heavy_Resid"): 0.15,
}

RESID_PROCESS = {
    ("Light_Resid", "Light_Lube"): 0.6,
    ("Light_Resid", "Heavy_Lube"): 0.3,
    ("Heavy_Resid", "Light_Lube"): 0.4,
    ("Heavy_Resid", "Heavy_Lube"): 0.5,
}

REFORM_PROCESS = {
    ("Light_Naptha", "High_Octane"): 0.7,
    ("Light_Naptha", "Medium_Octane"): 0.25,
    ("Heavy_Naptha", "High_Octane"): 0.6,
    ("Heavy_Naptha", "Medium_Octane"): 0.35,
}

CRACK_PROCESS = {
    ("Light_Oil", "CG"): 0.3,
    ("Light_Oil", "CO"): 0.65,
    ("Medium_Oil", "CG"): 0.25,
    ("Medium_Oil", "CO"): 0.70,
    ("Heavy_Oil", "CG"): 0.20,
    ("Heavy_Oil", "CO"): 0.75,
}

VAPOR_OIL = {"Light_Oil": 8.5, "Medium_Oil": 6.2, "Heavy_Oil": 4.1}
VAPOR_RESID = {"Light_Resid": 3.2, "Heavy_Resid": 2.1}
VAPOR_CRACKED_OIL = 7.8
MAX_VAPOR_JF = 5.5

MAX_CRUDE = {"Arabian_Light": 5000, "Brent": 4000, "WTI": 3500}
MAX_DISTILL = 10000
MAX_REFORM = 2000
MAX_CRACK = 1800

MIN_LUBE = {"Light_Lube": 100, "Heavy_Lube": 150}
MAX_LUBE = {"Light_Lube": 800, "Heavy_Lube": 1200}

OCTANE_NAPHTHA = {"Light_Naptha": 65, "Heavy_Naptha": 70}
OCTANE_REFORM = {"High_Octane": 95, "Medium_Octane": 87}
OCTANE_CG = 92
MIN_OCTANE = {"PMF": 91, "RMF": 87}
MIN_PMF_TO_RMF_RATIO = 0.4

# These are within-group blend ratios, not shares of total fuel oil.
FO_OIL_RATIO = {"Light_Oil": 0.3, "Medium_Oil": 0.5, "Heavy_Oil": 0.2}
FO_CRACKED_OIL_SHARE = 0.15
FO_RESID_RATIO = {"Light_Resid": 0.6, "Heavy_Resid": 0.4}

PROFIT_PETROL = {"PMF": 45, "RMF": 38}
PROFIT_FUEL = {"JF": 42, "FO": 28}
PROFIT_LUBE = {"Light_Lube": 85, "Heavy_Lube": 95}


def build_model():
    model = pulp.LpProblem("Oil_Refinery_Optimization", pulp.LpMaximize)

    crude = {
        c: pulp.LpVariable(f"Cr_{c}", lowBound=0, upBound=MAX_CRUDE[c])
        for c in CRUDE
    }

    naphtha = pulp.LpVariable.dicts("Naphtha", NAPHTHA, lowBound=0)
    oil = pulp.LpVariable.dicts("Oil", OIL, lowBound=0)
    resid = pulp.LpVariable.dicts("Resid", RESID, lowBound=0)

    naphtha_to_reformer = pulp.LpVariable.dicts("NaphthaToReformer", NAPHTHA, lowBound=0)
    oil_to_cracker = pulp.LpVariable.dicts("OilToCracker", OIL, lowBound=0)
    resid_to_lube = pulp.LpVariable.dicts("ResidToLube", RESID, lowBound=0)

    naphtha_to_petrol = pulp.LpVariable.dicts(
        "NaphthaToPetrol", [(n, p) for n in NAPHTHA for p in PETROL], lowBound=0
    )
    reform_to_petrol = pulp.LpVariable.dicts(
        "ReformToPetrol", [(r, p) for r in REFORM_PRODUCTS for p in PETROL], lowBound=0
    )
    oil_to_fuel = pulp.LpVariable.dicts(
        "OilToFuel", [(o, f) for o in OIL for f in FUEL], lowBound=0
    )
    resid_to_fuel = pulp.LpVariable.dicts(
        "ResidToFuel", [(r, f) for r in RESID for f in FUEL], lowBound=0
    )

    reform = pulp.LpVariable.dicts("Reform", REFORM_PRODUCTS, lowBound=0)
    cracked = pulp.LpVariable.dicts("Cracked", CRACK_PRODUCTS, lowBound=0)
    cracked_gas_to_petrol = pulp.LpVariable.dicts("CrackedGasToPetrol", PETROL, lowBound=0)
    cracked_oil_to_fuel = pulp.LpVariable.dicts("CrackedOilToFuel", FUEL, lowBound=0)

    fuel_prod = pulp.LpVariable.dicts("FuelProd", FUEL, lowBound=0)
    petrol_prod = pulp.LpVariable.dicts("PetrolProd", PETROL, lowBound=0)
    lube_prod = {
        l: pulp.LpVariable(f"LubeProd_{l}", lowBound=MIN_LUBE[l], upBound=MAX_LUBE[l])
        for l in LUBE
    }

    model += (
        pulp.lpSum(PROFIT_FUEL[f] * fuel_prod[f] for f in FUEL)
        + pulp.lpSum(PROFIT_PETROL[p] * petrol_prod[p] for p in PETROL)
        + pulp.lpSum(PROFIT_LUBE[l] * lube_prod[l] for l in LUBE)
    ), "Total_Profit"

    model += pulp.lpSum(crude[c] for c in CRUDE) <= MAX_DISTILL, "Distillation_Capacity"
    model += pulp.lpSum(naphtha_to_reformer[n] for n in NAPHTHA) <= MAX_REFORM, "Reforming_Capacity"
    model += pulp.lpSum(oil_to_cracker[o] for o in OIL) <= MAX_CRACK, "Cracking_Capacity"

    for n in NAPHTHA:
        model += (
            pulp.lpSum(DISTILL_NAPHTHA.get((c, n), 0) * crude[c] for c in CRUDE)
            == naphtha[n]
        ), f"Distill_Naphtha_{n}"

    for o in OIL:
        model += (
            pulp.lpSum(DISTILL_OIL.get((c, o), 0) * crude[c] for c in CRUDE)
            == oil[o]
        ), f"Distill_Oil_{o}"

    for r in RESID:
        model += (
            pulp.lpSum(DISTILL_RESID.get((c, r), 0) * crude[c] for c in CRUDE)
            == resid[r]
        ), f"Distill_Resid_{r}"

    for rp in REFORM_PRODUCTS:
        model += (
            pulp.lpSum(REFORM_PROCESS.get((n, rp), 0) * naphtha_to_reformer[n] for n in NAPHTHA)
            == reform[rp]
        ), f"Reform_Product_{rp}"

    for cp in CRACK_PRODUCTS:
        model += (
            pulp.lpSum(CRACK_PROCESS.get((o, cp), 0) * oil_to_cracker[o] for o in OIL)
            == cracked[cp]
        ), f"Crack_Product_{cp}"

    for l in LUBE:
        model += (
            pulp.lpSum(RESID_PROCESS.get((r, l), 0) * resid_to_lube[r] for r in RESID)
            == lube_prod[l]
        ), f"Lube_Product_{l}"

    for n in NAPHTHA:
        model += (
            naphtha_to_reformer[n]
            + pulp.lpSum(naphtha_to_petrol[(n, p)] for p in PETROL)
            == naphtha[n]
        ), f"Naphtha_Balance_{n}"

    for o in OIL:
        model += (
            oil_to_cracker[o]
            + pulp.lpSum(oil_to_fuel[(o, f)] for f in FUEL)
            == oil[o]
        ), f"Oil_Balance_{o}"

    for r in RESID:
        model += (
            resid_to_lube[r]
            + pulp.lpSum(resid_to_fuel[(r, f)] for f in FUEL)
            == resid[r]
        ), f"Resid_Balance_{r}"

    for rp in REFORM_PRODUCTS:
        model += (
            pulp.lpSum(reform_to_petrol[(rp, p)] for p in PETROL) == reform[rp]
        ), f"Reform_Balance_{rp}"

    model += cracked["CG"] == pulp.lpSum(cracked_gas_to_petrol[p] for p in PETROL), "Cracked_Gas_Balance"
    model += cracked["CO"] == pulp.lpSum(cracked_oil_to_fuel[f] for f in FUEL), "Cracked_Oil_Balance"

    for p in PETROL:
        model += (
            pulp.lpSum(naphtha_to_petrol[(n, p)] for n in NAPHTHA)
            + pulp.lpSum(reform_to_petrol[(rp, p)] for rp in REFORM_PRODUCTS)
            + cracked_gas_to_petrol[p]
            == petrol_prod[p]
        ), f"Petrol_Balance_{p}"

    for f in FUEL:
        model += (
            pulp.lpSum(oil_to_fuel[(o, f)] for o in OIL)
            + cracked_oil_to_fuel[f]
            + pulp.lpSum(resid_to_fuel[(r, f)] for r in RESID)
            == fuel_prod[f]
        ), f"Fuel_Balance_{f}"

    # Fuel-oil blending. The original code treated each within-group ratio as
    # a share of total FO, making the coefficients sum to 2.15 and forcing
    # FO production to zero. The supplied oil and residue ratios are instead
    # enforced within their respective component groups.
    fo_oil_group = pulp.LpVariable("FO_Oil_Group", lowBound=0)
    fo_resid_group = pulp.LpVariable("FO_Resid_Group", lowBound=0)

    model += (
        pulp.lpSum(oil_to_fuel[(o, "FO")] for o in OIL) == fo_oil_group
    ), "FO_Oil_Group_Balance"
    model += (
        pulp.lpSum(resid_to_fuel[(r, "FO")] for r in RESID) == fo_resid_group
    ), "FO_Resid_Group_Balance"

    for o in OIL:
        model += (
            oil_to_fuel[(o, "FO")] == FO_OIL_RATIO[o] * fo_oil_group
        ), f"FO_Oil_Ratio_{o}"

    for r in RESID:
        model += (
            resid_to_fuel[(r, "FO")] == FO_RESID_RATIO[r] * fo_resid_group
        ), f"FO_Resid_Ratio_{r}"

    model += (
        cracked_oil_to_fuel["FO"] == FO_CRACKED_OIL_SHARE * fuel_prod["FO"]
    ), "FO_Cracked_Oil_Share"

    model += (
        petrol_prod["PMF"] >= MIN_PMF_TO_RMF_RATIO * petrol_prod["RMF"]
    ), "Petrol_Ratio_Requirement"

    for p in PETROL:
        model += (
            pulp.lpSum(OCTANE_NAPHTHA[n] * naphtha_to_petrol[(n, p)] for n in NAPHTHA)
            + pulp.lpSum(OCTANE_REFORM[rp] * reform_to_petrol[(rp, p)] for rp in REFORM_PRODUCTS)
            + OCTANE_CG * cracked_gas_to_petrol[p]
            >= MIN_OCTANE[p] * petrol_prod[p]
        ), f"Octane_Requirement_{p}"

    model += (
        pulp.lpSum(VAPOR_OIL[o] * oil_to_fuel[(o, "JF")] for o in OIL)
        + VAPOR_CRACKED_OIL * cracked_oil_to_fuel["JF"]
        + pulp.lpSum(VAPOR_RESID[r] * resid_to_fuel[(r, "JF")] for r in RESID)
        <= MAX_VAPOR_JF * fuel_prod["JF"]
    ), "Vapor_Pressure_JF"

    variables = {
        "crude": crude,
        "naphtha_to_reformer": naphtha_to_reformer,
        "oil_to_cracker": oil_to_cracker,
        "fuel_prod": fuel_prod,
        "petrol_prod": petrol_prod,
        "lube_prod": lube_prod,
    }
    return model, variables


def solve_and_report():
    model, v = build_model()

    print("Solving Oil Refinery Optimization Problem...")
    solver = pulp.PULP_CBC_CMD(msg=False)
    status_code = model.solve(solver)
    status = pulp.LpStatus[status_code]

    print(f"\nStatus: {status}")
    if status != "Optimal":
        raise RuntimeError(f"Optimization did not reach an optimal solution: {status}")

    objective = pulp.value(model.objective)
    print(f"Optimal Total Profit: ${objective:,.2f}")

    print("\n" + "=" * 60)
    print("OPTIMAL SOLUTION")
    print("=" * 60)

    print("\nCrude Oil Processing:")
    for c in CRUDE:
        value = v["crude"][c].value() or 0.0
        if value > 0.01:
            print(f"  {c}: {value:,.2f} units")

    print("\nFinal Product Production:")
    print("  Fuels:")
    for f in FUEL:
        value = v["fuel_prod"][f].value() or 0.0
        if value > 0.01:
            print(f"    {f}: {value:,.2f} units (Margin: ${PROFIT_FUEL[f] * value:,.2f})")

    print("  Petrols:")
    for p in PETROL:
        value = v["petrol_prod"][p].value() or 0.0
        if value > 0.01:
            print(f"    {p}: {value:,.2f} units (Margin: ${PROFIT_PETROL[p] * value:,.2f})")

    print("  Lubricants:")
    for l in LUBE:
        value = v["lube_prod"][l].value() or 0.0
        if value > 0.01:
            print(f"    {l}: {value:,.2f} units (Margin: ${PROFIT_LUBE[l] * value:,.2f})")

    total_crude = sum((v["crude"][c].value() or 0.0) for c in CRUDE)
    reform_usage = sum((v["naphtha_to_reformer"][n].value() or 0.0) for n in NAPHTHA)
    crack_usage = sum((v["oil_to_cracker"][o].value() or 0.0) for o in OIL)

    print("\nCapacity Utilization:")
    print(f"  Distillation: {100 * total_crude / MAX_DISTILL:.1f}% ({total_crude:,.0f}/{MAX_DISTILL:,})")
    print(f"  Reforming:    {100 * reform_usage / MAX_REFORM:.1f}% ({reform_usage:,.0f}/{MAX_REFORM:,})")
    print(f"  Cracking:     {100 * crack_usage / MAX_CRACK:.1f}% ({crack_usage:,.0f}/{MAX_CRACK:,})")


if __name__ == "__main__":
    solve_and_report()
