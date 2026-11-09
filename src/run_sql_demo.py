"""Run the SQL versions of the analyses against an in-memory SQLite database."""
from pathlib import Path
import sqlite3
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW, SQL = ROOT / "data" / "raw", ROOT / "sql"

con = sqlite3.connect(":memory:")
for table, file in [("orders", "orders.csv"), ("carrier_cod_report", "carrier_cod_report.csv"), ("ar_invoices", "ar_invoices.csv")]:
    pd.read_csv(RAW / file).to_sql(table, con, index=False)

for name in ["cod_reconciliation.sql", "ar_aging.sql"]:
    print(f"\n=== {name} ===")
    print(pd.read_sql_query((SQL / name).read_text(), con).to_string(index=False))
