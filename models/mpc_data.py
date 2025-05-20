from dataclasses import dataclass
import numpy as np


@dataclass
class MPCInputData:
    """
    Invoerdata voor het MPC-algoritme over een volledige horizon.

    Attributen:
        P_load (np.ndarray): Belastingsprofiel [kW].
        P_pv (np.ndarray): PV-opwekking [kW].
        price (np.ndarray): Elektriciteitsprijzen [€/kWh].
        soc_init (float): Startwaarde van de batterij-SOC.
    """
    P_load: np.ndarray
    P_pv_available: np.ndarray
    price: np.ndarray
    soc_init: float

@dataclass
class MPCResult:
    """
    Resultaten van een MPC-optimalisatie.

    Attributen:
        U (np.ndarray): Beslissingsvariabelenmatrix: rijen zijn [P_grid, P_charge, P_discharge].
        SOC (np.ndarray): SOC-verloop over tijd (N+1 waarden).
        status (str): Optimalisatiestatus (bijv. 'optimal').
    """
    U: np.ndarray
    SOC: np.ndarray
    status: str
