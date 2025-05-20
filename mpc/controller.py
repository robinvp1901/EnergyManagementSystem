import cvxpy as cp
import numpy as np
from models.mpc_data import MPCInputData, MPCResult
from models.battery import Battery


def run_full_mpc(data: MPCInputData, battery: Battery) -> MPCResult:
    """
    Optimaliseert energieverdeling over volledige tijdshorizon (N tijdstappen).
    Houdt rekening met:
    - PV-afschakeling (P_pv_used ≤ P_pv_available)
    - SOC-beperkingen op basis van actuele capaciteit
    - Laad/ontlaadvermogenslimieten
    - Ramp rate beperkingen voor P_charge en P_discharge

    Args:
        data (MPCInputData): Vraag, PV-aanbod, prijs, initiele SOC
        battery (Battery): Batterijparameters

    Returns:
        MPCResult: Optimalisatie-uitvoer: U (4×N), SOC, status
    """
    if battery is None or battery.capacity_kWh == 0:
        # Simulatie zonder batterij
        N = len(data.P_load)
        P_grid = cp.Variable(N)
        P_pv_used = cp.Variable(N)
        constraints = []

        for t in range(N):

            constraints += [
                P_pv_used[t] >= 0,
                P_pv_used[t] <= data.P_pv_available[t],
                P_grid[t] >= 0,
                P_grid[t] == data.P_load[t] - P_pv_used[t]
            ]

        cost = cp.sum(cp.multiply(data.price, P_grid))
        problem = cp.Problem(cp.Minimize(cost), constraints)
        problem.solve(solver=cp.ECOS_BB,
                      verbose=False,
                      max_iters=10000,
                      abstol=1e-5,
                      reltol=1e-5,
                      feastol=1e-5
                      )

        return MPCResult(
            U=np.vstack([
                P_grid.value,
                np.zeros(N),  # P_charge
                np.zeros(N),  # P_discharge
                P_pv_used.value,
                np.zeros(N),
                np.zeros(N)
            ]),
            SOC=np.zeros(N+1),
            status=problem.status
        )

    N = len(data.P_load)

    # Efficiëntie-coëfficiënten op basis van actuele capaciteit
    alpha = battery.eta_ch / battery.capacity_kWh
    beta = 1 / (battery.eta_dis * battery.capacity_kWh)

    # Variabelen
    P_grid = cp.Variable(N)
    P_charge = cp.Variable(N)
    P_discharge = cp.Variable(N)
    P_pv_used = cp.Variable(N)
    SOC = cp.Variable(N + 1)
    z = cp.Variable(N, boolean=True)

    # Begin-SOC
    constraints = [SOC[0] == data.soc_init]

    # Constraints per tijdstap
    for t in range(N):
        if t > 0:
            # Ramp rate beperkingen (ΔP ≤ limiet)
            constraints += [
                cp.abs(P_charge[t] - P_charge[t-1]) <= battery.ramp_charge,
                cp.abs(P_discharge[t] - P_discharge[t-1]) <= battery.ramp_discharge,
            ]

        net_load = data.P_load[t] - P_pv_used[t] + P_charge[t] - P_discharge[t]

        constraints += [
            # Vermogensbalans
            P_grid[t] == net_load,

            # Fysieke grenzen
            P_grid[t] >= 0,
            P_charge[t] >= 0,
            P_discharge[t] >= 0,

            # PV-gebruik beperkingen
            P_pv_used[t] >= 0,
            P_pv_used[t] <= data.P_pv_available[t],

            # SOC-dynamiek
            SOC[t+1] == SOC[t] + alpha * P_charge[t] - beta * P_discharge[t],
            SOC[t+1] >= battery.soc_min,
            SOC[t+1] <= battery.soc_max,

            # Big-M constraints voor gelijktijdig laden en ontladen voorkomen
            P_charge[t] <= z[t] * battery.power_max_charge,
            P_discharge[t] <= (1 - z[t]) * battery.power_max_discharge,
            z[t] >= 0,
            z[t] <= 1,
        ]

    # Kosten: minimaliseer totale energiekosten en stimuleer laden met overtollige PV
    # Stimuleer laden met overtollige PV
    weight_pv_charge = 0.05  # stel een positieve waarde in om laden met PV te stimuleren
    pv_charge_penalty = -cp.sum(cp.minimum(P_charge, data.P_pv_available)) * weight_pv_charge

    weight_discharge_price = 0.025  # stem af op gewenste agressiviteit
    discharge_reward = cp.sum(cp.multiply(P_discharge, data.price)) * weight_discharge_price

    cost = cp.sum(cp.multiply(data.price, P_grid)) \
         + pv_charge_penalty \
         - discharge_reward

    # Optimalisatieprobleem
    # ======================= OPTIMALISATIEPROBLEEM DEFINITIE =======================
    problem = cp.Problem(cp.Minimize(cost), constraints)
    problem.solve(solver=cp.ECOS_BB,
                  verbose=False,
                  max_iters=10000,
                  abstol=1e-5,
                  reltol=1e-5,
                  feastol=1e-5)

    # Output
    return MPCResult(
        U=np.vstack([
            P_grid.value,
            P_charge.value,
            P_discharge.value,
            P_pv_used.value,
            np.minimum(P_charge.value, data.P_pv_available),  # PV naar batterij
            np.minimum(P_pv_used.value, data.P_load)          # PV naar load
        ]),
        SOC=SOC.value,
        status=problem.status
    )
