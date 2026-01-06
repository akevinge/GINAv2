"""
Calculate theoretical gas mass flow rate based on given parameters.
"""

import math
import numpy as np
from scipy.constants import R
import matplotlib.pyplot as plt
from typing import Literal

from conversions import psi_to_pa, pa_to_psi, mm2_to_m2, bar_to_psi, m3_to_gal
from properties import (
    get_n2_molar_mass,
    get_gox_molar_mass,
    get_n2_density,
    get_gox_density,
    get_eth_density,
    get_water_density,
)

FIRE_DURATION = 5 # s 
GAS: Literal["N2"] | Literal["GOX"] = "GOX"
LIQUID: Literal["ETHANOL"] | Literal["WATER"] = "ETHANOL"
IDEAL_TOTAL_MDOT = 0.1442994641
OF_RATIO = 1.3
DESIRED_GAS_MDOT = IDEAL_TOTAL_MDOT * (OF_RATIO / (OF_RATIO + 1))
print("Ideal gas mdot (kg/s):", DESIRED_GAS_MDOT)
DIATOMIC_GAMMA = 1.4
OUTLET_PRESSURE = bar_to_psi(20)  # psi
STAGNATION_TEMPERATURE = 293  # K
GAS_OUTLET_AREA = mm2_to_m2(11.5185) * 2
LIQUID_OUTLET_AREA = mm2_to_m2(3.0219) * 2
Cd = 0.7  # Assumption

specific_gas_constant = R / (
    get_n2_molar_mass() if GAS == "N2" else get_gox_molar_mass()
)
print("Specific Gas Constant (J/kg-K):", specific_gas_constant)
get_gas_density_fn = get_n2_density if GAS == "N2" else get_gox_density
get_liquid_density_fn = get_eth_density if LIQUID == "ETHANOL" else get_water_density


def critical_pressure_ratio(gamma=DIATOMIC_GAMMA):
    return (2 / (gamma + 1)) ** (gamma / (gamma - 1))


def choked_gas_mdot(Cd, P0, T0, A, gamma=DIATOMIC_GAMMA, R=specific_gas_constant):
    return (
        (Cd * A * P0 / math.sqrt(T0))
        * math.sqrt(gamma / R)
        * ((gamma + 1) / 2) ** (-(gamma + 1) / (2 * (gamma - 1)))
    )


def compressible_m_flow_rate(A: float, p1: float, p2: float, rho1: float, gamma: float):
    p_ratio = p2 / p1
    return A * (
        Cd
        * math.sqrt(
            2
            * rho1
            * p1
            * (
                (gamma / (gamma - 1))
                * (p_ratio ** (2 / gamma) - p_ratio ** ((gamma + 1) / gamma))
            )
        )
    )


def incompressible_mdot(Cd: float, A: float, rho: float, dP: float):
    return Cd * A * math.sqrt(2 * rho * dP)


def incompresible_dP(Cd: float, A: float, rho: float, mdot: float):
    return (mdot / (Cd * A)) ** 2 / (2 * rho)


critical_pressure_ratio = critical_pressure_ratio(DIATOMIC_GAMMA)
print("Diatomic Gas Critical Pressure Ratio:", critical_pressure_ratio)

minimum_choked_inlet_pressure = psi_to_pa(OUTLET_PRESSURE) / critical_pressure_ratio

# Possible inlet pressures that exceed the critical pressure ratio for choked flow
possible_inlet_pressures = np.linspace(
    psi_to_pa(OUTLET_PRESSURE) + 1, psi_to_pa(1000), num=100
)
gas_mdots = [
    (
        choked_gas_mdot(Cd, P0, T0=STAGNATION_TEMPERATURE, A=GAS_OUTLET_AREA)
        if P0 >= minimum_choked_inlet_pressure
        else compressible_m_flow_rate(
            A=GAS_OUTLET_AREA,
            p1=P0,
            p2=psi_to_pa(OUTLET_PRESSURE),
            rho1=get_gas_density_fn(P0, STAGNATION_TEMPERATURE),
            gamma=DIATOMIC_GAMMA,
        )
    )
    for P0 in possible_inlet_pressures
]
# Find the pressure that gives the ideal gas mdot
best_pressure_index = np.argmin(np.abs(np.array(gas_mdots) - DESIRED_GAS_MDOT))
print(
    "Best inlet pressure (psi):",
    pa_to_psi(possible_inlet_pressures[best_pressure_index]),
    "kg/s:",
    gas_mdots[best_pressure_index],
)

# Chart the results
plt.plot(
    pa_to_psi(possible_inlet_pressures),
    gas_mdots,
    label=f"{GAS} Mass Flow Rate w/ Cd={Cd}",
)
plt.axhline(
    DESIRED_GAS_MDOT,
    color="red",
    linestyle="--",
    label=f"Desired {GAS} Mass Flow Rate",
)
# Plot vertical line for minimum choked inlet pressure
plt.axvline(
    pa_to_psi(minimum_choked_inlet_pressure),
    color="orange",
    linestyle="--",
    label="Minimum Choked Inlet Pressure",
)
# Plot point which is closest to desired mdot and label it
plt.plot(
    pa_to_psi(possible_inlet_pressures[best_pressure_index]),
    gas_mdots[best_pressure_index],
    "go",
    label=f"Optimal Inlet Pressure Point ({pa_to_psi(possible_inlet_pressures[best_pressure_index]):.1f} psi, {gas_mdots[best_pressure_index]:.3f} kg/s)",
)
plt.xlabel("Inlet Pressure (psi)")
plt.ylabel("Mass Flow Rate (kg/s)")
plt.title(
    f"{GAS} Mass Flow Rate vs Inlet Pressure w/ Cd={Cd}, O/F={OF_RATIO}, T={STAGNATION_TEMPERATURE}K, P_out={round(OUTLET_PRESSURE, 2)}psi"
)
plt.legend()
plt.grid()
plt.show()


# Calculate the theoretical flow rate of liquid
liquid_mdot = IDEAL_TOTAL_MDOT - gas_mdots[best_pressure_index]
dP = incompresible_dP(
    Cd=Cd,
    A=LIQUID_OUTLET_AREA,
    rho=get_liquid_density_fn(
        psi_to_pa(OUTLET_PRESSURE) + 1,  # Slightly above outlet pressure
        STAGNATION_TEMPERATURE,
    ),
    mdot=liquid_mdot,
)
dP_precent = dP / (psi_to_pa(OUTLET_PRESSURE)) * 100
print(
    f"dP required for {LIQUID} flow (psi): {pa_to_psi(dP)} = {dP_precent:.2f}% of outlet pressure"
)

# Calculate volume needed to sustain `FIRE_DURATION`
liquid_vol = m3_to_gal(liquid_mdot * FIRE_DURATION / get_liquid_density_fn(
        psi_to_pa(OUTLET_PRESSURE) + 1,  # Slightly above outlet pressure
        STAGNATION_TEMPERATURE,
))

print(f"Volume of {LIQUID} required for {FIRE_DURATION}: {liquid_vol} gal")


gas_mdot = gas_mdots[best_pressure_index]
gas_inlet_pressure = possible_inlet_pressures[best_pressure_index]
gas_density = get_gas_density_fn(
    possible_inlet_pressures[best_pressure_index], STAGNATION_TEMPERATURE
)
vel_gox = gas_mdot / (gas_density * GAS_OUTLET_AREA)

liquid_inlet_pressure = psi_to_pa(OUTLET_PRESSURE) + dP
vel_eth = liquid_mdot / (
    get_liquid_density_fn(liquid_inlet_pressure, STAGNATION_TEMPERATURE)
    * LIQUID_OUTLET_AREA
)
J = vel_gox / vel_eth
print(f"{GAS} Velocity at outlet (m/s):", vel_gox)
print(f"{LIQUID} Velocity at outlet (m/s):", vel_eth)
print(f"Velocity Ratio J = V_gas / V_liquid:", J)
