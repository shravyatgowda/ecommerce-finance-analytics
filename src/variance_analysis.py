"""Month-end variance analysis: actual operating expenses vs budget."""
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW, OUT = ROOT / "data" / "raw", ROOT / "outputs"
THRESHOLD_PCT = 5.0  # flag overruns above this percentage


def run():
    df = pd.read_csv(RAW / "budget_vs_actual.csv")
    df["variance"] = df["actual"] - df["budget"]
    df["variance_pct"] = (df["variance"] / df["budget"] * 100).round(1)
    df["flag"] = df["variance_pct"].apply(
        lambda v: "OVERRUN" if v > THRESHOLD_PCT else ("UNDERSPEND" if v < -THRESHOLD_PCT else "ON TRACK"))

    monthly = (df.groupby("month")[["budget", "actual", "variance"]].sum()
               .assign(variance_pct=lambda d: (d["variance"] / d["budget"] * 100).round(1)).reset_index())

    OUT.mkdir(exist_ok=True)
    df.to_csv(OUT / "variance_by_category.csv", index=False)
    monthly.to_csv(OUT / "variance_monthly_summary.csv", index=False)
    df[df["flag"] == "OVERRUN"].sort_values("variance", ascending=False).to_csv(OUT / "variance_overruns.csv", index=False)

    print(monthly.to_string(index=False))
    print(f"\nCategory-months flagged OVERRUN (> {THRESHOLD_PCT}%): {(df['flag'] == 'OVERRUN').sum()}")


if __name__ == "__main__":
    run()
