"""
main.py

Simuleert een energiebeheersysteem met Model Predictive Control (MPC) voor verschillende scenario's met PV-panelen
en een batterijopslagsysteem.

De gebruiker kiest één van de volgende scenario's:
1. Basis – geen PV en geen batterij
2. Alleen PV – met opgewekte zonne-energie maar zonder batterij
3. Alleen Accu – alleen batterij-opslag, geen zonne-energie
4. PV en Accu – combinatie van zonnepanelen en batterijopslag

Functionaliteit:
- Laadt verbruiksprofiel, energieprijzen, temperatuur- en zoninstralingsgegevens
- Initialiseert batterij en PV-systeem op basis van scenario
- Voert een sliding window MPC-optimalisatie uit over een tijdshorizon
- Simuleert energiestromen tussen grid, batterij, load en PV
- Houdt verbruik, opslag en PV-gebruik bij
- Visualiseert resultaten en toont verbruikssamenvatting

Gebruik:
    Start het script en volg de prompt om een scenario te kiezen.
"""
import numpy as np
import pandas as pd
from models.battery import Battery
from models.pv import PVSystem
from models.mpc_data import MPCInputData
from mpc.controller import run_full_mpc
from data.data_loader import load_prices, load_temperature, SimulationOptions
from data.date_generator import DataGenerator
# from visualization.visualization import plot_results
from models.energy_price import EnergyPriceCalculator
from tqdm import tqdm  # Voortgangsbalk voor de simulatie

steps = 8760
Np = 24
Np_bat = 12
Np_PV = 6

PV_panelen1 = 3
PV_panelen2 = 6


batterij1 = 2.4
batterij2 = 3.5
batterij3 = 4.8

# Nieuwe scenario-lijst: (aantal_panelen, accucapaciteit, T, Np)
scenario_lijst = [
    (SimulationOptions(name="SIM_1: ",
                       description="Controle zonder PV en Batterij",
                       n_pvpanels=0,
                       battery_capacity=0,
                       steps=steps,
                       prediction_window=Np)),
    (SimulationOptions(name="SIM_2: ",
                       description=f"Controle alleen {PV_panelen1} PV-panelen",
                       n_pvpanels=3,
                       battery_capacity=0,
                       steps=steps,
                       prediction_window=Np)),
    (SimulationOptions(name="SIM_3: ",
                       description=f"Alleen {batterij1} kWh Batterij",
                       n_pvpanels=0,
                       battery_capacity=batterij1,
                       steps=steps,
                       prediction_window=Np_bat)),
    (SimulationOptions(name="SIM_4: ",
                       description=f"Alleen {batterij2} kWh Batterij",
                       n_pvpanels=0,
                       battery_capacity=batterij2,
                       steps=steps,
                       prediction_window=Np_bat)),
    (SimulationOptions(name="SIM_5: ",
                       description=f"Alleen {batterij3} kWh Batterij",
                       n_pvpanels=0,
                       battery_capacity=batterij3,
                       steps=steps,
                       prediction_window=Np_bat)),
    (SimulationOptions(name="SIM_6: ",
                       description=f"{PV_panelen1} PV-Panelen + {batterij1} kWH Batterij",
                       n_pvpanels=PV_panelen1,
                       battery_capacity=batterij1,
                       steps=steps,
                       prediction_window=Np_PV)),
    (SimulationOptions(name="SIM_7: ",
                       description=f"{PV_panelen1} PV-Panelen + {batterij2} kWH Batterij",
                       n_pvpanels=PV_panelen1,
                       battery_capacity=batterij2,
                       steps=steps,
                       prediction_window=Np_PV)),
    (SimulationOptions(name="SIM_8: ",
                       description=f"{PV_panelen1} PV-Panelen + {batterij3} kWH Batterij",
                       n_pvpanels=PV_panelen1,
                       battery_capacity=batterij3,
                       steps=steps,
                       prediction_window=Np_PV)),
    (SimulationOptions(name="SIM_9: ",
                       description=f"{PV_panelen2} PV-Panelen + {batterij1} kWH Batterij",
                       n_pvpanels=PV_panelen2,
                       battery_capacity=batterij1,
                       steps=steps,
                       prediction_window=Np_PV)),
    (SimulationOptions(name="SIM_10: ",
                       description=f"{PV_panelen2} PV-Panelen + {batterij2} kWH Batterij",
                       n_pvpanels=PV_panelen2,
                       battery_capacity=batterij2,
                       steps=steps,
                       prediction_window=Np_PV)),
    (SimulationOptions(name="SIM_11: ",
                       description=f"{PV_panelen2} PV-Panelen + {batterij3} kWH Batterij",
                       n_pvpanels=PV_panelen2,
                       battery_capacity=batterij3,
                       steps=steps,
                       prediction_window=Np_PV)),
]


def run_simulation(options):
    """
    Voert een dynamische simulatie uit van een energiebeheersysteem (EMS) met
    zonne-energie en een batterijopslag, gebruikmakend van een Model Predictive
    Control (MPC) algoritme binnen een sliding-window aanpak.

    Parameters:
    -----------
    options : Namespace
        Een object met alle benodigde simulatie-instellingen, zoals:
        - name (str): naam van het scenario.
        - description (str): beschrijving van het scenario.
        - steps (int): aantal simulatiestappen.
        - prediction_window (int): horizonlengte voor MPC.
        - battery_capacity (float): capaciteit van de batterij in kWh.
        - n_pvpanels (int): aantal PV-panelen in het systeem.

    Returns:
    --------
    df : pandas.DataFrame
        Een DataFrame met tijdreeksen van alle relevante variabelen in het EMS, waaronder:
        - load [kW]
        - price [€/kWh]
        - grid_power [kW]
        - soc_kwh [kWh]
        - soc_max [kWh]
        - pv_used [kW]
        - pv_avail [kW]
        - pv_to_bat [kW]
        - pv_to_load [kW]
        - battery_to_load [kW]
        - p_charge [kW]
        - p_discharge [kW]
        - grid_to_bat [kW]
        - grid_to_load [kW]

        De index van het DataFrame is een tijdstempelreeks met een uurlijkse frequentie,
        beginnend op 2022-01-01 00:00.

    Opmerkingen:
    ------------
    - De simulatie verwerkt synthetische verbruiks- en irradiantiedata.
    - Energieprijzen worden aangepast op basis van belasting en tijdstip.
    - Het systeemmodel houdt rekening met batterijdegradatie en laadsnelheden.
    - Als de oplossing van het MPC-probleem op enig moment niet optimaal is,
      wordt de simulatie vroegtijdig beëindigd.
    """

    Np = options.prediction_window

    print(f"Simuleer scenario: {options.name}- {options.description}")
    """Voert de volledige sliding-window MPC-simulatie uit."""
    n_steps = options.steps - options.prediction_window

    # Configuratie en data
    load = DataGenerator(T=options.steps).generate_load()
    price_orig = load_prices("./data/prices.csv", expected_length=options.steps).values
    price_orig[price_orig < 0] = 0.01
    temperature = load_temperature("./data/temperature.csv", expected_length=options.steps).values
    irradiance = DataGenerator(T=options.steps).generate_irradiance()

    # Initialisatie batterij en PV
    battery = Battery(soc=0.5,
                      soc_min=0.2,
                      soc_max_init=0.95,
                      capacity_kWh_nominal=options.battery_capacity,
                      max_cycles=6000,
                      voltage=48,
                      max_ampere_charge=105,
                      max_ampere_discharge=105,
                      ramp_ampere_charge=80,
                      ramp_ampere_discharge=80
                      ) if options.battery_capacity > 0 else None

    pv = PVSystem(irradiance=irradiance,
                  temperature=temperature,
                  panel_wp=435,
                  n_pvpanels=options.n_pvpanels,
                  )

    price_calculator = EnergyPriceCalculator(taxes_tarif=0.21,
                                             market_prices=price_orig,
                                             loads=load
                                             )

    # Resultatenopslag
    grid_history = []
    soc_history = []
    degradation_history = []
    pv_used_history = []
    pv_available_history = []
    pv_to_battery_history = []
    pv_to_load_history = []
    battery_to_load_history = []
    adjusted_prices_total = np.zeros(options.steps - options.prediction_window)
    # … na alle andere history‐lijsten …
    p_charge_history = []
    p_discharge_history = []
    used_energy_total = 0.0

    # Sliding-window loop
    for t in tqdm(range(n_steps), desc="Simulatie voortgang"):
        P_load = load[t:t + Np]
        P_pv_avail = pv.power_output()[t:t + Np]
        P_price = price_orig[t:t + Np]

        P_price_adjusted = price_calculator.adjust_price(
            market_prices=P_price,
            loads=load[t:t+Np],
            cumulative_init=np.sum(load[:t])
        )
        adjusted_prices_total[t] = P_price_adjusted[0]

        input_data = MPCInputData(
            P_load=P_load,
            P_pv_available=P_pv_avail,
            price=P_price_adjusted,
            soc_init=battery.soc if battery else 0.0
        )
        result = run_full_mpc(input_data, battery)

        if result.status != 'optimal':
            print(f"[t={t}] ⚠️ Niet-optimaal!")
            break

        if battery:
            step_used = float(result.U[2][0]) + float(result.U[4][0])
            used_energy_total += step_used
            battery.update_degradation(float(result.U[2][0]) + float(result.U[4][0]))
            battery.soc = float(result.SOC[1])
            soc_history.append(battery.soc)
            degradation_history.append(battery.soc_max)

        grid_history.append(result.U[0][0])
        pv_used_history.append(result.U[3][0])
        pv_available_history.append(P_pv_avail[0])

        # Energie van PV naar batterij (per stap)
        pv_to_battery_history.append(float(result.U[4][0]))
        pv_to_load_history.append(float(result.U[5][0]))

        # Energie van batterij naar load (per stap)
        battery_to_load_history.append(float(result.U[2][0]))

        # sla ook P_charge (U[1]) en P_discharge (U[2]) op
        p_charge_history.append(float(result.U[1][0]))
        p_discharge_history.append(float(result.U[2][0]))

    # Converteer naar arrays voor terugkeer
    p_charge      = np.array(p_charge_history)
    p_discharge   = np.array(p_discharge_history)
    grid_power = np.array(grid_history)
    pv_used = np.array(pv_used_history)
    pv_avail = np.array(pv_available_history)
    pv_to_bat = np.array(pv_to_battery_history)
    pv_to_load = np.array(pv_to_load_history)
    battery_to_load = np.array(battery_to_load_history)

    # Zorg dat soc_kwh en soc_max_vals altijd de juiste lengte krijgen:
    if battery:
        soc_kwh      = np.array(soc_history) * battery.capacity_kWh_nominal
        soc_max_vals = np.array(degradation_history)
    else:
        # vul met NaN zodat je wel kolommen krijgt
        soc_kwh      = np.full(n_steps, np.nan)
        soc_max_vals = np.full(n_steps, np.nan)

    # slice de ingeladen data ook op n_steps:
    load_slice = load[:n_steps]
    price_slice = adjusted_prices_total[:n_steps]

    # bouw de DataFrame met *alle* kolommen van gelijke lengte
    df = pd.DataFrame({
        'load [kW]': load_slice,
        'price [€/kWh]': price_slice,
        'grid_power [kW]': grid_power,
        'soc_kwh [kWh]': soc_kwh,
        'soc_max [kWh]': soc_max_vals,
        'pv_used [kW]': pv_used,
        'pv_avail [kW]': pv_avail,
        'pv_to_bat [kW]': pv_to_bat,
        'pv_to_load [kW]': pv_to_load,
        'battery_to_load [kW]': battery_to_load,
        'p_charge [kW]': p_charge,
        'p_discharge [kW]': p_discharge,
    })

    # bereken extra flows
    df['grid_to_bat [kW]'] = (df['p_charge [kW]'] - df['pv_to_bat [kW]']).clip(lower=0)
    df['grid_to_load [kW]'] = df['grid_power [kW]'] - df['grid_to_bat [kW]']

    # (Optioneel) voeg een tijdstap-kolom toe als index
    start = pd.Timestamp('2022-01-01 00:00')  # kies jouw startmoment
    idx = pd.date_range(start, periods=n_steps, freq='h')
    df.index = idx
    df.index.name = 'timestamp'

    return df


def show_summary(df):
    """Drukt een overzicht van de simulatieresultaten gebaseerd op de DataFrame."""

    print("\n✅ Simulatie voltooid")
    print(f"📦 Totale energieverbruik (P_load): {df['load [kW]'].sum():.1f} kWh")
    print(f"🔌 Energie geleverd door net: {df['grid_power [kW]'].sum():.1f} kWh")
    print(f"🔌→📦 Net → Load    : {df['grid_to_load [kW]'].sum():.1f} kWh")
    print(f"📥 Energie ingekocht van net: € {(df['grid_power [kW]'] * df['price [€/kWh]']).sum():.1f}")

    # Let op: hier de volledige kolomnaam met [kW]
    if 'battery_to_load [kW]' in df.columns:
        print(f"🔋 Energie geleverd door batterij: {df['battery_to_load [kW]'].sum():.1f} kWh")
        print(f"🔌→🔋 Net → Batterie: {df['grid_to_bat [kW]'].sum():.1f} kWh")

    else:
        print("🪫 Geen batterij in simulatie")


    if 'pv_avail [kW]' in df.columns:
        print(f"☀️ PV beschikbaar: {df['pv_avail [kW]'].sum():.1f} kWh")
        print(f"☀️ PV geleverd: {df['pv_used [kW]'].sum():.1f} kWh")
        print(f"☀️→📦️ PV → Load: {df['pv_to_load [kW]'].sum():.1f} kWh")
        print(f"☀️→🔋 PV → Batterij: {df['pv_to_bat [kW]'].sum():.1f} kWh")
    else:
        print("☁︎ Geen PV in simulatie")


# === Hoofdfunctie ===
if __name__ == "__main__":

    summaries = []
    for options in scenario_lijst:
        df = run_simulation(options)  # Zorg dat deze een DataFrame retourneert

        # Bouw een bestandsnaam op basis van de scenario-naam
        safe_name = options.name.strip().replace(":", "").replace(" ", "_")
        safe_description = options.description.strip().replace(":", "").replace(" ", "_")
        bestandsnaam = f"resultaat_{safe_name}_{safe_description}.csv"

        df.to_csv(str("./export/" + bestandsnaam), index=True)
        print(f"Resultaten geëxporteerd als {bestandsnaam}")
        samenvatting = {
            "SIM": options.name.strip(),
            "beschrijving": options.description,
            "PV [n]": options.n_pvpanels,
            "Accu [kWh]": options.battery_capacity,
            "T": options.steps,
            "Np": options.prediction_window,
            "Load [kWh]": df["load [kW]"].sum(),
            "Grid [kWh]": df["grid_power [kW]"].sum(),
            "Grid → Load [kWh]": df["grid_to_load [kW]"].sum(),
            "Kosten Net [€]": (df["grid_power [kW]"] * df["price [€/kWh]"]).sum(),
            "Batterij → Load [kWh]": df["battery_to_load [kW]"].sum() if "battery_to_load [kW]" in df else 0,
            "Net → Batterij [kWh]": df["grid_to_bat [kW]"].sum() if "grid_to_bat [kW]" in df else 0,
            "PV Beschikbaar [kWh]": df["pv_avail [kW]"].sum() if "pv_avail [kW]" in df else 0,
            "PV Gebruikt [kWh]": df["pv_used [kW]"].sum() if "pv_used [kW]" in df else 0,
            "PV → Load [kWh]": df["pv_to_load [kW]"].sum() if "pv_to_load [kW]" in df else 0,
            "PV → Batterij [kWh]": df["pv_to_bat [kW]"].sum() if "pv_to_bat [kW]" in df else 0,
        }

        # Maak samenvatting

        summaries.append(samenvatting)

    # Na alle simulaties: bundel in een DataFrame
    summary_df = pd.DataFrame(summaries)
    summary_df.to_csv("./export/"+"samenvatting_scenario's.csv", index=False)
    print("\n📊 Samenvatting geëxporteerd naar 'samenvatting_scenario's.csv'")
    # aantal_panelen, accucapaciteit = select_scenario()
    # df = run_simulation(aantal_panelen, accucapaciteit)
    # show_summary(df)
    # plot_results(df)

