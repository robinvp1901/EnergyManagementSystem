from plotly.subplots import make_subplots
import plotly.graph_objects as go
from plotly.express import colors

palette = colors.qualitative.Plotly


def plot_results(df):
    fig = make_subplots(
        rows=5, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.15,
        subplot_titles=(
            "Vermogens: Load, PV en Grid [kW]",
            "PV gebruik vs beschikbaar [kW]",
            "Elektriciteitsprijs [€/kWh]",
            "Batterij SOC [kWh]",
            "SOC Max. grens [%] (capaciteitsverlies)"
        )
    )

    # Rij 1: Load, PV beschikbaar, Grid
    fig.add_trace(
        go.Scatter(
            x=df.index, y=df['load [kW]'], name='Load [kW]',
            legendgroup='1', line=dict(color=palette[0])
        ), row=1, col=1
    )
    if 'pv_avail [kW]' in df:
        fig.add_trace(
            go.Scatter(
                x=df.index, y=df['pv_avail [kW]'], name='PV beschikbaar [kW]',
                legendgroup='1', line=dict(color=palette[1])
            ), row=1, col=1
        )
    if 'grid_power [kW]' in df:
        fig.add_trace(
            go.Scatter(
                x=df.index, y=df['grid_power [kW]'], name='Grid Power [kW]',
                legendgroup='1', line=dict(color=palette[2])
            ), row=1, col=1
        )

    # Rij 2: PV gebruikt vs beschikbaar
    if 'pv_used [kW]' in df and 'pv_avail [kW]' in df:
        fig.add_trace(
            go.Scatter(
                x=df.index, y=df['pv_used [kW]'], name='PV gebruikt [kW]',
                legendgroup='2', line=dict(color=palette[3])
            ), row=2, col=1
        )
        # grijze beschikbaarheidslijn
        fig.add_trace(
            go.Scatter(
                x=df.index, y=df['pv_avail [kW]'], name='PV beschikbaar [kW]',
                legendgroup='2', line=dict(color='#888888')
            ), row=2, col=1
        )

    # Rij 3: Prijs
    if 'price [€/kWh]' in df:
        fig.add_trace(
            go.Scatter(
                x=df.index, y=df['price [€/kWh]'], name='Prijs [€/kWh]',
                legendgroup='3', line=dict(color=palette[9])
            ), row=3, col=1
        )

    # Rij 4: SOC
    if 'soc_kwh [kWh]' in df:
        fig.add_trace(
            go.Scatter(
                x=df.index, y=df['soc_kwh [kWh]'], name='SOC [kWh]',
                legendgroup='4', line=dict(color='green')
            ), row=4, col=1
        )

    # Rij 5: SOC Max
    if 'soc_max [kWh]' in df:
        fig.add_trace(
            go.Scatter(
                x=df.index, y=df['soc_max [kWh]'] * 100, name='Max SOC [%]',
                legendgroup='5', line=dict(color=palette[6])
            ), row=5, col=1
        )

    # Layout & assen
    fig.update_layout(
        height=1200,
        title="MPC Resultaat: Vermogen, PV, Prijs & SOC",
        template="plotly_white",
        legend=dict(x=1.02, y=1, xanchor='left', yanchor='top'),
        showlegend=True,
        xaxis=dict(title='Tijdstap [uur]', showticklabels=True),
        xaxis2=dict(title='Tijdstap [uur]', showticklabels=True),
        xaxis3=dict(title='Tijdstap [uur]', showticklabels=True),
        xaxis4=dict(title='Tijdstap [uur]', showticklabels=True),
        xaxis5=dict(title='Tijdstap [uur]', showticklabels=True),
    )
    fig.update_yaxes(title_text="Vermogen [kW]", row=1, col=1)
    fig.update_yaxes(title_text="PV [kW]",       row=2, col=1)
    fig.update_yaxes(title_text="Prijs [€/kWh]", row=3, col=1)
    fig.update_yaxes(title_text="SOC [kWh]",     row=4, col=1)
    fig.update_yaxes(
        title_text="Max SOC [%]",
        row=5, col=1,
        range=[80, 100]  # vaste schaal van 80% tot 100%
    )

    # 4) Statistieken berekenen
    total_load        = df['load [kW]'].sum()
    total_grid        = df['grid_power [kW]'].sum() if 'grid_power [kW]' in df else 0.0
    total_cost        = (df['grid_power [kW]'] * df['price [€/kWh]']).sum() if 'price [€/kWh]' in df else 0.0
    net_to_bat        = df['grid_to_bat [kW]'].sum()        if 'grid_to_bat [kW]' in df else 0.0
    bat_to_load       = df['battery_to_load [kW]'].sum()   if 'battery_to_load [kW]' in df else 0.0
    pv_avail          = df['pv_avail [kW]'].sum() if 'pv_avail [kW]' in df else 0.0
    pv_used           = df['pv_used [kW]'].sum()  if 'pv_used [kW]' in df else 0.0
    pv_to_load        = df['pv_to_load [kW]'].sum()       if 'pv_to_load [kW]' in df else 0.0
    pv_to_bat         = df['pv_to_bat [kW]'].sum()        if 'pv_to_bat [kW]' in df else 0.0

    summary_text = (
        f"📦 Verbruik: {total_load:.1f} kWh<br>"
        f"🔌 Net: {total_grid:.1f} kWh (€{total_cost:.1f})<br>"
        f"🔌→🔋 Net→Bat: {net_to_bat:.1f} kWh<br>"
        f"🔋→📦 Bat→Load: {bat_to_load:.1f} kWh<br>"
        f"☀️ PV beschikbaar: {pv_avail:.1f} kWh<br>"
        f"☀️ PV geleverd: {pv_used:.1f} kWh<br>"
        f"☀️→📦 PV→Load: {pv_to_load:.1f} kWh<br>"
        f"☀️→🔋 PV→Bat: {pv_to_bat:.1f} kWh"
    )

    # 5) Toon de summary als annotation
    fig.add_annotation(
        text=summary_text,
        xref='paper', yref='paper',
        x=1.17, y=0.75,
        showarrow=False,
        align='left',
        bordercolor='black',
        borderwidth=1,
        bgcolor='white',
        font=dict(size=12)
    )

    fig.show(config={'modeBarButtonsToAdd': ['drawline',
                                             'drawopenpath',
                                             'drawclosedpath',
                                             'drawcircle',
                                             'drawrect',
                                             'eraseshape'
                                             ]})
