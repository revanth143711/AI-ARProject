import os
import numpy as np
import pandas as pd

# -----------------------------------------
# Rule-based reconciliation (MATCHING stage)
# -----------------------------------------

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

IN_PATH = os.path.join(BASE_DIR, "data", "erp_export.csv")
OUT_PATH = os.path.join(BASE_DIR, "reports", "mismatches_rule_based.csv")


def run_reconciliation():
    """
    Matching stage:
    Recompute balances and detect mismatches.
    Returns mismatched records for workflow usage.
    """

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)

    # ---------------------------
    # Load data
    # ---------------------------
    df = pd.read_csv(IN_PATH)

    # ---------------------------
    # Recompute expected balance
    # ---------------------------
    expected = (
        (df["Invoice Total"] - df["Invoice applied amount"]) * df["Invoice exchange rate"]
        - (df["Payment Total"] - df["Payment applied amount"]) * df["Payment exchange rate"]
        - (df["Credit Total"] - df["Credit applied amount"]) * df["Credit exchange rate"]
        + (df["Adjustment Total"] - df["Adjustment applied amount"]) * df["Adjustment exchange rate"]
    )

    df["Expected Balance"] = np.round(expected, 2)
    df["Delta"] = np.round(df["Customer Balance"] - df["Expected Balance"], 2)
    df["Abs Delta"] = df["Delta"].abs()

    # ---------------------------
    # Root cause analysis
    # ---------------------------
    def likely_cause(row):
        inv = (row["Invoice Total"] - row["Invoice applied amount"]) * row["Invoice exchange rate"]
        pay = (row["Payment Total"] - row["Payment applied amount"]) * row["Payment exchange rate"]
        cred = (row["Credit Total"] - row["Credit applied amount"]) * row["Credit exchange rate"]
        adj = (row["Adjustment Total"] - row["Adjustment applied amount"]) * row["Adjustment exchange rate"]

        comps = {
            "Invoice": inv,
            "Payments": -pay,
            "Credits": -cred,
            "Adjustments": adj
        }

        driver = max(comps.items(), key=lambda kv: abs(kv[1]))[0]

        if row["Invoice applied amount"] > row["Invoice Total"] + 0.01:
            return "Invoice applied exceeds total"
        if row["Payment applied amount"] > row["Payment Total"] + 0.01:
            return "Payment applied exceeds total"
        if row["Credit applied amount"] > row["Credit Total"] + 0.01:
            return "Credit applied exceeds total"
        if row["Adjustment applied amount"] > row["Adjustment Total"] + 0.01:
            return "Adjustment applied exceeds total"

        return f"Check {driver}/exchange rate/rounding"

    # ---------------------------
    # Filter mismatches
    # ---------------------------
    TOL = 0.05
    bad = df[df["Abs Delta"] > TOL].copy()

    if not bad.empty:
        bad["Likely Cause"] = bad.apply(likely_cause, axis=1)

    bad = bad.sort_values("Abs Delta", ascending=False)

    # ---------------------------
    # Save output
    # ---------------------------
    bad.to_csv(OUT_PATH, index=False)

    print(f"✅ Rule-based mismatches → {OUT_PATH} (rows: {len(bad)})")

    # 🔥 IMPORTANT: return mismatches
    return bad.to_dict(orient="records")