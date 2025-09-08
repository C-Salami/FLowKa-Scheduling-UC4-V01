from __future__ import annotations
import altair as alt
import pandas as pd

def line_forecast_vs_supply(df: pd.DataFrame) -> alt.Chart:
    base = df.melt(id_vars=["week_start","sku_id"], value_vars=["demand","supply_potential","shipped_units"],
                   var_name="metric", value_name="units")
    return alt.Chart(base).mark_line(point=True).encode(
        x="week_start:T",
        y="units:Q",
        color="metric:N",
        tooltip=["week_start:T","sku_id:N","metric:N","units:Q"]
    ).properties(height=320)

def bar_gap(df: pd.DataFrame) -> alt.Chart:
    agg = df.groupby("week_start", as_index=False)["gap_units"].sum()
    return alt.Chart(agg).mark_bar().encode(
        x="week_start:T",
        y="gap_units:Q",
        tooltip=["week_start:T","gap_units:Q"]
    ).properties(height=200)

def kpi_badge(label: str, value: str) -> str:
    return f"**{label}:** {value}"
