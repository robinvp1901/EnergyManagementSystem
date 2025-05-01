from dataclasses import dataclass
import numpy as np

@dataclass
class PVSystem:
    """
    Dataclass voor het simuleren van PV-opwekking op basis van zoninstraling en temperatuur.

    Attributen:
        irradiance (np.ndarray): Zoninstraling [kWh/m²] per tijdstap.
        temperature (np.ndarray): Temperatuur [°C] per tijdstap.
        area (float): Oppervlak van PV-panelen in m².
        efficiency (float): Paneelrendement (typisch ~0.18).

    Methoden:
        power_output(): Retourneert array met PV-vermogen per tijdstap [kW].
    """
    irradiance: np.ndarray
    temperature: np.ndarray
    area: float = 10.0
    efficiency: float = 0.18

    def power_output(self) -> np.ndarray:
        """
        Berekent het PV-vermogen met temperatuurcorrectie.

        Returns:
            np.ndarray: Vermogen in kW per tijdstap.
        """
        temp_corr = 1 - 0.005 * (self.temperature - 25)
        return self.efficiency * self.irradiance * self.area * temp_corr