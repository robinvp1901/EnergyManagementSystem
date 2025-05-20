from dataclasses import dataclass
import numpy as np


@dataclass
class PVSystem:
    """
    Dataclass voor het simuleren van PV-opwekking op basis van zoninstraling en temperatuur.

    Attributen:
        irradiance (np.ndarray): Zoninstraling [kWh/m²] per tijdstap.
        temperature (np.ndarray): Temperatuur [°C] per tijdstap.
        panel_area (float): Oppervlakte van één zonnepaneel in m² (standaard 1.65).
        panel_wp (float): Wattpiek van één zonnepaneel in Wp (standaard 450).
        n_pvpanels (int): Aantal zonnepanelen (standaard 6).
        max_irradiance (float): Maximale zoninstraling in W/m² (standaard 1000).
    """
    irradiance: np.ndarray
    temperature: np.ndarray
    panel_area: float = 1.65  # Oppervlakte van één paneel in m²
    panel_wp: float = 400.0   # Wattpiek per paneel
    n_pvpanels: int = 4       # Aantal panelen
    max_irradiance: float = 1000.0  # Maximale zoninstraling in W/m²

    def power_output(self) -> np.ndarray:
        """
        Berekent het PV-vermogen met temperatuurcorrectie.

        Returns:
            np.ndarray: Vermogen in kW per tijdstap.
        """
        return self.n_pvpanels * self.panel_area * (self.panel_wp / 1000) * self.irradiance * (1 - 0.005 * (self.temperature - 25))
        # resultaat in kW
