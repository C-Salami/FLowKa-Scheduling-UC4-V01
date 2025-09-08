# CPG S&OP Demo – Streamlit
Minimal, intuitive web app to **test S&OP use cases** on the provided **synthetic CPG dataset**.

## ✨ Features
- **Demand & Supply Balancing**: Compare weekly forecast vs. available supply capacity + starting inventory.
- **Scenario Planning**: Try demand uplifts, supplier delays (materials), and fuel cost spikes and see **service level, gap, revenue, and margin** deltas.
- **Clean, minimal UI** (Streamlit).

## 📁 Project Structure
```
.
├─ app/
│  ├─ streamlit_app.py
│  ├─ logic/
│  │  ├─ data_io.py
│  │  └─ simulator.py
│  └─ ui/
│     └─ components.py
├─ data/                 # ← put your CSVs here (from cpg_sop_dataset.zip)
├─ requirements.txt
├─ .streamlit/config.toml
└─ README.md
```

## ▶️ Quickstart
1. **Put data in `data/`**  
   Unzip your `cpg_sop_dataset.zip` and copy all CSVs into the `data/` folder (same level as this README).

2. **Create & activate env (optional but recommended)**
```bash
python -m venv .venv
# macOS/Linux
source .venv/bin/activate
# Windows
.venv\Scripts\activate
```

3. **Install deps**
```bash
pip install -r requirements.txt
```

4. **Run app**
```bash
streamlit run app/streamlit_app.py
```

5. **Open in browser**  
   Streamlit will print a local URL (usually http://localhost:8501) – click it.

## 🧪 How to test the two use cases

### 1) Demand & Supply Balancing
- In the sidebar, select **Use case → Demand & Supply Balancing**.
- Choose one or more **SKUs**, **regions**, and the **week range**.
- Click **Run**.  
  You’ll see **Forecast vs Supply** charts and a **weekly gap table** with service level and contribution margin.

### 2) Scenario Planning & Risk Management
- Select **Use case → Scenario Planning**.
- Adjust scenario knobs:
  - **Demand uplift** for categories, with optional date window (e.g., summer).
  - **Supplier delay** for selected material (e.g., MAT004 – Aluminium Can).
  - **Fuel cost spike** % (affects logistics cost → margin).
- Click **Run scenario** to compare **Baseline vs Scenario** KPIs and charts (service level, revenue, margin).

## 🧩 Data expected in `data/`
```
calendar.csv
products.csv
customers.csv
promotions.csv
sales_history.csv
pos_market_signal.csv
inventory_snapshots.csv
production_capacity.csv
capacity_calendar.csv
bom.csv
suppliers.csv
purchase_orders.csv
logistics_lanes.csv
cost_structures.csv
forecast_baseline.csv
scenarios.csv
```
> All files come from the synthetic dataset we generated earlier.

## 🚀 Deploy (optional)
- **Local**: already covered above.
- **GitHub + Streamlit Community Cloud**: push this repo to GitHub → add app in Streamlit Cloud, main file: `app/streamlit_app.py` → set **Secrets** or **Env Vars** if needed (not required here).

---
**Tip:** Keep it minimal at first. Once validated, you can add store-level detail, factory routing, or full material-constrained planning.
