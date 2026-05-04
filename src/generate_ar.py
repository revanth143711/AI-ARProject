import os
import numpy as np
import pandas as pd

# -----------------------------------------
# Generate synthetic AR export for customers
# (used as INGESTION stage in workflow engine)
# -----------------------------------------

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
OUT_PATH = os.path.join(BASE_DIR, "data", "erp_export.csv")


def rand_money(rng, low, high, size):
    vals = rng.uniform(low, high, size)
    return np.round(vals, 2)


def generate_data(n=1000, seed=42):
    """
    Ingestion stage:
    Generates synthetic ERP data and saves to CSV.
    Returns list of records for workflow processing.
    """

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)

    rng = np.random.default_rng(seed)

    # ---------------------------
    # Base entities
    # ---------------------------
    customer_ids = [f"CUST-{i:04d}" for i in range(1, n + 1)]
    customer_names = [f"Customer {i:04d}" for i in range(1, n + 1)]

    # ---------------------------
    # Financial components
    # ---------------------------
    invoice_total = rand_money(rng, 100, 5000, n)
    invoice_applied = np.minimum(invoice_total, rand_money(rng, 0, invoice_total, n))
    invoice_rate = np.round(rng.uniform(0.8, 1.2, n), 4)

    payment_total = rand_money(rng, 0, 4000, n)
    payment_applied = np.minimum(payment_total, rand_money(rng, 0, payment_total, n))
    payment_rate = np.round(rng.uniform(0.8, 1.2, n), 4)

    credit_total = rand_money(rng, 0, 2000, n)
    credit_applied = np.minimum(credit_total, rand_money(rng, 0, credit_total, n))
    credit_rate = np.round(rng.uniform(0.8, 1.2, n), 4)

    adjust_total = rand_money(rng, 0, 1500, n)
    adjust_applied = np.minimum(adjust_total, rand_money(rng, 0, adjust_total, n))
    adjust_rate = np.round(rng.uniform(0.8, 1.2, n), 4)

    # ---------------------------
    # True ERP balance formula
    # ---------------------------
    true_balance = (
        (invoice_total - invoice_applied) * invoice_rate
        - (payment_total - payment_applied) * payment_rate
        - (credit_total - credit_applied) * credit_rate
        + (adjust_total - adjust_applied) * adjust_rate
    )

    customer_balance = np.round(true_balance, 2)

    # ---------------------------
    # Inject errors (~12%)
    # ---------------------------
    error_mask = rng.random(n) < 0.12

    for i in np.where(error_mask)[0]:
        mode = rng.integers(0, 4)

        if mode == 0:
            customer_balance[i] = np.round(
                customer_balance[i] + rng.normal(0, 25), 2
            )

        elif mode == 1:
            wrong_rate = rng.choice([0.85, 0.95, 1.05, 1.15])
            customer_balance[i] = np.round(
                (invoice_total[i] - invoice_applied[i]) * wrong_rate
                - (payment_total[i] - payment_applied[i]) * wrong_rate
                - (credit_total[i] - credit_applied[i]) * wrong_rate
                + (adjust_total[i] - adjust_applied[i]) * wrong_rate,
                2,
            )

        elif mode == 2:
            customer_balance[i] = np.round(
                (invoice_total[i] - invoice_applied[i]) * invoice_rate[i]
                - (payment_total[i] - payment_applied[i]) * payment_rate[i]
                + (adjust_total[i] - adjust_applied[i]) * adjust_rate[i],
                2,
            )

        else:
            bump = np.round(rng.uniform(10, 80), 2)
            customer_balance[i] = np.round(customer_balance[i] + bump, 2)

    # ---------------------------
    # Create DataFrame
    # ---------------------------
    df = pd.DataFrame({
        "Customer ID": customer_ids,
        "Customer Name": customer_names,
        "Customer Balance": customer_balance,
        "Invoice Total": invoice_total,
        "Invoice applied amount": invoice_applied,
        "Invoice exchange rate": invoice_rate,
        "Payment Total": payment_total,
        "Payment applied amount": payment_applied,
        "Payment exchange rate": payment_rate,
        "Credit Total": credit_total,
        "Credit applied amount": credit_applied,
        "Credit exchange rate": credit_rate,
        "Adjustment Total": adjust_total,
        "Adjustment applied amount": adjust_applied,
        "Adjustment exchange rate": adjust_rate,
    })

    # ---------------------------
    # Save file
    # ---------------------------
    df.to_csv(OUT_PATH, index=False)

    print(f"✅ ERP export generated: {OUT_PATH} ({len(df)} rows)")
    print(f"   Injected error rows: {error_mask.sum()} ({error_mask.mean()*100:.1f}%)")

    # 🔥 IMPORTANT: return records for workflow engine
    return df.to_dict(orient="records")