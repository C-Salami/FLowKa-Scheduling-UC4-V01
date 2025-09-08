from __future__ import annotations
import pandas as pd
from pathlib import Path
from typing import Dict

REQUIRED_FILES = [
    "calendar.csv",
    "products.csv",
    "customers.csv",
    "promotions.csv",
    "sales_history.csv",
    "pos_market_signal.csv",
    "inventory_snapshots.csv",
    "production_capacity.csv",
    "capacity_calendar.csv",
    "bom.csv",
    "suppliers.csv",
    "purchase_orders.csv",
    "logistics_lanes.csv",
    "cost_structures.csv",
    "forecast_baseline.csv",
    "scenarios.csv",
]

def load_all(data_dir: str | Path) -> Dict[str, pd.DataFrame]:
    data_dir = Path(data_dir)
    missing = [f for f in REQUIRED_FILES if not (data_dir / f).exists()]
    if missing:
        raise FileNotFoundError(f"Missing files in {data_dir}: {', '.join(missing)}")
    dfs = {name.replace(".csv",""): pd.read_csv(data_dir / name, parse_dates=[0], dayfirst=False, infer_datetime_format=True)
           for name in REQUIRED_FILES}
    # Ensure date columns are proper dtypes
    if "forecast_baseline" in dfs:
        dfs["forecast_baseline"]["week_start"] = pd.to_datetime(dfs["forecast_baseline"]["week_start"])
    if "inventory_snapshots" in dfs:
        dfs["inventory_snapshots"]["date"] = pd.to_datetime(dfs["inventory_snapshots"]["date"])
    if "capacity_calendar" in dfs:
        dfs["capacity_calendar"]["date"] = pd.to_datetime(dfs["capacity_calendar"]["date"])
    if "calendar" in dfs:
        dfs["calendar"]["date"] = pd.to_datetime(dfs["calendar"]["date"])
    if "promotions" in dfs:
        dfs["promotions"]["start_date"] = pd.to_datetime(dfs["promotions"]["start_date"])
        dfs["promotions"]["end_date"] = pd.to_datetime(dfs["promotions"]["end_date"])
    return dfs
