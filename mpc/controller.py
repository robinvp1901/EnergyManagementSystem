import cvxpy as cp
import numpy as np
from models.mpc_data import MPCInputData, MPCResult
from models.battery import Battery


def run_full_mpc(data: MPCInputData, battery: Battery) -> MPCResult:
    """
    Voert een MPC-optimalisatie uit over de volledige tijdshorizon.
    Er wordt gerekend met een batterij en PV-opwekking, zonder sliding window.
    De kosten worden geminimaliseerd op basis van netverbruik en prijs.

    Args:
        data (MPCInputData): Gegevens over belasting, PV, prijs en initieel SOC.
        battery (Battery): Batterijobject met eigenschappen en limieten.

    Returns:
        MPCResult: Optimalisatieresultaat met SOC-profiel en vermogensbeslissingen.
    """
    N = len(data.P_load)
    dt = 1.0
    alpha = dt * battery.eta_ch / battery.capacity_kWh
    beta = dt / (battery.eta_dis * battery.capacity_kWh)

    P_grid = cp.Variable(N)
    P_charge = cp.Variable(N)
    P_discharge = cp.Variable(N)
    SOC = cp.Variable(N + 1)

    constraints = [SOC[0] == data.soc_init]

    for t in range(N):
        net_load = data.P_load[t] - data.P_pv[t] + P_charge[t] - P_discharge[t]
        constraints += [
            P_grid[t] == net_load,
            P_grid[t] >= 0,
            P_charge[t] >= 0,
            P_discharge[t] >= 0,
            SOC[t+1] == SOC[t] + alpha * P_charge[t] - beta * P_discharge[t],
            SOC[t+1] >= battery.soc_min,
            SOC[t+1] <= battery.soc_max
        ]

    cost = cp.sum(cp.multiply(data.price, P_grid))
    problem = cp.Problem(cp.Minimize(cost), constraints)
    problem.solve(solver=cp.OSQP, eps_abs=1e-3, eps_rel=1e-3, max_iter=20000)

    return MPCResult(
        U=np.vstack([P_grid.value, P_charge.value, P_discharge.value]),
        SOC=SOC.value,
        status=problem.status
    )