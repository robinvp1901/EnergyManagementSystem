"""
Hoofdscript voor het draaien van een volledige MPC-optimalisatie
zonder sliding window. Simuleert belasting, PV en prijsdata,
roept het MPC-model aan, en toont de resultaten met Plotly.

Werking:
- Genereert synthetische tijdreeksen (load, irradiance, price)
- Maakt PVSystem en Battery objecten aan
- Roept run_full_mpc() aan
- Toont SOC, vermogens en prijs in interactieve plot

Auteur: Robin v. Putten
"""

import numpy as np
from models.battery import Battery
from models.pv import PVSystem
from models.mpc_data import MPCInputData
from mpc.controller import run_full_mpc
from plotly.subplots import make_subplots
import plotly.graph_objects as go

# Simulatieparameters
N = 500
np.random.seed(42)

P_load = np.random.uniform(4, 6, N)
irradiance = np.random.uniform(0.2, 0.8, N)
temperature = np.random.uniform(10, 30, N)
price = np.random.uniform(0.15, 0.3, N)

# Componenten aanmaken
pv = PVSystem(irradiance=irradiance, temperature=temperature)
battery = Battery(soc=0.5)

# MPC input voorbereiden
data = MPCInputData(
    P_load=P_load,
    P_pv=pv.power_output(),
    price=price,
    soc_init=battery.soc
)

# MPC draaien
result = run_full_mpc(data, battery)
print("✅ Status:", result.status)
print("💰 Totale kosten: €", round(np.sum(price * result.U[0]), 2))

# Interactieve plot maken
soc_kwh = result.SOC[:-1] * battery.capacity_kWh

fig = make_subplots(
    rows=3, cols=1,
    shared_xaxes=True,
    vertical_spacing=0.07,
    subplot_titles=("Vermogens: Load, PV en Grid", "Batterij SOC [kWh]", "Elektriciteitsprijs [€/kWh]")
)

fig.add_trace(go.Scatter(y=data.P_load, name='Load [kW]'), row=1, col=1)
fig.add_trace(go.Scatter(y=data.P_pv, name='PV [kW]'), row=1, col=1)
fig.add_trace(go.Scatter(y=result.U[0], name='Grid Power [kW]'), row=1, col=1)

fig.add_trace(go.Scatter(y=soc_kwh, name='SOC [kWh]', line=dict(color='green')), row=2, col=1)
fig.add_trace(go.Scatter(y=data.price, name='Prijs [€/kWh]', line=dict(color='orange')), row=3, col=1)

fig.update_layout(
    height=800,
    title="MPC Resultaat – Vermogen, SOC en Prijs",
    xaxis=dict(title='Tijdstap (uur)'),
    template="plotly_white",
    legend=dict(x=0, y=1.15, orientation='h')
)

fig.update_yaxes(title_text="Vermogen [kW]", row=1, col=1)
fig.update_yaxes(title_text="SOC [kWh]", row=2, col=1)
fig.update_yaxes(title_text="Prijs [€/kWh]", row=3, col=1)

fig.show()