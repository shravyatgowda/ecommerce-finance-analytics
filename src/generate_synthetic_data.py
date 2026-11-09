"""Generate SYNTHETIC e-commerce finance datasets.

The data is fully artificial. It mirrors the scale and structure of the
reconciliation, aging and variance work described in the README, but contains
no client or employer data. Run from the repo root:

    python src/generate_synthetic_data.py
"""
from pathlib import Path
import numpy as np
import pandas as pd

SEED = 42
N_ORDERS = 35_000
TARGET_LEAKAGE = 0.028          # leakage as a share of COD collected by carriers
AR_OUTSTANDING_TARGET = 152_000  # total outstanding receivables (currency units)
AS_OF = pd.Timestamp("2025-06-30")

RAW = Path(__file__).resolve().parents[1] / "data" / "raw"
rng = np.random.default_rng(SEED)


def make_cod():
    order_ids = [f"ORD{i:06d}" for i in range(1, N_ORDERS + 1)]
    dates = pd.to_datetime("2025-01-01") + pd.to_timedelta(rng.integers(0, 181, N_ORDERS), unit="D")
    value = np.round(rng.lognormal(mean=6.6, sigma=0.55, size=N_ORDERS) / 10) * 10
    value = np.clip(value, 199, 9999)
    carriers = rng.choice(["Carrier A", "Carrier B", "Carrier C", "Carrier D"], N_ORDERS, p=[.4, .3, .2, .1])
    is_rto = rng.random(N_ORDERS) < 0.12

    orders = pd.DataFrame({
        "order_id": order_ids,
        "order_date": dates.date,
        "carrier": carriers,
        "order_value": value,
        "internal_status": np.where(is_rto, "RTO", "DELIVERED"),
    })

    # Carrier report: delivered orders are collected and remitted in full,
    # RTO orders show no cash collected.
    carrier = pd.DataFrame({
        "order_id": order_ids,
        "carrier_status": np.where(is_rto, "RTO", "DELIVERED"),
        "cod_collected": np.where(is_rto, 0.0, value),
        "cod_remitted": np.where(is_rto, 0.0, value),
    })

    # Inject discrepancies until leakage reaches the target share.
    collected_total = carrier["cod_collected"].sum()
    leaked = 0.0
    rto_pool = list(rng.permutation(np.where(is_rto)[0]))
    del_pool = list(rng.permutation(np.where(~is_rto)[0]))
    while leaked / collected_total < TARGET_LEAKAGE:
        if rng.random() < 0.7 and rto_pool:        # untracked RTO: carrier shows delivered + cash not remitted
            i = rto_pool.pop()
            carrier.loc[i, ["carrier_status", "cod_collected", "cod_remitted"]] = ["DELIVERED", value[i], 0.0]
            collected_total += value[i]
            leaked += value[i]
        else:                                       # short remittance on a delivered order
            i = del_pool.pop()
            short = np.round(value[i] * rng.uniform(0.05, 0.6))
            carrier.loc[i, "cod_remitted"] = value[i] - short
            leaked += short

    orders.to_csv(RAW / "orders.csv", index=False)
    carrier.to_csv(RAW / "carrier_cod_report.csv", index=False)


def make_ar():
    n = 90
    customers = [f"Customer {chr(65 + i)}" for i in range(14)]
    inv_date = AS_OF - pd.to_timedelta(rng.integers(20, 200, n), unit="D")
    terms = rng.choice([15, 30, 45], n, p=[.2, .6, .2])
    due = inv_date + pd.to_timedelta(terms, unit="D")
    raw_amt = rng.lognormal(7.3, 0.7, n)
    amt = np.round(raw_amt * AR_OUTSTANDING_TARGET / raw_amt.sum(), 0)
    ar = pd.DataFrame({
        "invoice_id": [f"INV{1000 + i}" for i in range(n)],
        "customer": rng.choice(customers, n),
        "invoice_date": inv_date.date,
        "due_date": due.date,
        "invoice_amount": amt,
        "amount_paid": 0.0,
    })
    ar.to_csv(RAW / "ar_invoices.csv", index=False)


def make_budget():
    cats = {"Carrier freight": 420_000, "Packaging": 90_000, "Warehouse labour": 260_000,
            "Customer support": 120_000, "Tech tools": 60_000, "Marketing": 180_000}
    rows = []
    for m in pd.period_range("2025-01", "2025-06", freq="M"):
        for cat, base in cats.items():
            budget = base * (1 + 0.02 * (m.month - 1))
            drift = rng.normal(0.02, 0.07)
            rows.append([str(m), cat, round(budget), round(budget * (1 + drift))])
    pd.DataFrame(rows, columns=["month", "category", "budget", "actual"]).to_csv(RAW / "budget_vs_actual.csv", index=False)


if __name__ == "__main__":
    RAW.mkdir(parents=True, exist_ok=True)
    make_cod()
    make_ar()
    make_budget()
    print("Synthetic data written to", RAW)
