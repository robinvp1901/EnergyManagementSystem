from dataclasses import dataclass
import numpy as np


@dataclass
class DataGenerator:
    T: int
    seed: int = 42

    def generate_load(self) -> np.ndarray:
        np.random.seed(self.seed)

        # 24-uurs profiel met gewenste pieken op juiste uren
        # (reële verhouding, ochtendpiek = 3, avondpiek = 5)
        day_profile = np.array([
            0.2, 0.2, 0.2, 0.2,    # 0-3
            0.3, 0.5, 1.5, 3.0,    # 4-7 ochtendpiek
            1.2, 0.6, 0.4, 0.3,    # 8-11
            0.3, 0.4, 0.5, 0.7,    # 12-15
            1.0, 2.5, 5.0, 3.5,    # 16-19 avondpiek
            2.0, 1.0, 0.6, 0.3     # 20-23
        ])

        # Schaal naar gemiddeld 0.276 kWh per uur (2420 kWh/jaar)
        avg_day_profile = day_profile.mean()
        target_hourly_avg = (2420 / 365) / 24  # ≈ 0.276
        scale_factor = target_hourly_avg / avg_day_profile
        scaled_day = day_profile * scale_factor

        # Herhaal over simulatieperiode T
        load = np.tile(scaled_day, self.T // 24 + 2)[:self.T]

        # Voeg ruis toe
        load += np.random.normal(0, 0.02, self.T)  # minder ruis voor behoud pieken
        load = np.clip(load, 0.1, 5.0)

        return load

    def generate_irradiance(self) -> np.ndarray:
        np.random.seed(self.seed)
        """
        Genereert een gesimuleerd irradiantieprofiel op uurbasis over T tijdstappen.

        Parameters:
            T (int): Aantal tijdstappen (bijv. uren in een jaar)
            seed (int): Random seed voor reproduceerbaarheid

        Returns:
            np.ndarray: Array met gesimuleerde irradiantiewaarden per uur
        """
        hours_per_day = 24
        days = self.T // hours_per_day
        irradiance = np.zeros(self.T)

        for d in range(days):
            for h in range(hours_per_day):
                t = d * hours_per_day + h
                hour_angle = np.pi * (h - 6) / 12  # piek rond 12u
                base_irradiance = max(0, np.sin(hour_angle))  # dagcurve
                cloud_factor = np.random.uniform(0.6, 1.0)  # variatie per uur
                irradiance[t] = base_irradiance * cloud_factor

        return irradiance
