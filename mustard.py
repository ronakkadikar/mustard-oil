import streamlit as st

def format_cr(n):
    try:
        n = float(n)
    except:
        return n
    return f"₹{n/1e7:.2f} Cr"

def format_inr(n):
    try:
        n = float(n)
    except:
        return n
    return f"₹{n:,.0f}"

st.set_page_config(page_title="Mustard Plant Dashboard", layout="wide")

st.markdown("""
    <style>
    .stApp {
        background-color: #e8f0fe;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🌱 Mustard Seed Processing Dashboard")

# --- Input Section: Grouped ---
st.header("Inputs")

colq, colr, coly, colm = st.columns([1.5,1.2,1.2,1.2])

with colq:
    st.subheader("Quantities & Yields")
    seed_input = st.number_input("Seed Input (MT)", min_value=0.0, value=200.0, format="%.2f")
    kg_oil_yield_pct = st.number_input("Kachi Ghani Oil Yield (% of seeds)", min_value=0.0, max_value=100.0, value=18.0, format="%.2f")
    exp_oil_yield_pct = st.number_input("Expeller Oil Yield (% of seeds)", min_value=0.0, max_value=100.0, value=15.0, format="%.2f")
    market_oil = st.number_input("Market-Bought Oil (MT)", min_value=0.0, value=0.0, format="%.2f")
    moc_base_yield_pct = 100.0 - (kg_oil_yield_pct + exp_oil_yield_pct)
    st.markdown(f"**MoC Base Yield (% of seeds):** {moc_base_yield_pct:.2f}")

with colr:
    st.subheader("Rates / Prices")
    seed_price = st.number_input("Seed Purchase Price (₹/MT)", min_value=0.0, value=57000.0, format="%.2f")
    hoarded_rm_rate = st.number_input("Hoarded RM Rate (₹/MT)", min_value=0.0, value=57000.0, format="%.2f")
    oil_sell_price = st.number_input("Oil Blend Sell Price (₹/MT)", min_value=0.0, value=138000.0, format="%.2f")
    exp_oil_sell_price = st.number_input("Expeller Oil Sell Price (₹/MT)", min_value=0.0, value=135500.0, format="%.2f")
    market_oil_price = st.number_input("Market-Bought Oil Price (₹/MT)", min_value=0.0, value=133000.0, format="%.2f")
    moc_sell_price = st.number_input("MoC Sell Price (₹/MT)", min_value=0.0, value=22500.0, format="%.2f")

with coly:
    st.subheader("Yields / Pungency")
    kg_pungency = st.number_input("Kachi Ghani Oil Pungency (%)", min_value=0.0, value=0.4, format="%.4f")
    exp_pungency = st.number_input("Expeller Oil Pungency (%)", min_value=0.0, value=0.12, format="%.4f")

with colm:
    st.subheader("MoC Enhancement")
    water_pct = st.number_input("Water Added (% of seed input)", min_value=0.0, value=2.0, format="%.2f")
    water_cost = st.number_input("Water Cost (₹/kg)", min_value=0.0, value=1.0, format="%.2f")
    salt_pct = st.number_input("Salt Added (% of seed input)", min_value=0.0, value=3.0, format="%.2f")
    salt_cost = st.number_input("Salt Cost (₹/kg)", min_value=0.0, value=5.0, format="%.2f")

st.markdown("---")

# --- Section: Processing & Revenue Logic ---
kg_oil = seed_input * (kg_oil_yield_pct / 100)
exp_oil = seed_input * (exp_oil_yield_pct / 100)
total_oil = kg_oil + exp_oil + market_oil

# Blend Pungency Calculation
blend_pungency = (
    (kg_oil * kg_pungency) +
    (exp_oil * exp_pungency) +
    (market_oil * 0)
) / total_oil if total_oil else 0.0

st.subheader("Blend Pungency")
st.markdown(f"**Blend Pungency:** {blend_pungency:.4f} %")

# --- Pungency Adjustment Logic ---
pungency_ok = abs(blend_pungency - 0.27) < 1e-6 or blend_pungency == 0.27

recommendation_msg = ""
exp_oil_used_in_blend = exp_oil
exp_oil_sold_separately = 0
market_oil_needed = 0
market_oil_profit = 0
exp_oil_loss = 0

if blend_pungency < 0.27 and total_oil > 0:
    if kg_pungency == exp_pungency:
        max_exp_oil_blend = 0
    else:
        max_exp_oil_blend = max(0, ((kg_oil * (kg_pungency - 0.27)) / (0.27 - exp_pungency)))
        max_exp_oil_blend = min(exp_oil, max_exp_oil_blend)
    exp_oil_used_in_blend = max_exp_oil_blend
    exp_oil_sold_separately = exp_oil - exp_oil_used_in_blend
    exp_oil_loss = exp_oil_sold_separately * (oil_sell_price - exp_oil_sell_price)
    recommendation_msg = (
        f"⚠️ **Blend pungency is below 0.27.**\n\n"
        f"To achieve compliance, reduce expeller oil in blend to **{exp_oil_used_in_blend:.2f} MT**. "
        f"Excess expeller oil (**{exp_oil_sold_separately:.2f} MT**) will be sold separately, resulting in a loss of "
        f"{format_inr(exp_oil_loss)} per day."
    )
elif blend_pungency > 0.27 and total_oil > 0:
    numerator = (kg_oil * kg_pungency) + (exp_oil * exp_pungency)
    denominator = 0.27
    if denominator > 0:
        market_oil_needed = max(0, (numerator / denominator) - (kg_oil + exp_oil))
    else:
        market_oil_needed = 0
    market_oil_profit = (oil_sell_price - market_oil_price) * market_oil_needed
    recommendation_msg = (
        f"ℹ️ **Blend pungency is above 0.27.**\n\n"
        f"To optimize cost, you may add **{market_oil_needed:.2f} MT** of market oil (0% pungency) to bring the blend to 0.27. "
        f"This could add a profit of {format_inr(market_oil_profit)} per day. "
        f"(This is a recommendation; you may choose to act or ignore.)"
    )
else:
    recommendation_msg = "✅ **Blend pungency is at the required 0.27. No adjustment needed.**"

st.info(recommendation_msg)

# --- Revenue Calculations ---
oil_blend = kg_oil + exp_oil_used_in_blend + market_oil
oil_blend_revenue = oil_blend * oil_sell_price
exp_oil_revenue = exp_oil_sold_separately * exp_oil_sell_price

# MoC Enhancement
base_moc = seed_input * (moc_base_yield_pct / 100)
water_moc = seed_input * (water_pct / 100)
salt_moc = seed_input * (salt_pct / 100)
enhanced_moc = base_moc + water_moc + salt_moc
moc_enhance_cost = (water_moc * water_cost) + (salt_moc * salt_cost)
moc_revenue = enhanced_moc * moc_sell_price

# --- Section: Costing & Margins ---
processing_cost = st.number_input("Processing Cost (₹/MT)", min_value=0.0, value=1300.0, format="%.2f")
other_variable_costs = st.number_input("Other Variable Costs (₹/MT)", min_value=0.0, value=2300.0, format="%.2f")
other_expenses = st.number_input("Other Expenses (₹/day)", min_value=0.0, value=0.0, format="%.2f")

# COGS Calculation (Seed, Market Oil, MoC Enhancement)
cogs = (seed_input * seed_price) + (market_oil * market_oil_price) + moc_enhance_cost
cogs_percent = (cogs / (oil_blend_revenue + exp_oil_revenue + moc_revenue) * 100) if (oil_blend_revenue + exp_oil_revenue + moc_revenue) else 0

# GM Calculation
gm = oil_blend_revenue + exp_oil_revenue + moc_revenue - cogs
gm_percent = (gm / (oil_blend_revenue + exp_oil_revenue + moc_revenue) * 100) if (oil_blend_revenue + exp_oil_revenue + moc_revenue) else 0

# Processing Cost Calculation
processing_cost_total = seed_input * processing_cost
processing_cost_percent = (processing_cost_total / (oil_blend_revenue + exp_oil_revenue + moc_revenue) * 100) if (oil_blend_revenue + exp_oil_revenue + moc_revenue) else 0

# CM Calculation
cm = gm - processing_cost_total
cm_percent = (cm / (oil_blend_revenue + exp_oil_revenue + moc_revenue) * 100) if (oil_blend_revenue + exp_oil_revenue + moc_revenue) else 0

# Variable Cost Calculation
variable_cost_total = seed_input * other_variable_costs
variable_cost_percent = (variable_cost_total / (oil_blend_revenue + exp_oil_revenue + moc_revenue) * 100) if (oil_blend_revenue + exp_oil_revenue + moc_revenue) else 0

# EBITDA Calculation
ebitda = cm - variable_cost_total - other_expenses
ebitda_percent = (ebitda / (oil_blend_revenue + exp_oil_revenue + moc_revenue) * 100) if (oil_blend_revenue + exp_oil_revenue + moc_revenue) else 0

# --- Monthly & Annual Projections ---
prod_days = st.number_input("Production Days per Month", min_value=1, value=24)
capex = st.number_input("Capex (₹)", min_value=0.0, value=170000000.0, format="%.2f")
depreciation = capex / 96
st.markdown(f"**Depreciation (₹/month):** {depreciation:,.0f}")
tax_rate = st.number_input("Tax Rate (%)", min_value=0.0, max_value=100.0, value=25.0, format="%.2f")
other_assets = st.number_input("Other Assets (₹)", min_value=0.0, value=0.0, format="%.2f")

# Annualization
annual_gm = gm * prod_days * 12
annual_cm = cm * prod_days * 12
annual_ebitda = ebitda * prod_days * 12
annual_processing_cost = processing_cost_total * prod_days * 12
annual_variable_cost = variable_cost_total * prod_days * 12
annual_other_expenses = other_expenses * prod_days * 12

# Interest Calculation (12% p.a. on WC + Capex)
# Working Capital section is below, so interest is calculated after total_wc is calculated

# --- Working Capital & Warehouse Financing ---
st.header("Working Capital & Warehouse Financing")

col15, col16, col17 = st.columns(3)
with col15:
    hoard_months = st.number_input("Raw Material Hoard (months)", min_value=0.0, value=6.0)
    financed_pct = st.number_input("% Financed (RM Hoard)", min_value=0.0, max_value=100.0, value=80.0)
    warehouse_int_rate = st.number_input("Warehouse Finance Interest Rate (% p.a.)", min_value=0.0, max_value=100.0, value=12.0)
    rm_safety_stock_days = st.number_input("RM Safety Stock (days)", min_value=0, value=24)
    creditors_days = st.number_input("Creditors Days", min_value=0, value=15)

with col16:
    fg_oil_ss_days = st.number_input("FG (Oil) Safety Stock (days)", min_value=0, value=15)
    fg_moc_ss_days = st.number_input("FG (MoC) Safety Stock (days)", min_value=0, value=5)

with col17:
    debtor_oil_days = st.number_input("Oil Debtor Cycle (days)", min_value=0, value=5)
    debtor_moc_days = st.number_input("MoC Debtor Cycle (days)", min_value=0, value=5)

daily_seed_consumption = seed_input
monthly_seed_consumption = daily_seed_consumption * prod_days

# RM Inventory
rm_hoarded_qty = monthly_seed_consumption * hoard_months
rm_hoarded_val = rm_hoarded_qty * hoarded_rm_rate
rm_safety_stock_qty = daily_seed_consumption * rm_safety_stock_days
rm_safety_stock_val = rm_safety_stock_qty * seed_price

# FG Inventory
daily_oil_output = oil_blend
daily_moc_output = enhanced_moc
fg_oil_inventory = daily_oil_output * fg_oil_ss_days * oil_sell_price
fg_moc_inventory = daily_moc_output * fg_moc_ss_days * moc_sell_price

# Debtors
oil_debtors = daily_oil_output * oil_sell_price * debtor_oil_days
moc_debtors = daily_moc_output * moc_sell_price * debtor_moc_days
total_debtors = oil_debtors + moc_debtors

# Creditors
creditors = daily_seed_consumption * creditors_days * seed_price

# Inventory
total_inventory = rm_hoarded_val + rm_safety_stock_val + fg_oil_inventory + fg_moc_inventory

# Total Working Capital
total_wc = total_inventory + total_debtors - creditors

# Interest Calculation (12% p.a. on WC + Capex)
annual_interest = (total_wc + capex) * 0.12
monthly_interest = annual_interest / 12
daily_interest = annual_interest / (12 * prod_days)

# Depreciation
annual_depreciation = depreciation * 12

# Annual PBT
annual_pbt = annual_ebitda - annual_depreciation - annual_interest

# --- OUTPUT SECTION ---

st.header("Margin Analysis (All values in ₹ Cr unless otherwise specified)")
st.markdown("#### Daily | Monthly | Annual")

st.write(f"**Revenue:** {format_cr(oil_blend_revenue + exp_oil_revenue + moc_revenue)} | {format_cr((oil_blend_revenue + exp_oil_revenue + moc_revenue) * prod_days)} | {format_cr((oil_blend_revenue + exp_oil_revenue + moc_revenue) * prod_days * 12)}")
st.write(f"**COGS:** {format_cr(cogs)} ({cogs_percent:.2f}%) | {format_cr(cogs * prod_days)} | {format_cr(cogs * prod_days * 12)}")
st.write(f"**GM:** {format_cr(gm)} ({gm_percent:.2f}%) | {format_cr(gm * prod_days)} | {format_cr(annual_gm)}")
st.write(f"**Processing Cost:** {format_cr(processing_cost_total)} ({processing_cost_percent:.2f}%) | {format_cr(processing_cost_total * prod_days)} | {format_cr(annual_processing_cost)}")
st.write(f"**CM:** {format_cr(cm)} ({cm_percent:.2f}%) | {format_cr(cm * prod_days)} | {format_cr(annual_cm)}")
st.write(f"**Variable Cost:** {format_cr(variable_cost_total)} ({variable_cost_percent:.2f}%) | {format_cr(variable_cost_total * prod_days)} | {format_cr(annual_variable_cost)}")
st.write(f"**Other Expenses:** {format_cr(other_expenses)} | {format_cr(other_expenses * prod_days)} | {format_cr(annual_other_expenses)}")
st.write(f"**EBITDA:** {format_cr(ebitda)} ({ebitda_percent:.2f}%) | {format_cr(ebitda * prod_days)} | {format_cr(annual_ebitda)}")
st.write(f"**Interest (Annual):** {format_cr(annual_interest)}")
st.write(f"**Depreciation (Annual):** {format_cr(annual_depreciation)}")
st.write(f"**Annual PBT:** {format_cr(annual_pbt)}")

st.markdown("---")

st.header("Working Capital Breakup")

colA, colB, colC, colD = st.columns(4)
with colA:
    st.metric("Debtors (₹ Cr)", format_cr(total_debtors))
with colB:
    st.metric("Creditors (₹ Cr)", format_cr(creditors))
with colC:
    st.metric("Inventory (₹ Cr)", format_cr(total_inventory))
with colD:
    st.metric("Total Working Capital (₹ Cr)", format_cr(total_wc))

st.markdown("---")

st.header("ROCE Calculation")
roce_numerator = annual_ebitda - annual_depreciation - annual_interest
roce_denominator = capex + total_wc + other_assets
roce_percent = (roce_numerator / roce_denominator) * 100 if roce_denominator else 0

st.markdown(f"""
- **EBITDA (Annual):** {format_cr(annual_ebitda)}
- **Depreciation (Annual):** {format_cr(annual_depreciation)}
- **Interest (Annual):** {format_cr(annual_interest)}
- **Annual PBT:** {format_cr(annual_pbt)}
- **Capex:** {format_cr(capex)}
- **Working Capital:** {format_cr(total_wc)}
- **Other Assets:** {format_cr(other_assets)}
- **ROCE (%):** **{roce_percent:.2f}%**
""")

st.info("All calculations update in real time as you change inputs. All numbers are shown in ₹ Cr for clarity.")

