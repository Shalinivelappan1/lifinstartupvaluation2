import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="Startup Valuation Lab", layout="wide")

st.title("🚀 Startup Valuation Lab (A/B/C Comparison)")
st.write("Monte Carlo simulation + decision analytics for fintech startup valuation")

# -----------------------------
# SIMULATION FUNCTION
# -----------------------------
def simulate(TAM, growth_mean, growth_std, market_share_mean,
             margin_low, margin_high, multiple, prob_success, simulations):

    vals = []

    for _ in range(simulations):
        growth = np.random.normal(growth_mean/100, growth_std/100)
        market_share = np.random.beta(2, 5) * (market_share_mean/100)
        margin = np.random.uniform(margin_low/100, margin_high/100)

        revenue = TAM * market_share * (1 + growth)
        profit = revenue * margin
        val = profit * multiple

        val = val * (prob_success/100)
        vals.append(val)

    return np.array(vals)

# -----------------------------
# SIDEBAR GLOBAL INPUTS
# -----------------------------
st.sidebar.header("📊 Global Assumptions")

simulations = st.sidebar.slider("Number of Simulations", 500, 5000, 1000)
multiple = st.sidebar.slider("Valuation Multiple", 5, 30, 15)
prob_success = st.sidebar.slider("Probability of Success (%)", 10, 100, 60)

scenario = st.sidebar.selectbox(
    "Scenario",
    ["Base Case", "Regulatory Shock", "Funding Winter"]
)

if scenario == "Regulatory Shock":
    prob_success *= 0.7

elif scenario == "Funding Winter":
    multiple *= 0.7

# -----------------------------
# STARTUP INPUT FUNCTION
# -----------------------------
def startup_inputs(name):
    st.sidebar.subheader(name)

    TAM = st.sidebar.number_input(f"{name} TAM (₹ Cr)", value=10000)
    growth_mean = st.sidebar.slider(f"{name} Growth (%)", 0, 100, 20)
    growth_std = st.sidebar.slider(f"{name} Growth σ", 0, 50, 10)
    market_share = st.sidebar.slider(f"{name} Market Share (%)", 0, 50, 5)
    margin_low = st.sidebar.slider(f"{name} Min Margin (%)", 0, 50, 10)
    margin_high = st.sidebar.slider(f"{name} Max Margin (%)", 10, 80, 30)

    return TAM, growth_mean, growth_std, market_share, margin_low, margin_high

# Inputs
A_inputs = startup_inputs("Startup A")
B_inputs = startup_inputs("Startup B")
C_inputs = startup_inputs("Startup C")

# Run simulations
vals_A = simulate(*A_inputs, multiple, prob_success, simulations)
vals_B = simulate(*B_inputs, multiple, prob_success, simulations)
vals_C = simulate(*C_inputs, multiple, prob_success, simulations)

# -----------------------------
# METRICS
# -----------------------------
def metrics(vals):
    median = np.median(vals)
    mean = np.mean(vals)
    downside = np.percentile(vals, 5)
    upside = np.percentile(vals, 95)
    cvar = vals[vals <= downside].mean()
    return median, mean, downside, upside, cvar

mA = metrics(vals_A)
mB = metrics(vals_B)
mC = metrics(vals_C)

# -----------------------------
# DISPLAY METRICS
# -----------------------------
st.subheader("📊 Comparative Valuation")

col1, col2, col3 = st.columns(3)

def show(col, name, m):
    col.markdown(f"### {name}")
    col.metric("Median", f"{m[0]:,.0f}")
    col.metric("Mean", f"{m[1]:,.0f}")
    col.metric("Downside (5%)", f"{m[2]:,.0f}")
    col.metric("Upside (95%)", f"{m[3]:,.0f}")
    col.metric("CVaR", f"{m[4]:,.0f}")

show(col1, "Startup A", mA)
show(col2, "Startup B", mB)
show(col3, "Startup C", mC)

# -----------------------------
# RANKINGS
# -----------------------------
labels = ["Startup A", "Startup B", "Startup C"]
means = [mA[1], mB[1], mC[1]]
cvars = [mA[4], mB[4], mC[4]]

best = np.argmax(means)
risk_adj = [means[i] / abs(cvars[i]) for i in range(3)]
best_risk = np.argmax(risk_adj)

st.subheader("🏆 Model Insights")
st.success(f"Highest Expected Value: {labels[best]}")
st.info(f"Best Risk-Adjusted Return: {labels[best_risk]}")

# -----------------------------
# PLOT
# -----------------------------
st.subheader("📈 Valuation Distributions")

fig, ax = plt.subplots()
ax.hist(vals_A, bins=30, alpha=0.5, label="A")
ax.hist(vals_B, bins=30, alpha=0.5, label="B")
ax.hist(vals_C, bins=30, alpha=0.5, label="C")

ax.legend()
ax.set_xlabel("Valuation (₹ Cr)")
ax.set_ylabel("Frequency")

st.pyplot(fig)

# -----------------------------
# USER DECISION
# -----------------------------
st.subheader("💰 Your Decision")

chosen = st.radio("Which startup would you invest in?", ["Startup A", "Startup B", "Startup C"])

if chosen != labels[best]:
    st.warning("⚠️ Your choice differs from model (Possible Bias)")
else:
    st.success("✅ Your choice aligns with model")

# -----------------------------
# PORTFOLIO ALLOCATION
# -----------------------------
st.subheader("📊 Allocate ₹100 Cr")

alloc_A = st.slider("Startup A Allocation", 0, 100, 33)
alloc_B = st.slider("Startup B Allocation", 0, 100, 33)
alloc_C = 100 - alloc_A - alloc_B

st.write(f"Startup C Allocation: {alloc_C}")

# -----------------------------
# EXPORT DATA
# -----------------------------
st.subheader("📥 Export Data (For Research)")

df = pd.DataFrame({
    "Startup": labels,
    "Mean": means,
    "CVaR": cvars,
    "Chosen": [chosen]*3,
    "Allocation": [alloc_A, alloc_B, alloc_C]
})

st.download_button("Download Results CSV", df.to_csv(index=False), "valuation_results.csv")
