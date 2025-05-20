from dataclasses import dataclass, field
import numpy as np


@dataclass
class Battery:
    """
    Klasse voor het modelleren van een batterij, inclusief energiecapaciteit, efficiëntie, laad- en ontlaadvermogens,
    stroombegrenzing en degradatie op basis van cyclisch gebruik.

    Attributen:
        soc (float): Huidige State of Charge (SOC) als fractie (0–1).
        soc_min (float): Minimale toegestane SOC.
        soc_max_init (float): Maximale SOC bij nieuwe batterij.
        soc_max (float): Actuele maximale SOC, aangepast op basis van degradatie.

        eta_ch (float): Laadrendement (tussen 0 en 1).
        eta_dis (float): Ontlaadrendement (tussen 0 en 1).

        capacity_kWh_nominal (float): Nominale capaciteit van de batterij in kWh.
        capacity_kWh (float): Actuele capaciteit na degradatie in kWh.

        voltage (float): Spanning van het systeem in Volt.
        max_ampere_charge (float): Maximale laadstroom in Ampère.
        max_ampere_discharge (float): Maximale ontlaadstroom in Ampère.
        power_max_charge (float): Maximale laadvermogen in kW (afgeleid van spanning en stroom).
        power_max_discharge (float): Maximale ontlaadvermogen in kW (afgeleid van spanning en stroom).

        ramp_ampere_charge (float): Maximale verandering in laadstroom per tijdstap in Ampère.
        ramp_ampere_discharge (float): Maximale verandering in ontlaadstroom per tijdstap in Ampère.
        ramp_charge (float): Maximale verandering in laadvermogen per tijdstap (kW).
        ramp_discharge (float): Maximale verandering in ontlaadvermogen per tijdstap (kW).

        max_cycles (int): Aantal cycli waarna de batterij de minimale capaciteit heeft bereikt.
        degradation_c_min (float): Minimale capaciteit in procenten na volledige degradatie.
        degradation_c_max (float): Maximale capaciteit in procenten bij start (afgeleid van soc_max_init).
        degradation_b (float): Parameter voor de logaritmische degradatiecurve.
    """
    soc: float                              # huidige SOC [0–1]
    soc_min: float = 0.2                    # minimale SOC
    soc_max_init: float = 0.95               # initiële maximale SOC
    soc_max: float = field(init=False)       # actuele SOC max (past af bij degradatie)

    eta_ch: float = 0.95                    # laadrendement
    eta_dis: float = 0.9                    # ontlaadrendement

    capacity_kWh_nominal: float = 10.0      # nominale batterijcapaciteit
    capacity_kWh: float = field(init=False)  # actuele capaciteit (degradeert)

    voltage: float = 48.0                               # batterijspanning in Volt

    max_ampere_charge: float = 105.0                    # maximale laadstroom in Ampère
    max_ampere_discharge: float = 105.0                 # maximale ontlaadstroom in Ampère
    power_max_charge: float = field(init=False)         # maximale laadvermogen in kW (afgeleid van V en A)
    power_max_discharge: float = field(init=False)      # maximale ontlaadvermogen in kW (afgeleid van V en A)

    ramp_ampere_charge: float = 80.0                    # maximale verandering in laadstroom per tijdstap
    ramp_ampere_discharge: float = 80.0                 # maximale verandering in ontlaadstroom per tijdstap
    ramp_charge: float = field(init=False)              # maximale verandering in laadvermogen per tijdstap
    ramp_discharge: float = field(init=False)           # maximale verandering in ontlaadvermogen per tijdstap

    max_cycles: int = 6000                              # maximaal aantal cycli

    degradation_c_min: float = 80.0                     # minimale capaciteit in %
    degradation_c_max: float = field(init=False)        # maximale capaciteit in %
    degradation_b: float = 0.5                          # parameter voor logaritmische curve
    used_energy_total: float = field(init=False, default=0.0)

    def __post_init__(self):
        """
        Initialiseert afgeleide attributen na het aanmaken van het Battery-object.

        Zet:
            capacity_kWh (float): op de waarde van capacity_kWh_nominal.
            soc_max (float): op de waarde van soc_max_init.
            power_max_charge (float): op basis van voltage × max_ampere_charge (in kW).
            power_max_discharge (float): op basis van voltage × max_ampere_discharge (in kW).
            ramp_charge (float): op basis van voltage × ramp_ampere_charge (in kW).
            ramp_discharge (float): op basis van voltage × ramp_ampere_discharge (in kW).
        """
        self.capacity_kWh = self.capacity_kWh_nominal
        self.soc_max = self.soc_max_init
        self.power_max_charge = (self.voltage * self.max_ampere_charge) / 1000          # in kW
        self.power_max_discharge = (self.voltage * self.max_ampere_discharge) / 1000    # in kW
        self.ramp_charge = (self.voltage * self.ramp_ampere_charge) / 1000              # in kW
        self.ramp_discharge = (self.voltage * self.ramp_ampere_discharge) / 1000        # in kW
        self.degradation_c_max = self.soc_max_init * 100                                # in %
        self.used_energy_total = 0.0

    def update_degradation(self, used_energy_step: float) -> None:
        """
        Werkt de actuele capaciteit en maximale SOC bij op basis van het totale energieverbruik.

        Args:
            used_energy_total (float): Totale hoeveelheid gebruikte energie sinds de start (in kWh).

        Berekent het aantal cycli op basis van het energieverbruik per volledige laad-ontlaad cyclus
        en past de capaciteit aan volgens een logaritmische degradatiecurve die is afgeleid van:
            - minimale en maximale capaciteitsgrenzen (in %)
            - aantal maximaal toegestane cycli
            - een logaritmische vervalparameter b
        """
        # 1) Accumuleer het éne stapje
        self.used_energy_total += used_energy_step

        # 2) Bereken het aantal cycli
        energy_per_cycle = self.capacity_kWh_nominal * self.soc_max_init * 2
        cycles_used = self.used_energy_total / energy_per_cycle

        # Degradatiecurve
        C_min = self.degradation_c_min
        C_max = self.degradation_c_max
        b = self.degradation_b
        cycles_max = self.max_cycles
        a = (C_max - C_min) / np.log(b * cycles_max)
        cap_percent = C_min + a * np.log(b * (cycles_max - cycles_used + 1))

        cap_kWh = self.capacity_kWh_nominal * (cap_percent / 100)
        self.capacity_kWh = cap_kWh
        self.soc_max = min(self.soc_max_init, cap_kWh / self.capacity_kWh_nominal)
