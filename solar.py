import streamlit as st
import numpy as np
import plotly.graph_objects as go
import pandas as pd

# Page Configuration
st.set_page_config(
    page_title="Solar Cell Array Simulator",
    page_icon="☀️",
    layout="wide"
)

st.title("☀️ Solar Cell Array Simulator")
st.markdown("""
This application models the electrical performance ($V$, $I$, $P$) of interconnected solar cells (e.g., Perovskite Solar Cells) across different wiring topologies (Series, Parallel, and Series-Parallel Hybrid) and plots interactive **I-V** and **P-V** characteristic curves.
""")

# Sidebar Input Parameters
st.sidebar.header("⚙️ 1. Single Cell Parameters")
voc_cell = st.sidebar.number_input("Open-Circuit Voltage $V_{oc}$ (V)", value=1.15, step=0.05)
jsc_cell = st.sidebar.number_input("Short-Circuit Current Density $J_{sc}$ (mA/cm²)", value=23.0, step=0.5)
vmpp_cell = st.sidebar.number_input("Voltage at MPP $V_{mpp}$ (V)", value=0.95, step=0.05)
jmpp_cell = st.sidebar.number_input("Current Density at MPP $J_{mpp}$ (mA/cm²)", value=20.5, step=0.5)
area_cell = st.sidebar.number_input("Single Cell Area (cm²)", value=1.0, step=0.1)

st.sidebar.header("🔌 2. Array Topology")
connection_type = st.sidebar.radio(
    "Connection Scheme",
    ["Series Only", "Parallel Only", "Series-Parallel Hybrid"]
)

if connection_type == "Series Only":
    n_series = st.sidebar.slider("Number of Cells in Series ($N_s$)", 1, 50, 8)
    n_parallel = 1
elif connection_type == "Parallel Only":
    n_series = 1
    n_parallel = st.sidebar.slider("Number of Cells in Parallel ($N_p$)", 1, 50, 8)
else:
    n_series = st.sidebar.slider("Series Cells per String ($N_s$)", 1, 25, 4)
    n_parallel = st.sidebar.slider("Parallel Strings ($N_p$)", 1, 25, 4)

# Electrical Calculations
isc_single = (jsc_cell * area_cell) / 1000.0  # Convert mA to Amperes (A)
impp_single = (jmpp_cell * area_cell) / 1000.0

n_total = n_series * n_parallel
total_area = n_total * area_cell

# Array Total Output Calculations
voc_total = n_series * voc_cell
isc_total = n_parallel * isc_single
vmpp_total = n_series * vmpp_cell
impp_total = n_parallel * impp_single
pmax_total = vmpp_total * impp_total
ff_total = (pmax_total / (voc_total * isc_total)) * 100 if (voc_total * isc_total) > 0 else 0

# Display Key Metrics
st.subheader("📌 Total Array Output Metrics")
col1, col2, col3, col4 = st.columns(4)

col1.metric("MPP Voltage $V_{mpp}$", f"{vmpp_total:.2f} V", f"Voc = {voc_total:.2f} V")
col2.metric("MPP Current $I_{mpp}$", f"{impp_total:.3f} A", f"Isc = {isc_total:.3f} A")
col3.metric("Max Power $P_{max}$", f"{pmax_total:.2f} W", f"Fill Factor = {ff_total:.1f}%")
col4.metric("Total Active Area", f"{total_area:.1f} cm²", f"Cells: {n_total}")

st.markdown("---")

# Generate I-V and P-V Curves
st.subheader("📈 Performance Characteristic Curves (I-V & P-V)")

v_vec = np.linspace(0, voc_total, 300)
# Empirical diode approximation model for solar cell I(V) characteristics
m_factor = (
    np.log(1 - (impp_total / isc_total)) / np.log(vmpp_total / voc_total)
    if (impp_total < isc_total and vmpp_total < voc_total)
    else 5.0
)
i_vec = np.maximum(0, isc_total * (1 - (v_vec / voc_total) ** m_factor))
p_vec = v_vec * i_vec

# Interactive Plotly Figure
fig = go.Figure()

# Add I-V Curve
fig.add_trace(go.Scatter(
    x=v_vec, y=i_vec,
    mode='lines',
    name='Current (I-V)',
    line=dict(color='#1f77b4', width=3)
))

# Add P-V Curve on Secondary Axis
fig.add_trace(go.Scatter(
    x=v_vec, y=p_vec,
    mode='lines',
    name='Power (P-V)',
    line=dict(color='#ff7f0e', width=3, dash='dash'),
    yaxis='y2'
))

# Highlight Maximum Power Point (MPP) on the I-V curve
fig.add_trace(go.Scatter(
    x=[vmpp_total], y=[impp_total],
    mode='markers',
    name='MPP (I-V)',
    marker=dict(size=12, color='red', symbol='star')
))

# Highlight Maximum Power Point (MPP) on the P-V curve
fig.add_trace(go.Scatter(
    x=[vmpp_total], y=[pmax_total],
    mode='markers',
    name='MPP (P-V)',
    marker=dict(size=12, color='red', symbol='star'),
    yaxis='y2'
))

fig.update_layout(
    title="Solar Cell Array Performance Output",
    xaxis=dict(title="Voltage (V)"),
    yaxis=dict(
        title=dict(text="Current (A)", font=dict(color="#1f77b4")),
        tickfont=dict(color="#1f77b4")
    ),
    yaxis2=dict(
        title=dict(text="Power (W)", font=dict(color="#ff7f0e")),
        tickfont=dict(color="#ff7f0e"),
        overlaying="y",
        side="right"
    ),
    hovermode="x unified",
    legend=dict(x=0.01, y=0.99, bgcolor='rgba(255,255,255,0.6)')
)

st.plotly_chart(fig, width="stretch")

# Summary Comparison Dataframe
st.subheader("📋 Performance Parameter Breakdown")
single_ff = (
    ((vmpp_cell * impp_single) / (voc_cell * isc_single)) * 100
    if (voc_cell * isc_single) > 0 else 0
)

summary_df = pd.DataFrame({
    "Electrical Parameter": [
        "Open-Circuit Voltage (Voc)",
        "Short-Circuit Current (Isc)",
        "Voltage at MPP (Vmpp)",
        "Current at MPP (Impp)",
        "Maximum Power Output (Pmax)",
        "Fill Factor (FF)",
        "Total Active Area"
    ],
    "Single Cell Level": [
        f"{voc_cell:.2f} V",
        f"{isc_single*1000:.1f} mA",
        f"{vmpp_cell:.2f} V",
        f"{impp_single*1000:.1f} mA",
        f"{vmpp_cell*impp_single:.3f} W",
        f"{single_ff:.1f}%",
        f"{area_cell} cm²"
    ],
    "Total Array Level": [
        f"{voc_total:.2f} V",
        f"{isc_total:.3f} A",
        f"{vmpp_total:.2f} V",
        f"{impp_total:.3f} A",
        f"{pmax_total:.2f} W",
        f"{ff_total:.1f}%",
        f"{total_area:.1f} cm²"
    ]
})

st.dataframe(summary_df, width="stretch")
