from __future__ import annotations
import streamlit as st
import pandas as pd
from pathlib import Path

# --- Bootstrap: ensure we can import our own package in any environment ---
import sys, importlib.util
from pathlib import Path as _P
_ROOT = _P(__file__).resolve().parents[1]  # repo root (folder that contains "app")
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

# Try normal package import; if it fails, fall back to direct file import
try:
    from app.logic.data_io import load_all  # noqa
except ModuleNotFoundError:
    _data_io_path = _ROOT / "app" / "logic" / "data_io.py"
    spec = importlib.util.spec_from_file_location("data_io", _data_io_path)
    _mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(_mod)  # type: ignore
    load_all = _mod.load_all  # type: ignore
    # also patch the other modules similarly below
    _sim_path = _ROOT / "app" / "logic" / "simulator.py"
    _spec2 = importlib.util.spec_from_file_location("simulator", _sim_path)
    _mod2 = importlib.util.module_from_spec(_spec2)
    assert _spec2.loader is not None
    _spec2.loader.exec_module(_mod2)  # type: ignore
    weekly_capacity = _mod2.weekly_capacity
    weekly_inventory_start = _mod2.weekly_inventory_start
    baseline_forecast = _mod2.baseline_forecast
    apply_scenario = _mod2.apply_scenario
    capacity_material_adjustment = _mod2.capacity_material_adjustment
    fuel_cost_adjustment = _mod2.fuel_cost_adjustment
    plan_balance = _mod2.plan_balance
    summarize_kpis = _mod2.summarize_kpis

    _ui_path = _ROOT / "app" / "ui" / "components.py"
    _spec3 = importlib.util.spec_from_file_location("components", _ui_path)
    _mod3 = importlib.util.module_from_spec(_spec3)
    assert _spec3.loader is not None
    _spec3.loader.exec_module(_mod3)  # type: ignore
    line_forecast_vs_supply = _mod3.line_forecast_vs_supply
    bar_gap = _mod3.bar_gap
else:
    # If normal import succeeded, import the rest normally
    from app.logic.simulator import (
        weekly_capacity, weekly_inventory_start, baseline_forecast,
        apply_scenario, capacity_material_adjustment, fuel_cost_adjustment,
        plan_balance, summarize_kpis, cost_table
    )
    from app.ui.components import line_forecast_vs_supply, bar_gap
# --- End bootstrap ---

# (imports continue below)
from app.logic.data_io import load_all
from app.logic.simulator import (
    weekly_capacity, weekly_inventory_start, baseline_forecast,
    apply_scenario, capacity_material_adjustment, fuel_cost_adjustment,
    plan_balance, summarize_kpis, cost_table
)
from app.ui.components import line_forecast_vs_supply, bar_gap

st.set_page_config(page_title="CPG S&OP Demo", page_icon="📦", layout="wide")

# Health check: show where we're importing from and verify required CSVs
import streamlit as st
from app.logic.data_io import REQUIRED_FILES
st.sidebar.caption("Health")
st.sidebar.code(f"sys.path[0]: {sys.path[0]}\nroot: {_ROOT}")
missing = [f for f in REQUIRED_FILES if not (_ROOT / "data" / f).exists()]
if missing:
    st.sidebar.error("Missing CSVs in ./data: " + ", ".join(missing))


# Sidebar: data folder & use case
st.sidebar.header("⚙️ Setup")
data_dir = st.sidebar.text_input("Data folder", value=str(Path(__file__).resolve().parents[1] / "data"))
use_case = st.sidebar.radio("Use case", ["Demand & Supply Balancing", "Scenario Planning"], index=0)

# Load data
try:
    dfs = load_all(data_dir)
except Exception as e:
    st.error(f"Could not load data from `{data_dir}`.\n\n{e}\n\n"
             "→ Put the CSVs from `cpg_sop_dataset.zip` into that folder and retry.")
    st.stop()

products = dfs["products"]
regions_all = ["ANZ-North","ANZ-South","ANZ-East","ANZ-West"]

# Common selections
st.sidebar.header("🔎 Filters")
sku_sel = st.sidebar.multiselect("SKUs", options=products["sku_id"].tolist(), default=products["sku_id"].tolist()[:2])
region_sel = st.sidebar.multiselect("Regions", options=regions_all, default=regions_all)

weeks = dfs["forecast_baseline"]["week_start"].sort_values().unique().tolist()
if len(weeks)==0:
    st.error("No forecast weeks found in dataset.")
    st.stop()
wk_min = weeks[0]
wk_max = weeks[-1]
min_dt = pd.to_datetime(wk_min).to_pydatetime()
max_dt = pd.to_datetime(wk_max).to_pydatetime()
default_end = (pd.to_datetime(wk_min) + pd.Timedelta(weeks=8)).to_pydatetime()
week_range = st.sidebar.slider("Week range", min_value=min_dt, max_value=max_dt,
                               value=(min_dt, default_end), format="YYYY-MM-DD")
start_ts = pd.Timestamp(week_range[0])
end_ts = pd.Timestamp(week_range[1])
week_starts = [w for w in weeks if start_ts <= pd.to_datetime(w) <= end_ts]

# Scenario knobs (shown only in Scenario Planning)
scenario = {}
if use_case == "Scenario Planning":
    st.sidebar.header("🧪 Scenario knobs")
    st.sidebar.caption("Demand uplift by category")
    cats = products["category"].unique().tolist()
    uplift = {}
    for c in cats:
        v = st.sidebar.slider(f"{c} uplift (×)", min_value=0.5, max_value=1.8, value=1.0, step=0.05)
        if abs(v-1.0) > 1e-6:
            uplift[c] = v
    if uplift:
        scenario["uplift_by_category"] = uplift
        col1, col2 = st.sidebar.columns(2)
        with col1:
            use_window = st.toggle("Limit by date window", value=False)
        if use_window:
            scenario["uplift_start"] = st.date_input("Uplift start", value=pd.to_datetime("2024-12-01"))
            scenario["uplift_end"] = st.date_input("Uplift end", value=pd.to_datetime("2025-02-28"))

    st.sidebar.divider()
    st.sidebar.caption("Supplier delay (material constraint)")
    delay_material_id = st.sidebar.selectbox("Material", options=dfs["bom"]["material_id"].unique().tolist())
    delay_days = st.sidebar.slider("Delay (days)", min_value=0, max_value=35, value=0, step=1)
    scenario["delay_material_id"] = delay_material_id
    scenario["delay_days"] = delay_days
    col3, col4 = st.sidebar.columns(2)
    with col3:
        scenario["delay_start"] = st.date_input("Delay start", value=pd.to_datetime("2025-03-01"))
    with col4:
        scenario["delay_end"] = st.date_input("Delay end", value=pd.to_datetime("2025-04-15"))

    st.sidebar.divider()
    fuel_spike = st.sidebar.slider("Fuel cost spike (%)", min_value=0, max_value=50, value=0, step=1)

# Actions
colA, colB = st.columns([1,1])
with colA:
    if use_case == "Demand & Supply Balancing":
        run = st.button("Run", type="primary")
    else:
        run = st.button("Run scenario", type="primary")
with colB:
    st.write("")

if not run:
    st.stop()

# Compute baseline
base_fc = baseline_forecast(dfs, sku_sel, region_sel, week_starts)
cap = weekly_capacity(dfs, sku_sel, week_starts)
inv = weekly_inventory_start(dfs, sku_sel, week_starts[:1])  # starting inv only for first week
costs = cost_table(dfs)

if use_case == "Demand & Supply Balancing":
    plan = plan_balance(base_fc, cap, inv, costs)
    st.subheader("📈 Forecast vs Supply")
    st.altair_chart(line_forecast_vs_supply(plan), use_container_width=True)
    st.subheader("🕳️ Gaps by Week")
    st.altair_chart(bar_gap(plan), use_container_width=True)
    st.subheader("📋 Plan Table")
    st.dataframe(plan, use_container_width=True, hide_index=True)
    st.subheader("🔢 KPIs")
    kpis = plan.groupby("sku_id").apply(lambda df: summarize_kpis(df)).reset_index()
    st.dataframe(kpis, use_container_width=True, hide_index=True)

else:
    # Scenario path
    sc_fc = apply_scenario(base_fc, dfs, scenario)
    sc_cap = capacity_material_adjustment(dfs, cap, scenario)
    sc_costs = fuel_cost_adjustment(costs, fuel_spike)
    base_plan = plan_balance(base_fc, cap, inv, costs)
    sc_plan = plan_balance(sc_fc, sc_cap, inv, sc_costs)

    st.subheader("📊 Service Level: Baseline vs Scenario")
    svc = pd.DataFrame({
        "week_start": base_plan["week_start"],
        "Baseline": base_plan["service_level"].round(3),
        "Scenario": sc_plan["service_level"].round(3)
    })
    st.line_chart(svc.set_index("week_start"))

    st.subheader("💰 Revenue & Margin (Totals)")
    cols = st.columns(3)
    base_kpi = summarize_kpis(base_plan)
    sc_kpi = summarize_kpis(sc_plan)
    delta = sc_kpi - base_kpi
    with cols[0]:
        st.metric("Service level", f"{base_kpi['Service level']:.3f}", f"{(sc_kpi['Service level']-base_kpi['Service level']):+.3f}")
    with cols[1]:
        st.metric("Revenue", f"{base_kpi['Revenue']:,}", f"{delta['Revenue']:+,.0f}")
    with cols[2]:
        st.metric("Margin", f"{base_kpi['Margin']:,}", f"{delta['Margin']:+,.0f}")

    st.subheader("🧾 Details (Scenario Plan)")
    st.dataframe(sc_plan, use_container_width=True, hide_index=True)
