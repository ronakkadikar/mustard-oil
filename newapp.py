import streamlit as st
import pandas as pd
import plotly.express as px

# --- Page Configuration and Helper Function ---
st.set_page_config(layout="wide", page_title="Mustard Oil Business Dashboard")

def format_indian(num):
    """Formats a number into the Indian numbering system for better readability."""
    if not isinstance(num, (int, float)):
        return num
    num_str = f"{abs(num):,.0f}"
    parts = num_str.split('.')
    integer_part = parts[0].replace(',', '')
    if len(integer_part) > 3:
        last_three = integer_part[-3:]
        other_digits = integer_part[:-3]
        if other_digits:
            formatted_other_digits = ','.join([other_digits[max(0, i-2):i] for i in range(len(other_digits), 0, -2)][::-1])
            formatted_num = f"{formatted_other_digits},{last_three}"
        else:
            formatted_num = last_three
    else:
        formatted_num = integer_part
    return '-' + formatted_num if num < 0 else formatted_num

st.title("🛢️ Mustard Oil Financial & Operational Dashboard")
st.markdown("An interactive dashboard for daily, monthly, and annual analysis of a mustard oil processing business.")

# --- Sidebar for All User Inputs ---
with st.sidebar:
    st.header("⚙️ Business & Financial Inputs")

    with st.expander("Production, Yields & Prices", expanded=True):
        seed_input_mt = st.number_input("Daily Seed Input (MT)", value=200.0)
        kachi_ghani_yield_pct = st.slider("Kachi Ghani Oil Yield (%)", 0, 100, 18)
        expeller_yield_pct = st.slider("Expeller Oil Yield (%)", 0, 100, 15)
        seed_purchase_price = st.number_input("Seed Purchase Price (₹/MT)", value=57000)
        oil_blend_sell_price = st.number_input("Oil Blend Sell Price (₹/MT)", value=138000)
        moc_sell_price = st.number_input("MoC Sell Price (₹/MT)", value=22500)

    with st.expander("Costs & Expenses", expanded=True):
        processing_cost_per_mt = st.number_input("Processing Cost (₹/MT of Seed)", value=1300)
        other_variable_costs_per_mt = st.number_input("Other Variable Costs (₹/MT of Seed)", value=2300)
        other_expenses_daily = st.number_input("Other Fixed Expenses (₹/day)", value=50000)
        production_days_per_month = st.number_input("Production Days per Month", value=24)

    with st.expander("Pungency & MoC Enhancement", expanded=True):
        kachi_ghani_pungency = st.slider("Kachi Ghani Oil Pungency (%)", 0.0, 1.0, 0.40, step=0.01)
        expeller_oil_pungency = st.slider("Expeller Oil Pungency (%)", 0.0, 1.0, 0.12, step=0.01)
        expeller_oil_sell_price = st.number_input("Expeller Oil Sell Price (₹/MT)", value=135500)
        market_bought_oil_price = st.number_input("Market-Bought Oil Price (₹/MT)", value=133000)
        water_added_pct = st.slider("Water Added to MoC (% of seed)", 0, 10, 2)
        water_cost_per_kg = st.number_input("Water Cost (₹/kg)", value=1)
        salt_added_pct = st.slider("Salt Added to MoC (% of seed)", 0, 10, 3)
        salt_cost_per_kg = st.number_input("Salt Cost (₹/kg)", value=5)

    with st.expander("Capex, Tax & Working Capital", expanded=True):
        capex = st.number_input("Capex (₹)", value=170000000)
        depreciation_years = st.number_input("Depreciation Period (Years)", min_value=1, value=8)
        tax_rate_pct = st.slider("Tax Rate (%)", 0, 50, 25)
        other_assets = st.number_input("Other Assets (₹)", value=10000000)
        rm_hoard_months = st.number_input("Raw Material Hoard (months)", value=6)
        hoarded_rm_rate = st.number_input("Hoarded RM Rate (₹/MT)", value=57000)
        rm_safety_stock_days = st.number_input("RM Safety Stock (days)", value=24)
        fg_oil_safety_days = st.number_input("FG (Oil) Safety Stock (days)", value=15)
        fg_moc_safety_days = st.number_input("FG (MoC) Safety Stock (days)", value=5)
        oil_debtor_days = st.number_input("Oil Debtor Cycle (days)", value=5)
        moc_debtor_days = st.number_input("MoC Debtor Cycle (days)", value=5)
        creditor_days = st.number_input("Creditors Days", value=15)

    with st.expander("🏭 Solvex Plant Synergy Inputs", expanded=False):
        moc_consumed_perc = st.slider("% of MOC Consumed In-House", 0, 100, 70)
        logistics_saved_per_ton = st.number_input("Logistics Saved (₹/Ton of MOC)", value=500)
        labor_saved_nos = st.number_input("Labor Headcount Saved (Daily)", value=10)
        labor_cost_per_head_daily = st.number_input("Cost per Labor Head (₹/Day)", value=700)
        brokerage_saved_per_ton = st.number_input("Brokerage Saved (₹/Ton of MOC)", value=150)


# --- Calculation Engine ---
@st.cache_data
def calculate_metrics(inputs):
    # Unpack all inputs into local variables for calculations
    for key, value in inputs.items():
        locals()[key] = value

    kachi_ghani_yield = inputs['kachi_ghani_yield_pct'] / 100
    expeller_yield = inputs['expeller_yield_pct'] / 100
    moc_base_yield = 1 - (kachi_ghani_yield + expeller_yield)
    min_pungency_req = 0.27
    
    kachi_ghani_oil_produced = inputs['seed_input_mt'] * kachi_ghani_yield
    expeller_oil_produced = inputs['seed_input_mt'] * expeller_yield
    total_produced_oil = kachi_ghani_oil_produced + expeller_oil_produced
    initial_blend_pungency = (kachi_ghani_oil_produced * inputs['kachi_ghani_pungency'] + expeller_oil_produced * inputs['expeller_oil_pungency']) / total_produced_oil if total_produced_oil > 0 else 0
    
    exp_oil_used_in_blend, exp_oil_sold_separately, market_oil_to_add = expeller_oil_produced, 0, 0
    daily_pungency_gain_loss, pungency_recommendation = 0, ""

    if initial_blend_pungency < min_pungency_req and total_produced_oil > 0:
        denominator = min_pungency_req - inputs['expeller_oil_pungency']
        if denominator != 0:
            exp_oil_used_in_blend = max(0, (kachi_ghani_oil_produced * (inputs['kachi_ghani_pungency'] - min_pungency_req)) / denominator)
        exp_oil_sold_separately = expeller_oil_produced - exp_oil_used_in_blend
        daily_pungency_gain_loss = -exp_oil_sold_separately * (inputs['oil_blend_sell_price'] - inputs['expeller_oil_sell_price'])
        pungency_recommendation = f"🔴 **Pungency Low ({initial_blend_pungency:.2f}%)**: Sell {exp_oil_sold_separately:.2f} MT of Expeller Oil separately. Est. daily opportunity loss: ₹ {format_indian(abs(daily_pungency_gain_loss))}."
    elif initial_blend_pungency > min_pungency_req and total_produced_oil > 0:
        if min_pungency_req > 0:
            market_oil_to_add = max(0, ((kachi_ghani_oil_produced * inputs['kachi_ghani_pungency'] + expeller_oil_produced * inputs['expeller_oil_pungency']) / min_pungency_req) - total_produced_oil)
        daily_pungency_gain_loss = market_oil_to_add * (inputs['oil_blend_sell_price'] - inputs['market_bought_oil_price'])
        pungency_recommendation = f"🟢 **Pungency High ({initial_blend_pungency:.2f}%)**: Add {market_oil_to_add:.2f} MT of Market Oil to optimize. Est. daily profit opportunity: ₹ {format_indian(daily_pungency_gain_loss)}."
    else:
        pungency_recommendation = f"✅ **Pungency Compliant ({initial_blend_pungency:.2f}%)**: No action needed."

    final_oil_blend_mt = kachi_ghani_oil_produced + exp_oil_used_in_blend + market_oil_to_add
    water_added_mt = inputs['seed_input_mt'] * (inputs['water_added_pct'] / 100)
    salt_added_mt = inputs['seed_input_mt'] * (inputs['salt_added_pct'] / 100)
    enhanced_moc_mt = (inputs['seed_input_mt'] * moc_base_yield) + water_added_mt + salt_added_mt
    
    revenue_oil_blend = final_oil_blend_mt * inputs['oil_blend_sell_price']
    revenue_expeller_separate = exp_oil_sold_separately * inputs['expeller_oil_sell_price']
    revenue_moc = enhanced_moc_mt * inputs['moc_sell_price']
    daily_revenue = revenue_oil_blend + revenue_expeller_separate + revenue_moc

    cost_seed = inputs['seed_input_mt'] * inputs['seed_purchase_price']
    cost_market_oil = market_oil_to_add * inputs['market_bought_oil_price']
    cost_moc_enhancement = (water_added_mt * 1000 * inputs['water_cost_per_kg']) + (salt_added_mt * 1000 * inputs['salt_cost_per_kg'])
    daily_cogs = cost_seed + cost_market_oil + cost_moc_enhancement
    daily_gm = daily_revenue - daily_cogs
    daily_processing_cost = inputs['seed_input_mt'] * inputs['processing_cost_per_mt']
    daily_cm = daily_gm - daily_processing_cost
    daily_variable_cost = inputs['seed_input_mt'] * inputs['other_variable_costs_per_mt']
    daily_ebitda = daily_cm - daily_variable_cost - inputs['other_expenses_daily']
    
    annual_production_days = inputs['production_days_per_month'] * 12
    annual_ebitda = daily_ebitda * annual_production_days
    
    monthly_seed_consumption = inputs['seed_input_mt'] * inputs['production_days_per_month']
    rm_hoarded_value = monthly_seed_consumption * inputs['rm_hoard_months'] * inputs['hoarded_rm_rate']
    rm_safety_stock_value = inputs['seed_input_mt'] * inputs['rm_safety_stock_days'] * inputs['seed_purchase_price']
    inventory_rm = rm_hoarded_value + rm_safety_stock_value
    
    total_daily_oil_revenue = revenue_oil_blend + revenue_expeller_separate
    total_daily_oil_qty = final_oil_blend_mt + exp_oil_sold_separately
    avg_oil_price = total_daily_oil_revenue / total_daily_oil_qty if total_daily_oil_qty > 0 else 0
    fg_oil_inventory_value = total_daily_oil_qty * avg_oil_price * inputs['fg_oil_safety_days']
    fg_moc_inventory_value = enhanced_moc_mt * inputs['moc_sell_price'] * inputs['fg_moc_safety_days']
    inventory_fg = fg_oil_inventory_value + fg_moc_inventory_value
    total_inventory = inventory_rm + inventory_fg

    debtors_oil = total_daily_oil_revenue * inputs['oil_debtor_days']
    debtors_moc = revenue_moc * inputs['moc_debtor_days']
    total_debtors = debtors_oil + debtors_moc
    total_creditors = inputs['seed_input_mt'] * inputs['seed_purchase_price'] * inputs['creditor_days']
    total_wc = total_inventory + total_debtors - total_creditors

    annual_interest = (total_wc + inputs['capex']) * 0.12
    annual_depreciation = inputs['capex'] / inputs['depreciation_years'] if inputs['depreciation_years'] > 0 else 0
    annual_pbt = annual_ebitda - annual_depreciation - annual_interest
    annual_tax = max(0, annual_pbt * (inputs['tax_rate_pct'] / 100))
    annual_pat = annual_pbt - annual_tax

    financed_rm_hoard_value = rm_hoarded_value * 0.80
    wc_excl_financed_rm = total_wc - financed_rm_hoard_value
    capital_employed_incl_finance = inputs['capex'] + total_wc + inputs['other_assets']
    capital_employed_excl_finance = inputs['capex'] + wc_excl_financed_rm + inputs['other_assets']
    
    roce_pbt_incl = (annual_pbt / capital_employed_incl_finance) * 100 if capital_employed_incl_finance != 0 else 0
    roce_pbt_excl = (annual_pbt / capital_employed_excl_finance) * 100 if capital_employed_excl_finance != 0 else 0
    roce_ebitda_incl = (annual_ebitda / capital_employed_incl_finance) * 100 if capital_employed_incl_finance != 0 else 0
    roce_ebitda_excl = (annual_ebitda / capital_employed_excl_finance) * 100 if capital_employed_excl_finance != 0 else 0

    moc_consumed_inhouse_mt = enhanced_moc_mt * (inputs['moc_consumed_perc'] / 100)
    daily_logistics_saving = moc_consumed_inhouse_mt * inputs['logistics_saved_per_ton']
    daily_labor_saving = inputs['labor_saved_nos'] * inputs['labor_cost_per_head_daily']
    daily_brokerage_saving = moc_consumed_inhouse_mt * inputs['brokerage_saved_per_ton']
    total_daily_solvex_saving = daily_logistics_saving + daily_labor_saving + daily_brokerage_saving
    
    # --- FIX: Explicitly define the dictionary to be returned ---
    return {
        "production_days_per_month": inputs['production_days_per_month'], # Key that was missing
        "annual_production_days": annual_production_days,
        "daily_revenue": daily_revenue, "daily_cogs": daily_cogs, "daily_gm": daily_gm, "daily_ebitda": daily_ebitda,
        "pungency_recommendation": pungency_recommendation,
        "annual_ebitda": annual_ebitda, "annual_depreciation": annual_depreciation, "annual_interest": annual_interest,
        "annual_pbt": annual_pbt, "annual_tax": annual_tax, "annual_pat": annual_pat,
        "total_inventory": total_inventory, "total_debtors": total_debtors, "total_creditors": total_creditors,
        "total_wc": total_wc,
        "roce_pbt_incl": roce_pbt_incl, "roce_pbt_excl": roce_pbt_excl,
        "roce_ebitda_incl": roce_ebitda_incl, "roce_ebitda_excl": roce_ebitda_excl,
        "total_daily_solvex_saving": total_daily_solvex_saving, "daily_logistics_saving": daily_logistics_saving,
        "daily_labor_saving": daily_labor_saving, "daily_brokerage_saving": daily_brokerage_saving
    }

# --- Collect Inputs & Run Calculations ---
input_dict = {
    'seed_input_mt': seed_input_mt, 'kachi_ghani_yield_pct': kachi_ghani_yield_pct, 'expeller_yield_pct': expeller_yield_pct,
    'seed_purchase_price': seed_purchase_price, 'oil_blend_sell_price': oil_blend_sell_price, 'moc_sell_price': moc_sell_price,
    'processing_cost_per_mt': processing_cost_per_mt, 'other_variable_costs_per_mt': other_variable_costs_per_mt,
    'other_expenses_daily': other_expenses_daily, 'production_days_per_month': production_days_per_month,
    'kachi_ghani_pungency': kachi_ghani_pungency, 'expeller_oil_pungency': expeller_oil_pungency,
    'expeller_oil_sell_price': expeller_oil_sell_price, 'market_bought_oil_price': market_bought_oil_price,
    'water_added_pct': water_added_pct, 'water_cost_per_kg': water_cost_per_kg, 'salt_added_pct': salt_added_pct, 'salt_cost_per_kg': salt_cost_per_kg,
    'capex': capex, 'depreciation_years': depreciation_years, 'tax_rate_pct': tax_rate_pct, 'other_assets': other_assets,
    'rm_hoard_months': rm_hoard_months, 'hoarded_rm_rate': hoarded_rm_rate, 'rm_safety_stock_days': rm_safety_stock_days,
    'fg_oil_safety_days': fg_oil_safety_days, 'fg_moc_safety_days': fg_moc_safety_days, 'oil_debtor_days': oil_debtor_days,
    'moc_debtor_days': moc_debtor_days, 'creditor_days': creditor_days, 'moc_consumed_perc': moc_consumed_perc,
    'logistics_saved_per_ton': logistics_saved_per_ton, 'labor_saved_nos': labor_saved_nos,
    'labor_cost_per_head_daily': labor_cost_per_head_daily, 'brokerage_saved_per_ton': brokerage_saved_per_ton
}
metrics = calculate_metrics(input_dict)

# --- Main Dashboard Display ---

st.subheader("Pungency Compliance & Course Correction")
if "🔴" in metrics["pungency_recommendation"]: st.warning(metrics["pungency_recommendation"])
elif "🟢" in metrics["pungency_recommendation"]: st.success(metrics["pungency_recommendation"])
else: st.info(metrics["pungency_recommendation"])

st.subheader("Financial Performance Analysis")
daily_tab, monthly_tab, annual_tab = st.tabs(["📊 Daily View", "📅 Monthly View", "🗓️ Annual View"])

with daily_tab:
    cols = st.columns(4)
    cols[0].metric("Daily Revenue", f"₹ {metrics['daily_revenue']/1e5:.2f} L")
    cols[1].metric("Daily EBITDA", f"₹ {metrics['daily_ebitda']/1e5:.2f} L")
    cols[2].metric("Gross Margin %", f"{metrics['daily_gm']/metrics['daily_revenue']*100 if metrics['daily_revenue'] else 0:.1f}%")
    cols[3].metric("EBITDA Margin %", f"{metrics['daily_ebitda']/metrics['daily_revenue']*100 if metrics['daily_revenue'] else 0:.1f}%")

with monthly_tab:
    cols = st.columns(2)
    cols[0].metric("Monthly Revenue", f"₹ {metrics['daily_revenue'] * metrics['production_days_per_month'] / 1e7:.2f} Cr")
    cols[1].metric("Monthly EBITDA", f"₹ {metrics['daily_ebitda'] * metrics['production_days_per_month'] / 1e7:.2f} Cr")

with annual_tab:
    cols = st.columns(4)
    cols[0].metric("Annual Revenue", f"₹ {metrics['daily_revenue'] * metrics['annual_production_days'] / 1e7:.2f} Cr")
    cols[1].metric("Annual EBITDA", f"₹ {metrics['annual_ebitda'] / 1e7:.2f} Cr")
    cols[2].metric("Annual PBT", f"₹ {metrics['annual_pbt'] / 1e7:.2f} Cr")
    cols[3].metric("Annual PAT", f"₹ {metrics['annual_pat'] / 1e7:.2f} Cr")
    
    st.markdown("##### Annual Profit & Loss Statement")
    pnl_df_annual = pd.DataFrame({
        "Metric": ["Revenue", "COGS", "Gross Margin", "EBITDA", "Depreciation", "Interest", "PBT", "Tax", "PAT (Net Profit)"],
        "Value (₹ Cr)": [
            metrics['daily_revenue'] * metrics['annual_production_days'] / 1e7,
            metrics['daily_cogs'] * metrics['annual_production_days'] / 1e7,
            metrics['daily_gm'] * metrics['annual_production_days'] / 1e7,
            metrics['annual_ebitda'] / 1e7,
            -metrics['annual_depreciation'] / 1e7, -metrics['annual_interest'] / 1e7,
            metrics['annual_pbt'] / 1e7, -metrics['annual_tax'] / 1e7, metrics['annual_pat'] / 1e7,
        ]
    })
    st.dataframe(pnl_df_annual.style.format({"Value (₹ Cr)": "{:,.2f}"}), use_container_width=True)

st.divider()
wc_col, roce_col = st.columns([1, 1])

with wc_col:
    st.subheader("Working Capital Analysis")
    st.metric("Total Working Capital", f"₹ {metrics['total_wc']/1e7:.2f} Cr")
    wc_data = {'Component': ['Inventory (RM + FG)', 'Debtors (Oil + MoC)', 'Creditors'], 'Value (₹ Cr)': [metrics['total_inventory'] / 1e7, metrics['total_debtors'] / 1e7, -metrics['total_creditors'] / 1e7]}
    wc_df = pd.DataFrame(wc_data)
    fig = px.bar(wc_df, x='Component', y='Value (₹ Cr)', title='Working Capital Components', color='Component', text_auto='.2f', color_discrete_map={'Creditors': '#d62728'})
    fig.update_layout(showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

with roce_col:
    st.subheader("Return on Capital Employed (ROCE)")
    roce1, roce2 = st.columns(2)
    with roce1:
        st.info("**On PBT Basis**")
        st.metric("Incl. Financed RM", f"{metrics['roce_pbt_incl']:.2f}%")
        st.metric("Excl. Financed RM", f"{metrics['roce_pbt_excl']:.2f}%")
    with roce2:
        st.info("**On EBITDA Basis**")
        st.metric("Incl. Financed RM", f"{metrics['roce_ebitda_incl']:.2f}%")
        st.metric("Excl. Financed RM", f"{metrics['roce_ebitda_excl']:.2f}%")

st.divider()
st.subheader("🏭 Solvex Plant Synergy Savings")
col1, col2 = st.columns(2)
col1.metric("Total Daily Savings", f"₹ {format_indian(metrics['total_daily_solvex_saving'])}")
col2.metric("Total Monthly Savings", f"₹ {format_indian(metrics['total_daily_solvex_saving'] * metrics['production_days_per_month'])}")
st.markdown("##### Daily Savings Breakdown")
savings_df = pd.DataFrame({"Saving Component": ["Logistics Saving", "Labor Saving", "Brokerage Saving"], "Value (₹)": [metrics['daily_logistics_saving'], metrics['daily_labor_saving'], metrics['daily_brokerage_saving']]})
st.dataframe(savings_df.style.format({"Value (₹)": format_indian}), use_container_width=True)
