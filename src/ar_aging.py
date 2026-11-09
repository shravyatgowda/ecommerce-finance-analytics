"""Accounts receivable aging model with 30/60/90-day buckets."""
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW, OUT = ROOT / "data" / "raw", ROOT / "outputs"
AS_OF = pd.Timestamp("2025-06-30")
BUCKETS = ["Current", "1-30 days", "31-60 days", "61-90 days", "90+ days"]


def bucket(days_overdue: int) -> str:
    if days_overdue <= 0:
        return "Current"
    if days_overdue <= 30:
        return "1-30 days"
    if days_overdue <= 60:
        return "31-60 days"
    if days_overdue <= 90:
        return "61-90 days"
    return "90+ days"


def run(as_of: pd.Timestamp = AS_OF):
    ar = pd.read_csv(RAW / "ar_invoices.csv", parse_dates=["invoice_date", "due_date"])
    ar["outstanding"] = ar["invoice_amount"] - ar["amount_paid"]
    ar = ar[ar["outstanding"] > 0].copy()
    ar["days_overdue"] = (as_of - ar["due_date"]).dt.days
    ar["bucket"] = ar["days_overdue"].apply(bucket)

    summary = (ar.groupby("bucket")["outstanding"].agg(["count", "sum"]).reindex(BUCKETS).fillna(0).reset_index()
               .rename(columns={"count": "invoices", "sum": "outstanding"}))
    summary["share_pct"] = (summary["outstanding"] / summary["outstanding"].sum() * 100).round(1)

    by_customer = (ar.pivot_table(index="customer", columns="bucket", values="outstanding", aggfunc="sum", fill_value=0)
                   .reindex(columns=BUCKETS, fill_value=0))
    by_customer["total"] = by_customer.sum(axis=1)
    by_customer = by_customer.sort_values("total", ascending=False)

    OUT.mkdir(exist_ok=True)
    summary.to_csv(OUT / "ar_aging_summary.csv", index=False)
    by_customer.to_csv(OUT / "ar_aging_by_customer.csv")
    ar.sort_values("days_overdue", ascending=False).to_csv(OUT / "ar_overdue_invoices.csv", index=False)

    print(f"As of {as_of.date()} | outstanding: {ar['outstanding'].sum():,.0f} across {len(ar)} invoices")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    run()
