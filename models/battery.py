from dataclasses import dataclass

@dataclass
class Battery:
    """
    Dataclass die de eigenschappen en grenzen van een batterij beschrijft.

    Attributen:
        soc (float): Huidige state-of-charge [0–1].
        soc_min (float): Minimale toegestane SOC.
        soc_max (float): Maximale toegestane SOC.
        eta_ch (float): Laad-efficiëntie (0–1).
        eta_dis (float): Ontlaad-efficiëntie (0–1).
        capacity_kWh (float): Totale batterijcapaciteit in kWh.
    """
    soc: float
    soc_min: float = 0.2
    soc_max: float = 0.9
    eta_ch: float = 0.95
    eta_dis: float = 0.9
    capacity_kWh: float = 10.0