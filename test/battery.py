import cvxpy as cp
import numpy as np
import time

# Parameters
N = 8800
np.random.seed(42)
price = np.random.uniform(0.15, 0.3, N)
load = np.random.uniform(4, 6, N)
pv_gen = np.random.uniform(0, 2, N)

# Batterij instellingen

soc_init = 0.5
soc_min = 0.2
soc_max = 0.9
eta_ch = 0.95
eta_dis = 0.9
capacity_kWh = 10
dt = 1.0
alpha = dt * eta_ch / capacity_kWh
beta = dt / (eta_dis * capacity_kWh)

# ---- Scenario 1: Met batterij + PV ----
print("\n🔋 Scenario 1: MET batterij + PV")
P_grid_1 = cp.Variable(N)
P_charge = cp.Variable(N)
P_discharge = cp.Variable(N)
SOC = cp.Variable(N + 1)
constraints_1 = [SOC[0] == soc_init]

for t in range(N):
    net_load = load[t] - pv_gen[t] + P_charge[t] - P_discharge[t]
    constraints_1 += [
        P_grid_1[t] == net_load,
        P_grid_1[t] >= 0,
        P_charge[t] >= 0,
        P_discharge[t] >= 0,
        SOC[t+1] == SOC[t] + alpha * P_charge[t] - beta * P_discharge[t],
        SOC[t+1] >= soc_min,
        SOC[t+1] <= soc_max,
    ]

cost_1 = cp.sum(cp.multiply(price, P_grid_1))
problem_1 = cp.Problem(cp.Minimize(cost_1), constraints_1)
start_1 = time.time()
problem_1.solve(solver=cp.OSQP, eps_abs=1e-3, eps_rel=1e-3, max_iter=20000, verbose=True)
end_1 = time.time()

# ---- Scenario 2: Zonder batterij, wél PV ----
print("\n☀️ Scenario 2: ZONDER batterij, WÉL PV")
P_grid_2 = cp.Variable(N)
constraints_2 = [
    P_grid_2[t] == cp.maximum(load[t] - pv_gen[t], 0) for t in range(N)
]
cost_2 = cp.sum(cp.multiply(price, P_grid_2))
problem_2 = cp.Problem(cp.Minimize(cost_2), constraints_2)
start_2 = time.time()
problem_2.solve(solver=cp.OSQP, eps_abs=1e-3, eps_rel=1e-3, max_iter=20000, verbose=True)
end_2 = time.time()

# ---- Scenario 3: Zonder batterij, zonder PV ----
print("\n🚫 Scenario 3: ZONDER batterij, ZONDER PV")
P_grid_3 = cp.Variable(N)
constraints_3 = [
    P_grid_3[t] == load[t] for t in range(N)  # alles komt van het net
]
cost_3 = cp.sum(cp.multiply(price, P_grid_3))
problem_3 = cp.Problem(cp.Minimize(cost_3), constraints_3)
start_3 = time.time()
problem_3.solve(solver=cp.OSQP, eps_abs=1e-3, eps_rel=1e-3, max_iter=20000, verbose=True)
end_3 = time.time()


# ---- Scenario 4: Alleen batterij, géén PV ----
print("\n🔄 Scenario 4: ALLEEN batterij (prijsarbitrage)")

P_grid_buy = cp.Variable(N)     # stroom inkopen uit net
P_grid_sell = cp.Variable(N)    # teruglevering aan net
P_charge_batt = cp.Variable(N)
P_discharge_batt = cp.Variable(N)
SOC_batt = cp.Variable(N + 1)

constraints_4 = [SOC_batt[0] == soc_init]

for t in range(N):
    # Balans: batterij bepaalt of we in- of verkopen
    constraints_4 += [
        P_grid_buy[t] - P_grid_sell[t] == P_charge_batt[t] - P_discharge_batt[t],
        P_grid_buy[t] >= 0,
        P_grid_sell[t] >= 0,
        P_charge_batt[t] >= 0,
        P_discharge_batt[t] >= 0,
        SOC_batt[t+1] == SOC_batt[t] + alpha * P_charge_batt[t] - beta * P_discharge_batt[t],
        SOC_batt[t+1] >= soc_min,
        SOC_batt[t+1] <= soc_max
    ]

# Doel: koop laag, verkoop hoog
cost_4 = cp.sum(cp.multiply(price, P_grid_buy) - cp.multiply(price, P_grid_sell))
problem_4 = cp.Problem(cp.Minimize(cost_4), constraints_4)

start_4 = time.time()
problem_4.solve(solver=cp.OSQP, eps_abs=1e-3, eps_rel=1e-3, max_iter=20000, verbose=True)
end_4 = time.time()

# ---- Resultaten ----
print("\n📊 Resultaten:")
print(f"✅ Met batterij + PV:       € {round(cost_1.value, 2)}  | Tijd: {round(end_1 - start_1, 2)} s")
print(f"☀️ Zonder batterij, wél PV: € {round(cost_2.value, 2)}  | Tijd: {round(end_2 - start_2, 2)} s")
print(f"🚫 Zonder PV/batterij:      € {round(cost_3.value, 2)}  | Tijd: {round(end_3 - start_3, 2)} s")
print(f"🔄 Alleen batterij:         € {round(cost_4.value, 2)}  | Tijd: {round(end_4 - start_4, 2)} s")


print("\n💰 Besparingen:")
print(f"- T.o.v. géén PV/batterij: batterij + PV bespaart € {round(cost_3.value - cost_1.value, 2)}")
print(f"- T.o.v. geen PV/batterij;  PV bespaart       € {round(cost_3.value - cost_2.value, 2)}")
print(f"- T.o.v. alleen PV; Batterij + PV bespaart € {round(cost_2.value - cost_1.value, 2)}")
print(f"- T.o.v. geen PV/batterij;Alleen batterij:   € {round(cost_3.value - cost_4.value, 2)}")