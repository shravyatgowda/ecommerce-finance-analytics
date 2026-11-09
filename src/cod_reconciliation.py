"""Reconcile Cash on Delivery (COD) carrier reports against internal order books."""
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW, OUT = ROOT / "data" / "raw", ROOT / "outputs"


def reconcile():
    orders = pd.read_csv(RAW / "orders.csv")
    carrier = pd.read_csv(RAW / "carrier_cod_report.csv")
    df = orders.merge(carrier, on="order_id", how="outer", indicator=True)

    unmatched = df[df["_merge"] != "both"]
    if len(unmatched):
        print(f"WARNING: {len(unmatched)} orders appear in only one source")

    rto_mismatch = (df["internal_status"] == "RTO") & (df["carrier_status"] == "DELIVERED")
    short_remit = (df["carrier_status"] == "DELIVERED") & (df["cod_remitted"] < df["cod_collected"]) & ~rto_mismatch

    df["issue"] = "MATCHED"
    df.loc[rto_mismatch, "issue"] = "RTO_STATUS_MISMATCH"
    df.loc[short_remit, "issue"] = "SHORT_REMITTANCE"
    df["leakage_amount"] = (df["cod_collected"] - df["cod_remitted"]).where(df["issue"] != "MATCHED", 0.0)

    total_collected = df["cod_collected"].sum()
    total_leakage = df["leakage_amount"].sum()

    exceptions = df[df["issue"] != "MATCHED"]
    summary = (exceptions.groupby("issue")
               .agg(orders=("order_id", "count"), leakage_amount=("leakage_amount", "sum")).reset_index())
    by_carrier = (exceptions.groupby("carrier")
                  .agg(orders=("order_id", "count"), leakage_amount=("leakage_amount", "sum")).reset_index()
                  .sort_values("leakage_amount", ascending=False))

    OUT.mkdir(exist_ok=True)
    exceptions.drop(columns="_merge").to_csv(OUT / "cod_exceptions.csv", index=False)
    summary.to_csv(OUT / "cod_summary_by_issue.csv", index=False)
    by_carrier.to_csv(OUT / "cod_leakage_by_carrier.csv", index=False)

    print(f"Orders reconciled     : {len(df):,}")
    print(f"COD collected         : {total_collected:,.0f}")
    print(f"Leakage               : {total_leakage:,.0f} ({total_leakage / total_collected:.2%})")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    reconcile()
