from __future__ import annotations
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional

def weekly_capacity(dfs: Dict[str, pd.DataFrame], skus: List[str], week_starts: List[pd.Timestamp]) -> pd.DataFrame:
    cap = dfs["production_capacity"].copy()
    cal = dfs["capacity_calendar"].copy()
    cal["uptime_ratio"] = (cal["available_minutes"] - cal["downtime_minutes"]) / cal["available_minutes"]
    # Expand to daily capacity per plant/sku/date
    days = cal["date"].drop_duplicates().sort_values()
    plants = cal["plant_id"].drop_duplicates()
    cap = cap[cap["sku_id"].isin(skus)]
    # Cross-join cap with cal dates for each plant/sku where plant matches
    cap = cap.merge(cal, on="plant_id", how="left")
    cap["effective_daily"] = (cap["daily_capacity_units"] * cap["uptime_ratio"]).clip(lower=0)
    # Weekly aggregate by Monday week start
    cap["week_start"] = cap["date"] - pd.to_timedelta(cap["date"].dt.weekday, unit="D")
    wk = cap.groupby(["week_start","sku_id"], as_index=False)["effective_daily"].sum()
    wk["weekly_capacity_units"] = (wk["effective_daily"] * 7).round().astype(int)
    wk = wk.drop(columns=["effective_daily"])
    wk = wk[wk["week_start"].isin(week_starts)]
    return wk

def weekly_inventory_start(dfs: Dict[str, pd.DataFrame], skus: List[str], week_starts: List[pd.Timestamp]) -> pd.DataFrame:
    inv = dfs["inventory_snapshots"].copy()
    inv["week_start"] = inv["date"] - pd.to_timedelta(inv["date"].dt.weekday, unit="D")
    # Take last snapshot at/just before each week start, sum across DCs
    inv = inv.sort_values(["sku_id","location","date"])
    inv = inv.groupby(["sku_id","week_start"], as_index=False).agg(on_hand_units=("on_hand_units","sum"))
    # Reindex to requested week_starts (forward fill not applied here; take exact week)
    inv = inv[inv["sku_id"].isin(skus) & inv["week_start"].isin(week_starts)]
    return inv

def baseline_forecast(dfs: Dict[str, pd.DataFrame], skus: List[str], regions: List[str], week_starts: List[pd.Timestamp]) -> pd.DataFrame:
    fc = dfs["forecast_baseline"].copy()
    fc = fc[fc["sku_id"].isin(skus) & fc["region"].isin(regions) & fc["week_start"].isin(week_starts)]
    fc = fc.groupby(["week_start","sku_id"], as_index=False)["forecast_units"].sum()
    return fc

def cost_table(dfs: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    return dfs["cost_structures"].copy()

def apply_scenario(
    base_fc: pd.DataFrame,
    dfs: Dict[str, pd.DataFrame],
    scenario: dict
) -> pd.DataFrame:
    """Apply simple what-if uplifts and return adjusted forecast by week_start, sku_id."""
    fc = base_fc.copy()
    prod = dfs["products"][["sku_id","category"]]
    fc = fc.merge(prod, on="sku_id", how="left")
    # Demand uplift by category (optional date window)
    uplift_by_cat = scenario.get("uplift_by_category", {})
    start = pd.to_datetime(scenario.get("uplift_start", None)) if scenario.get("uplift_start") else None
    end   = pd.to_datetime(scenario.get("uplift_end", None)) if scenario.get("uplift_end") else None
    if uplift_by_cat:
        def uplift(row):
            factor = uplift_by_cat.get(row["category"], 1.0)
            if start is not None and end is not None:
                if not (start <= row["week_start"] <= end):
                    factor = 1.0
            return int(round(row["forecast_units"] * factor))
        fc["forecast_units"] = fc.apply(uplift, axis=1)
    return fc[["week_start","sku_id","forecast_units"]]

def capacity_material_adjustment(dfs: Dict[str, pd.DataFrame], cap_weekly: pd.DataFrame, scenario: dict) -> pd.DataFrame:
    """Reduce capacity for SKUs using a delayed material within the scenario window."""
    mat_id = scenario.get("delay_material_id")
    delay_days = int(scenario.get("delay_days", 0) or 0)
    start = pd.to_datetime(scenario.get("delay_start", None)) if scenario.get("delay_start") else None
    end   = pd.to_datetime(scenario.get("delay_end", None)) if scenario.get("delay_end") else None
    if not mat_id or delay_days <= 0:
        return cap_weekly
    bom = dfs["bom"]
    affected_skus = bom.loc[bom["material_id"]==mat_id, "sku_id"].unique().tolist()
    adj = cap_weekly.copy()
    if start is not None and end is not None:
        mask_window = (adj["week_start"]>=start) & (adj["week_start"]<=end)
    else:
        mask_window = pd.Series([True]*len(adj))
    # heuristic: each 7 days delay → 15% reduction
    reduction = min(0.9, 0.15 * (delay_days / 7.0))
    adj.loc[mask_window & adj["sku_id"].isin(affected_skus), "weekly_capacity_units"] = (
        adj.loc[mask_window & adj["sku_id"].isin(affected_skus), "weekly_capacity_units"] * (1 - reduction)
    ).round().astype(int)
    return adj

def fuel_cost_adjustment(costs: pd.DataFrame, fuel_spike_pct: float) -> pd.DataFrame:
    if not fuel_spike_pct:
        return costs
    adj = costs.copy()
    adj["logistics_cost"] = adj["logistics_cost"] * (1 + fuel_spike_pct/100.0)
    return adj

def plan_balance(fc: pd.DataFrame, cap: pd.DataFrame, inv: pd.DataFrame, costs: pd.DataFrame) -> pd.DataFrame:
    """Compute simple weekly balance and KPIs by sku_id and week_start.
    Supply for week = weekly capacity + starting inventory (only counted in first week per sku).
    Shipped = min(supply, demand)."""
    df = fc.merge(cap, on=["week_start","sku_id"], how="left").fillna({"weekly_capacity_units": 0})
    inv0 = inv.groupby("sku_id", as_index=False)["on_hand_units"].sum().rename(columns={"on_hand_units":"starting_inventory"})
    df = df.merge(inv0, on="sku_id", how="left").fillna({"starting_inventory": 0})
    # Only add starting inventory to the earliest week per sku
    df = df.sort_values(["sku_id","week_start"])
    df["inv_to_use"] = 0
    first_week = df.groupby("sku_id", as_index=False).head(1).index
    df.loc[first_week, "inv_to_use"] = df.loc[first_week, "starting_inventory"]
    df["supply_potential"] = df["weekly_capacity_units"] + df["inv_to_use"]
    df["demand"] = df["forecast_units"]
    df["shipped_units"] = df[["supply_potential","demand"]].min(axis=1).astype(int)
    df["gap_units"] = (df["demand"] - df["shipped_units"]).clip(lower=0).astype(int)
    # Merge unit economics
    df = df.merge(costs, on="sku_id", how="left")
    df["revenue"] = df["shipped_units"] * df["unit_list_price"]
    unit_cost = df["material_cost"] + df["conversion_cost"] + df["logistics_cost"]
    df["margin"] = df["revenue"] - (df["shipped_units"] * unit_cost)
    df["service_level"] = (df["shipped_units"] / df["demand"]).replace([np.inf, np.nan], 0.0).clip(0,1).round(3)
    keep = ["week_start","sku_id","demand","weekly_capacity_units","inv_to_use","supply_potential","shipped_units","gap_units","revenue","margin","service_level"]
    return df[keep]

def summarize_kpis(plan: pd.DataFrame) -> pd.Series:
    total_demand = plan["demand"].sum()
    total_shipped = plan["shipped_units"].sum()
    service = (total_shipped / total_demand) if total_demand else 0.0
    revenue = plan["revenue"].sum()
    margin = plan["margin"].sum()
    gap = plan["gap_units"].sum()
    return pd.Series({
        "Demand (units)": int(total_demand),
        "Shipped (units)": int(total_shipped),
        "Gap (units)": int(gap),
        "Service level": round(service, 3),
        "Revenue": round(revenue, 2),
        "Margin": round(margin, 2),
    })
