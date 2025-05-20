import numpy as np
import plotly.graph_objects as go

# Parameters
hours_per_day = 24
peak_hour = 13

irradiance_clear = np.zeros(hours_per_day)
irradiance_cloudy = np.zeros(hours_per_day)

# Berekening voor één dag
for h in range(hours_per_day):
    hour_angle = np.pi * (h - peak_hour + 6) / 12
    base_irradiance = max(0, np.sin(hour_angle))

    # Zonder bewolking (theoretisch)
    irradiance_clear[h] = base_irradiance

    # Met bewolking (realistisch)
    cloud_factor = np.random.uniform(0.6, 1.0)
    irradiance_cloudy[h] = base_irradiance * cloud_factor

# Plotly overlappend staafdiagram
fig = go.Figure()

# Theoretisch: doorzichtig oranje
fig.add_trace(go.Bar(
    x=list(range(24)),
    y=irradiance_clear,
    name="Zonder bewolking",
    marker=dict(color='rgba(255, 127, 14, 0.3)')  # doorzichtig oranje
))

# Realistisch: ondoorzichtig oranje
fig.add_trace(go.Bar(
    x=list(range(24)),
    y=irradiance_cloudy,
    name="Met bewolking",
    marker=dict(color='rgba(255, 127, 14, 1.0)')  # volle oranje kleur
))

fig.update_layout(
    title="Zonne-instraling per uur (1 dag, met en zonder bewolking)",
    xaxis_title="Uur van de dag",
    yaxis_title="Instraling (kW/m²)",
    yaxis=dict(title="Instraling (kW/m²)",
               range=[0, 1.4],
               dtick=0.2),
    xaxis=dict(tickmode='linear'),
    barmode='overlay',  # balken overlappen
    template='plotly_white',
    width=800,
    height=400,
    legend=dict(
        x=1,
        y=1,
        xanchor="right",
        yanchor="top"
    )
)

fig.show(renderer="browser")