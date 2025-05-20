import numpy as np
import plotly.graph_objects as go

# Origineel dagprofiel (24 waarden)
day_profile = np.array([
    0.2, 0.2, 0.2, 0.2,
    0.3, 0.5, 1.5, 3.0,
    1.2, 0.6, 0.4, 0.3,
    0.3, 0.4, 0.5, 0.7,
    1.0, 2.5, 5.0, 3.5,
    2.0, 1.0, 0.6, 0.3
])

# Simulatielengte in uren (bijvoorbeeld 1 jaar = 365 dagen × 24 uur)
T = 365 * 24

# Doelgemiddelde: 2420 kWh per jaar = 0.388 kWh per uur
target_hourly_avg = 2420 / 365 / 24

# Schaal het dagprofiel
avg_day_profile = day_profile.mean()
scale_factor = target_hourly_avg / avg_day_profile
scaled_day = day_profile * scale_factor

# Herhaal het dagprofiel over de hele periode
load = np.tile(scaled_day, T // 24 + 2)[:T]

# Voeg ruis toe
np.random.seed(42)  # Voor reproduceerbaarheid
load += np.random.normal(0, 0.02, T)
load = np.clip(load, 0.1, 5.0)

# Controleer het totaalverbruik
total_consumption = load.sum()  # in kWh
print(f"Totaal verbruik over {T} uur: {total_consumption:.2f} kWh")

# Plot een voorbeeld van 1 dag
hours = list(range(24))
example_day = load[:24]

fig = go.Figure(data=[
    go.Bar(x=hours, y=example_day)
])

fig.update_layout(
    title="Dagprofiel verbruik huishouden (2420 kWh/jaar)",
    xaxis=dict(
        title='Uur van de dag',
        tickmode='linear',
        tick0=0,
        dtick=1,
        linecolor='black',
        mirror=True
    ),
    yaxis=dict(
        title='Verbruik (kWh)',
        linecolor='black',
        mirror=True,
        dtick=0.2
    ),
    plot_bgcolor='white',
    paper_bgcolor='white',
    width=800,  # A4-breedte
    height=400  # optionele hoogte
)

fig.show(renderer="browser")