import pandas as pd
from datetime import datetime


class EnergyPriceCalculator:
    """
    Bereken de total cost inclusief energieprijzen, belastingen en accijnzen.
    Accijnzen worden ingelezen uit een CSV met historische tarieven.
    """
    def __init__(
        self,
        taxes_tarif: float,
        market_prices,
        loads,
        excise_csv: str = './data/energy_taxes_NL.csv'
    ):
        # Netbeheerkosten (BTW e.d.)
        self.taxes_tarif = taxes_tarif
        # Marktprijzen en loads (array-achtige) voor prijsaanpassing
        self.market_prices = market_prices
        self.loads = loads

        # Lees accijnzen in vanuit CSV
        df = pd.read_csv(excise_csv)
        # Bepaal huidig jaar; als niet beschikbaar, pak laatste rij
        current_year = datetime.now().year
        if current_year in df['Jaar'].values:
            row = df[df['Jaar'] == current_year].iloc[0]
        else:
            row = df.iloc[-1]

        # Zet drempels en bijbehorende tarieven (particulier) op
        self.excise_thresholds = [2900, 10000, 50000, 10_000_000, float('inf')]
        self.excise_rates = [
            row['0-2900'],
            row['2901-10000'],
            row['10001-50000'],
            row['50001-10mln'],
            row['>10mln_particulier']
        ]

    def adjust_price(self, market_prices, loads, cumulative_init: float):
        """
        Past marktprijs aan met accijnzen en belastingen per tijdstap.
        """
        adj = []
        for t, base_price in enumerate(market_prices):
            load_t = loads[0] + cumulative_init if hasattr(loads, '__getitem__') else loads
            excise = self.determine_energy_excise(load_t)
            total_price = (base_price + excise) * (1 + self.taxes_tarif)
            adj.append(total_price)
        return pd.Series(adj, index=None)

    def determine_energy_excise(self, load: float) -> float:
        """
        Bepaalt het accijnstarief (€/kWh) op basis van (cumulatief) verbruik.
        """
        for threshold, rate in zip(self.excise_thresholds, self.excise_rates):
            if load <= threshold:
                return rate
        # Fallback
        return self.excise_rates[-1]
