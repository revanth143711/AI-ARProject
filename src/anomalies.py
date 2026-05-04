import os
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression

# -----------------------------------------
# ML-based anomaly detection (VALIDATION stage)
# -----------------------------------------

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

IN_PATH = os.path.join(BASE_DIR, "data", "erp_export.csv")
OUT_PATH = os.path.join(BASE_DIR, "reports", "anomalies_ml.csv")


def run_anomaly_detection():
    """
    Validation stage:
    Detect anomalies using ML (residual-based detection).
    Returns anomaly records for workflow usage.
    """

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)

    # ---------------------------
    # Load data
    # ---------------------------
    df = pd.read_csv(IN_PATH)

    # ---------------------------
    # Feature engineering
    # ---------------------------
    X = df[[
        "Invoice Total", "Invoice applied amount", "Invoice exchange rate",
        "Payment Total", "Payment applied amount", "Payment exchange rate",
        "Credit Total", "Credit applied amount", "Credit exchange rate",
        "Adjustment Total", "Adjustment applied amount", "Adjustment exchange rate"
    ]].copy()

    y_reported = df["Customer Balance"].values

    # ---------------------------
    # Train model
    # ---------------------------
    model = LinearRegression()
    model.fit(X, y_reported)

    # ---------------------------
    # Predictions & residuals
    # ---------------------------
    y_pred = model.predict(X)
    resid = y_reported - y_pred
    abs_resid = np.abs(resid)

    df_out = df.copy()
    df_out["ML Predicted Balance"] = np.round(y_pred, 2)
    df_out["Residual"] = np.round(resid, 2)
    df_out["Abs Residual"] = np.round(abs_resid, 2)

    # ---------------------------
    # Threshold detection
    # ---------------------------
    threshold = max(abs_resid.mean() + 2.5 * abs_resid.std(), 5.00)

    anomalies = df_out[df_out["Abs Residual"] >= threshold].copy()
    anomalies = anomalies.sort_values("Abs Residual", ascending=False)

    # ---------------------------
    # Save output
    # ---------------------------
    anomalies.to_csv(OUT_PATH, index=False)

    print(f"✅ ML anomalies → {OUT_PATH} (rows: {len(anomalies)})")
    print(f"   Residual threshold used: {threshold:.2f}")

    # 🔥 IMPORTANT: return anomaly records
    return anomalies.to_dict(orient="records")