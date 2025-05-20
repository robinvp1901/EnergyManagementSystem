import pandas as pd
from dataclasses import dataclass


@dataclass
class SimulationOptions:

    name: str = "SIM_1"
    description: str = "Simulation options"
    n_pvpanels: int = 1
    battery_capacity: float = 3
    steps: int = 100
    prediction_window: int = 100



def load_prices(csv_path: str, expected_length: int = 8760) -> pd.Series:
    """
    Laadt prijzen uit een CSV-bestand, converteert van €/MWh naar €/kWh
    en controleert op verwachte lengte.

    Parameters:
        csv_path (str): Pad naar het CSV-bestand
        expected_length (int): Verwacht aantal uurlijkse datapunten (standaard 8760)

    Returns:
        pd.Series: Prijsdata in €/kWh met datetime-index
    """
    df = pd.read_csv(csv_path, parse_dates=[0], index_col=0)
    prices_mwh = df.iloc[:, 0]
    prices_kwh = prices_mwh / 1000

    if len(prices_kwh) < expected_length:
        raise ValueError(f"CSV bevat slechts {len(prices_kwh)} waarden, verwacht {expected_length}.")
    elif len(prices_kwh) > expected_length:
        prices_kwh = prices_kwh.iloc[:expected_length]

    return prices_kwh



def load_temperature(csv_path: str, expected_length: int = 8760) -> pd.Series:
    """
    Laadt temperatuurdata uit een CSV-bestand en controleert op verwachte lengte.

    Parameters:
        csv_path (str): Pad naar het CSV-bestand
        expected_length (int): Verwacht aantal uurlijkse datapunten (standaard 8760)

    Returns:
        pd.Series: Temperatuurdata in graden Celsius met datetime-index
    """
    df = pd.read_csv(csv_path, parse_dates=[0], index_col=0)
    temperature = df["temperature"]

    if len(temperature) < expected_length:
        raise ValueError(f"CSV bevat slechts {len(temperature)} waarden, verwacht {expected_length}.")
    elif len(temperature) > expected_length:
        temperature = temperature.iloc[:expected_length]

    return temperature

def load_energy_tariff(csv_path: str, year: int = None):
    df = pd.read_csv(csv_path)

    # Selecteer rij op jaartal (laatste jaar als default)
    if year is None:
        year = df['Jaar'].max()
    row = df[df['Jaar'] == year].iloc[0]

    brackets = []

    for column in df.columns[1:]:
        try:
            # Limiet ophalen
            if '-' in column:
                upper_limit = column.split('-')[-1]
            elif '>' in column:
                upper_limit = 'inf'
            else:
                continue

            # Limiet converteren
            if upper_limit == 'inf':
                limit = float('inf')
            else:
                limit = float(
                    upper_limit.replace('.', '').replace(',', '.').replace('mln', '000000').replace('kWh', ''))

            # Tarief toevoegen
            tariff = float(str(row[column]).replace(',', '.'))
            brackets.append((limit, tariff))

        except Exception as e:
            print(f"⚠️ Kon kolom '{column}' niet verwerken: {e}")
            continue

    return brackets

