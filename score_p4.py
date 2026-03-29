# score_p4.py
# pandas version: checked at runtime | execution date: see printed output
# Scores prediction P4: "ballerina flat" UK Google Trends YoY growth T1 2026 vs T1 2025 > +40%
# NOTE: source CSV is monthly granularity (YYYY-MM-01); T1 = months 1, 2, 3.

import sys
import datetime
import pandas as pd

print(f"# score_p4.py | pandas {pd.__version__} | run {datetime.date.today()}")

CSV_PATH = "F:/fashion-benchmark/time_series_GB_20240101-0000_20260329-1914.csv"
THRESHOLD = 0.40  # +40% YoY

# -- Load ------------------------------------------------------------------
try:
    df = pd.read_csv(CSV_PATH, header=0)
except Exception as e:
    print(f"\n[ERROR] Could not read CSV: {e}")
    print("\n[DEBUG] First 5 raw lines:")
    with open(CSV_PATH, encoding="utf-8") as f:
        for i, line in enumerate(f):
            if i >= 5:
                break
            print(f"  {i}: {repr(line)}")
    sys.exit(1)

# -- Parse -----------------------------------------------------------------
df.columns = ["month", "interest"]
df["month"] = pd.to_datetime(df["month"].str.strip('"'), errors="coerce")
df = df.dropna(subset=["month"])

df["interest"] = df["interest"].replace("<1", "0.5")
df["interest"] = pd.to_numeric(df["interest"], errors="coerce").fillna(0)

df["m"] = df["month"].dt.month
df["y"] = df["month"].dt.year

# -- Filter T1 (months 1-3) ------------------------------------------------
t1_2025 = df[(df["y"] == 2025) & (df["m"].between(1, 3))]
t1_2026 = df[(df["y"] == 2026) & (df["m"].between(1, 3))]

print(f"\nT1 2025 rows  : {len(t1_2025)}  (expect 3)")
print(f"T1 2026 rows  : {len(t1_2026)}  (expect 3)")

print("\n-- T1 2025 monthly values --")
print(t1_2025[["month", "interest"]].to_string(index=False))

print("\n-- T1 2026 monthly values --")
print(t1_2026[["month", "interest"]].to_string(index=False))

# -- Compute means ---------------------------------------------------------
mean_2025 = t1_2025["interest"].mean()
mean_2026 = t1_2026["interest"].mean()

print(f"\nT1 2025 mean  : {mean_2025:.4f}")
print(f"T1 2026 mean  : {mean_2026:.4f}")

# -- Edge case: T1 2025 = 0 ------------------------------------------------
if mean_2025 == 0:
    print("\n[ANNULEE] T1_2025 = 0 -> division impossible, prediction annulee.")
    sys.exit(0)

# -- YoY growth ------------------------------------------------------------
yoy = (mean_2026 - mean_2025) / mean_2025
verdict = "TRUE" if yoy > THRESHOLD else "FALSE"

print(f"\nYoY growth    : {yoy:+.2%}")
print(f"Threshold     : >{THRESHOLD:.0%}")
print(f"\n{'='*40}")
print(f"  VERDICT : {verdict}")
print(f"{'='*40}")
