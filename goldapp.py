import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import requests
from datetime import datetime

# Function to get current gold price (simulated)
def get_gold_price():
    # In a real app, you would call an API here
    # For demo purposes, we'll use a fixed value with some random variation
    return 5832.50  # Price per gram in INR as of example

# Function to calculate probability of default
def calculate_pd(cibil, monthly_income, work_exp, age, dti, tenure, existing_customer, agriculture):
    # This is a simplified model - in practice you would use a more sophisticated approach
    pd_score = 0
    
    # CIBIL score impact (higher is better)
    pd_score += (850 - cibil) / 850 * 0.5  # CIBIL ranges from 300-900
    
    # Monthly income impact (higher is better)
    if monthly_income < 25000:
        pd_score += 0.3
    elif monthly_income < 50000:
        pd_score += 0.2
    else:
        pd_score += 0.1
    
    # Work experience impact
    if work_exp < 2:
        pd_score += 0.2
    elif work_exp < 5:
        pd_score += 0.1
    
    # Age impact
    if age < 25 or age > 60:
        pd_score += 0.15
    elif age < 30 or age > 55:
        pd_score += 0.1
    
    # Debt-to-income impact
    pd_score += dti * 0.5
    
    # Tenure impact (longer is riskier)
    pd_score += tenure / 120 * 0.1
    
    # Existing customer (lower risk)
    if existing_customer:
        pd_score -= 0.1
    
    # Agriculture (higher risk)
    if agriculture:
        pd_score += 0.15
    
    # Convert score to probability (0-1 range)
    pd1 = 1 / (1 + np.exp(-pd_score))  # Logistic function to keep between 0-1
    
    # Cap at 30% max PD
    return min(pd1, 0.3)

# Function to calculate LTV
def calculate_ltv(cibil, monthly_income, work_exp, age, dti, tenure, existing_customer, agriculture):
    # Base LTV for gold loans is typically 60-80%
    base_ltv = 0.7
    
    # Adjust based on risk factors
    # CIBIL adjustment
    ltv_adjustment = (cibil - 600) / 250 * 0.1  # +10% for 850, -8% for 300
    
    # Income adjustment
    if monthly_income > 50000:
        ltv_adjustment += 0.05
    elif monthly_income < 25000:
        ltv_adjustment -= 0.05
    
    # Work experience adjustment
    if work_exp > 5:
        ltv_adjustment += 0.03
    
    # Age adjustment
    if 30 <= age <= 50:
        ltv_adjustment += 0.02
    
    # Existing customer adjustment
    if existing_customer:
        ltv_adjustment += 0.05
    
    # Agriculture adjustment
    if agriculture:
        ltv_adjustment -= 0.03
    
    # Calculate final LTV (cap between 60-85%)
    final_ltv = base_ltv + ltv_adjustment
    return max(min(final_ltv, 0.85), 0.6)

# Function to calculate loss given default
def calculate_lgd():
    # For gold loans, LGD is typically low since gold can be auctioned
    # We'll use 20% as a standard value (80% recovery)
    return 0.2

# Streamlit app layout
st.set_page_config(layout="wide", page_title="Gold Loan Pricing Calculator")

st.title("Gold Loan Pricing Calculator")

# Divide into two columns
col1, col2 = st.columns(2)

# Customer Profile Section
with col1:
    st.header("Customer Profile")
    
    customer_id = st.text_input("Customer ID", value="CUST12345")
    cibil = st.slider("CIBIL Score", 300, 900, 750)
    monthly_income = st.number_input("Monthly Income (₹)", min_value=0, value=50000)
    work_exp = st.number_input("Work Experience (years)", min_value=0, max_value=50, value=5)
    age = st.number_input("Age", min_value=18, max_value=80, value=35)
    dti = st.slider("Debt to Income Ratio", 0.0, 1.0, 0.3)
    tenure = st.number_input("Tenure of Loan (months)", min_value=1, max_value=120, value=12)
    existing_customer = st.checkbox("Existing Customer", value=True)
    agriculture = st.checkbox("Agriculture Sector", value=False)
    
    st.subheader("Gold Details")
    gold_weight = st.number_input("Gold Weight (grams)", min_value=0.0, value=50.0)
    gold_purity = st.selectbox("Gold Purity", ["24K", "22K", "18K", "14K"], index=1)

# Bank Data Section
with col2:
    st.header("Bank Parameters")
    
    risk_free_rate = st.number_input("Risk Free Rate", min_value=0.0, max_value=1.0, value=0.07, step=0.01)
    funding_spread = st.number_input("Funding Spread", min_value=0.0, max_value=1.0, value=0.015, step=0.001)
    capital_requirement = st.number_input("Capital Requirement", min_value=0.0, max_value=1.0, value=0.01, step=0.001)
    cost_capital = st.number_input("Cost of Capital", min_value=0.0, max_value=2.0, value=1.0, step=0.1)
    roe_target = st.number_input("ROE Target", min_value=0.0, max_value=1.0, value=0.15, step=0.01)
    operating_cost_rate = st.number_input("Operating Cost Rate", min_value=0.0, max_value=1.0, value=0.015, step=0.001)
    profit_margin = st.number_input("Profit Margin", min_value=0.0, max_value=1.0, value=0.025, step=0.001)

# Calculate results when button is pressed
if st.button("Calculate Loan Terms"):
    # Get current gold price
    gold_rate = get_gold_price()
    
    # Calculate purity multiplier
    purity_multiplier = {
        "24K": 1.0,
        "22K": 0.916,
        "18K": 0.75,
        "14K": 0.585
    }[gold_purity]
    
    # Calculate gold value
    gold_value = gold_weight * gold_rate * purity_multiplier
    
    # Calculate PD, LTV, LGD
    pd1 = calculate_pd(cibil, monthly_income, work_exp, age, dti, tenure, existing_customer, agriculture)
    ltv = calculate_ltv(cibil, monthly_income, work_exp, age, dti, tenure, existing_customer, agriculture)
    lgd = calculate_lgd()
    
    # Calculate loan amount
    loan_amount = ltv * gold_value
    
    # Calculate expected loss
    expected_loss = pd1 * lgd * loan_amount
    
    # Calculate intermediate metrics
    expected_loss_rate = expected_loss / loan_amount if loan_amount > 0 else 0
    amount_capital = loan_amount * capital_requirement
    capital_charge = amount_capital * cost_capital
    capital_charge_rate = capital_charge / loan_amount if loan_amount > 0 else 0
    
    # Calculate rates
    cost_funds = risk_free_rate + funding_spread
    break_even_rate = cost_funds + expected_loss_rate + capital_charge_rate + operating_cost_rate
    final_rate = break_even_rate + profit_margin
    
    # Display results
    st.header("Loan Terms")
    
    # Key metrics in columns
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Gold Rate (₹/gram)", f"{gold_rate:,.2f}")
        st.metric("Gold Value (₹)", f"{gold_value:,.2f}")
    
    with col2:
        st.metric("LTV Ratio", f"{ltv*100:.1f}%")
        st.metric("Loan Amount (₹)", f"{loan_amount:,.2f}")
    
    with col3:
        st.metric("PD", f"{pd1*100:.1f}%")
        st.metric("Expected Loss (₹)", f"{expected_loss:,.2f}")
    
    # Rate breakdown
    st.subheader("Interest Rate Breakdown")
    
    # Create waterfall chart data
    rate_components = {
        "Cost of Funds": cost_funds,
        "Expected Loss": expected_loss_rate,
        "Capital Charge": capital_charge_rate,
        "Operating Costs": operating_cost_rate,
        "Profit Margin": profit_margin
    }
    
    df_rates = pd.DataFrame({
        "Component": list(rate_components.keys()),
        "Value": list(rate_components.values()),
        "Cumulative": np.cumsum(list(rate_components.values()))
    })
    
    # Waterfall chart
    fig = px.bar(df_rates, 
                 x="Component", 
                 y="Value",
                 text=[f"{v*100:.2f}%" for v in df_rates["Value"]],
                 title="Interest Rate Components Breakdown")
    
    # Add line for cumulative rates
    fig.add_scatter(x=df_rates["Component"], 
                   y=df_rates["Cumulative"],
                   mode='lines+markers',
                   name="Cumulative Rate",
                   line=dict(color='red', width=2))
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Final rate display
    st.success(f"### Final Interest Rate: {final_rate*100:.2f}%")
    
    # Detailed calculations
    with st.expander("Show Detailed Calculations"):
        st.write(f"""
        **Gold Value Calculation:**
        - Gold Weight: {gold_weight} grams
        - Gold Purity: {gold_purity} ({purity_multiplier*100:.1f}% pure)
        - Gold Rate: ₹{gold_rate:,.2f}/gram
        - Value = {gold_weight}g × ₹{gold_rate:,.2f} × {purity_multiplier} = ₹{gold_value:,.2f}
        
        **Loan Amount:**
        - LTV: {ltv*100:.1f}%
        - Loan Amount = {ltv*100:.1f}% × ₹{gold_value:,.2f} = ₹{loan_amount:,.2f}
        
        **Risk Calculations:**
        - Probability of Default (PD): {pd1*100:.1f}%
        - Loss Given Default (LGD): {lgd*100:.1f}%
        - Expected Loss = {pd*100:.1f}% × {lgd*100:.1f}% × ₹{loan_amount:,.2f} = ₹{expected_loss:,.2f}
        - Expected Loss Rate = ₹{expected_loss:,.2f} / ₹{loan_amount:,.2f} = {expected_loss_rate*100:.2f}%
        
        **Capital Requirements:**
        - Capital Requirement: {capital_requirement*100:.1f}%
        - Amount Capital = {capital_requirement*100:.1f}% × ₹{loan_amount:,.2f} = ₹{amount_capital:,.2f}
        - Cost of Capital: {cost_capital*100:.1f}%
        - Capital Charge = ₹{amount_capital:,.2f} × {cost_capital*100:.1f}% = ₹{capital_charge:,.2f}
        - Capital Charge Rate = ₹{capital_charge:,.2f} / ₹{loan_amount:,.2f} = {capital_charge_rate*100:.2f}%
        
        **Rate Calculations:**
        - Cost of Funds = Risk Free Rate + Funding Spread = {risk_free_rate*100:.1f}% + {funding_spread*100:.1f}% = {cost_funds*100:.2f}%
        - Break Even Rate = Cost of Funds + Expected Loss Rate + Capital Charge Rate + Operating Cost Rate
                         = {cost_funds*100:.2f}% + {expected_loss_rate*100:.2f}% + {capital_charge_rate*100:.2f}% + {operating_cost_rate*100:.1f}% = {break_even_rate*100:.2f}%
        - Final Rate = Break Even Rate + Profit Margin = {break_even_rate*100:.2f}% + {profit_margin*100:.1f}% = {final_rate*100:.2f}%
        """)

# Add some info text
st.sidebar.info("""
**Gold Loan Pricing Model**

This calculator determines appropriate loan terms for gold-backed loans based on:
- Customer risk profile
- Gold collateral value
- Bank funding costs and capital requirements

The model calculates:
1. Loan-to-Value ratio based on customer risk
2. Probability of default
3. Expected loss
4. Break-even interest rate
5. Final interest rate with profit margin
""")
