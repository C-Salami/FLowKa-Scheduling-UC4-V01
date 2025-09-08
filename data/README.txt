CPG S&OP Synthetic Dataset (CSV)
=================================
Date range: 2024-01-01 to 2025-08-31
Use cases supported: Demand & Supply Balancing, Scenario Planning & Risk Management

Files
-----
- calendar.csv: daily calendar with week/month/quarter, AU holidays flag, season.
- products.csv: product master (SKU, category, brand, pack size, shelf life).
- customers.csv: customers with channel and region.
- promotions.csv: promotional windows per SKU (discount & expected lift).
- sales_history.csv: daily sell-in to customers (units, revenue, price, promo flag).
- pos_market_signal.csv: daily POS signal per SKU & region.
- inventory_snapshots.csv: weekly inventory at DCs (on-hand & safety stock).
- production_capacity.csv: plant x SKU daily capacity & changeover.
- capacity_calendar.csv: plant daily available minutes and downtime.
- bom.csv: components per SKU and quantity per unit.
- suppliers.csv: supplier master with performance & lead times.
- purchase_orders.csv: weekly open/active POs for materials.
- logistics_lanes.csv: cost and transit times across lanes.
- cost_structures.csv: unit-level material/conversion/logistics cost and list price.
- forecast_baseline.csv: weekly baseline forecast per SKU & region.
- scenarios.csv: example levers for scenario analysis.

Notes
-----
- Values are synthetic but internally consistent (seasonality, promo lift, lead times).
- Monetary values are in AUD; quantities in units indicated by UOM columns.
- Feel free to trim or expand as needed for your modeling environment.
