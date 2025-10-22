import math
import dataclasses
import numpy as np
import matplotlib.pyplot as plt
from copy import copy
from typing import Callable

from pyfluids import Fluid, FluidsList, Input
from scipy.constants import convert_temperature, bar, psi


def bar_to_pa(p):
    return p * bar


def bar_to_psi(p):
    return (p * bar) / psi


def optional_print(s: str, should_print: bool = False):
    if should_print:
        print(s)


@dataclasses.dataclass
class Parameters:
    chamber_P: float
    of: float
    total_m_float_rate: float
    gox_inlet_dP_frac: float
    ethanol_inlet_dP_frac: float
    coaxial_post_wall_thickness_mm: float


@dataclasses.dataclass
class SizingOutcomes:
    vel_gox: float
    vel_eth: float
    V_ratio: float
    J: float
    A_ratio: float
    A_gox: float
    A_eth: float


Cd = 0.7
GOX_GAMMA = 1.4
GOX_INLET_T = 300  # K
ETHANOL_INLET_T = 300  # K
TOTAL_M_FLOW_RATE = 0.1442994641


def separate_m_flow_rate(m_flow: float, of: float) -> tuple[float, float]:
    return (m_flow * (of / (1 + of)), m_flow * (1 / (of + 1)))


def get_gox_density(p: float, t: float) -> float:
    return (
        Fluid(FluidsList.Oxygen, 100)
        .with_state(
            Input.pressure(p),
            Input.temperature(convert_temperature(t, "K", "C")),
        )
        .density
    )


def get_eth_density(p: float, t: float) -> float:
    return (
        Fluid(FluidsList.Ethanol, 100)
        .with_state(
            Input.pressure(p),
            Input.temperature(convert_temperature(t, "K", "C")),
        )
        .density
    )


def is_choked_flow(p1: float, p2: float, gamma: float):
    return (p2 / p1) <= ((2 / (gamma + 1)) ** (gamma / (gamma - 1)))


def choked_flow_area(m_flow_rate: float, p1: float, rho1: float, gamma: float) -> float:
    return m_flow_rate / (
        Cd
        * math.sqrt(
            gamma * rho1 * p1 * ((2 / (gamma + 1)) ** ((gamma + 1) / (gamma - 1)))
        )
    )


def choked_m_flow_rate(A: float, p1: float, rho1: float, gamma: float) -> float:
    return A * (
        Cd
        * math.sqrt(
            gamma * rho1 * p1 * ((2 / (gamma + 1)) ** ((gamma + 1) / (gamma - 1)))
        )
    )


def compressible_flow_area(
    m_flow_rate: float, p1: float, p2: float, rho1: float, gamma: float
) -> float:
    p_ratio = p2 / p1
    return m_flow_rate / (
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


def calculate_p1(
    target_mdot: float,
    A: float,
    p1_guess: float,
    p2: float,
    gamma: float,
    t: float,
    get_density: Callable[[float, float], float],
    learning_rate=0.001,
    max_iter=2000,
    tol=1e-5,
) -> float:
    """
    Calculates the required inlet pressure to achieve a target mass flow rate across an orifice of a given size.

    Uses iterative solving/gradient descent-esq algorithm to work backwards.
    """
    p1 = p1_guess
    error = None

    for _ in range(max_iter):
        # Compute predicted flow rate from current p1
        p_ratio = p2 / p1
        if p_ratio >= 1:
            p_ratio = 0.9999  # avoid invalid domain

        rho1 = get_density(p1, t)

        # compressible flow equation
        is_choked = is_choked_flow(p1=p1, p2=p2, gamma=gamma)

        mdot = (
            compressible_m_flow_rate(A=A, p1=p1, p2=p2, rho1=rho1, gamma=gamma)
            if not is_choked
            else choked_m_flow_rate(A=A, p1=p1, rho1=rho1, gamma=gamma)
        )
        error = mdot - target_mdot

        if abs(error) < tol:
            break

        # Numerical derivative (finite difference)
        delta = 1e-5 * p1
        p1_high = p1 + delta
        is_choked = is_choked_flow(p1=p1, p2=p2, gamma=gamma)
        rho1_high = get_density(p1_high, t)

        mdot_high = (
            compressible_m_flow_rate(
                A=A, p1=p1_high, p2=p2, rho1=rho1_high, gamma=gamma
            )
            if not is_choked
            else choked_m_flow_rate(A=A, p1=p1_high, rho1=rho1_high, gamma=gamma)
        )

        dmdot_dp1 = (mdot_high - mdot) / delta

        # Gradient descent / Newton step
        p1 -= learning_rate * error / (dmdot_dp1 + 1e-12)

        # Prevent non-physical negative pressures
        if p1 <= p2:
            p1 = p2 * 1.001

    return p1


def calculate_injector_element_geometry(
    num_elements: int, P: Parameters, should_print: bool = False
) -> SizingOutcomes:
    """
    Calculates the geometry for a single injector element given the total
    number of elements on the faceplate.
    """
    optional_print(
        f"\n-------- Calculating for {num_elements} Element(s) --------", should_print
    )
    optional_print(params, should_print)

    gox_inlet_p = P.chamber_P * (1 + P.gox_inlet_dP_frac)
    eth_inlet_p = P.chamber_P * (1 + P.ethanol_inlet_dP_frac)
    gox_dP = gox_inlet_p - P.chamber_P  # bar
    eth_dP = eth_inlet_p - P.chamber_P  # bar
    optional_print(f"ΔEthanol P: {bar_to_psi(eth_dP)} psi", should_print)
    optional_print(f"ΔGOX P: {bar_to_psi(gox_dP)} psi", should_print)

    # --- Mass Flow Per Element ---
    m_flow_rate_per_element = P.total_m_float_rate / num_elements
    gox_m_flow_rate, ethanol_m_flow_rate = separate_m_flow_rate(
        m_flow=m_flow_rate_per_element, of=P.of
    )

    # --- Fluid Properties ---
    gox_inlet_density = get_gox_density(p=bar_to_pa(gox_inlet_p), t=GOX_INLET_T)
    ethanol_inlet_density = get_eth_density(p=bar_to_pa(eth_inlet_p), t=ETHANOL_INLET_T)

    # --- GOX Orifice Area Calculation (Unchoked Flow) ---
    if is_choked_flow(p1=gox_inlet_p, p2=P.chamber_P, gamma=GOX_GAMMA):
        optional_print(
            "----------> Calculating for compressible choked flow", should_print
        )
        A_gox = choked_flow_area(
            m_flow_rate=gox_m_flow_rate,
            p1=bar_to_pa(gox_inlet_p),
            rho1=gox_inlet_density,
            gamma=GOX_GAMMA,
        )
        Vel_gox = gox_m_flow_rate / (gox_inlet_density * A_gox)
        optional_print(f"GOX orifice area: {A_gox * 1e6} mm^2", should_print)
        optional_print(f"GOX velocity at the orifice: {Vel_gox} m/s", should_print)
    else:
        # https://en.wikipedia.org/wiki/Orifice_plate#Compressible_flow
        optional_print(
            "----------> Caculating for compressible un-choked flow", should_print
        )
        A_gox = compressible_flow_area(
            m_flow_rate=gox_m_flow_rate,
            p1=bar_to_pa(gox_inlet_p),
            p2=bar_to_pa(P.chamber_P),
            rho1=gox_inlet_density,
            gamma=GOX_GAMMA,
        )
        Vel_gox = gox_m_flow_rate / (gox_inlet_density * A_gox)
        optional_print(f"GOX orifice area: {A_gox * 1e6} mm^2", should_print)
        optional_print(f"GOX velocity at the orifice: {Vel_gox} m/s", should_print)

    # --- Ethanol Orifice Area Calculation ---
    A_eth = ethanol_m_flow_rate / (
        Cd * math.sqrt(2 * ethanol_inlet_density * bar_to_pa(eth_dP))
    )
    Vel_eth = ethanol_m_flow_rate / (ethanol_inlet_density * A_eth)

    # --- Calculate Element Geometry (assuming GOX Annular, Ethanol Centric) ---
    A_eth_mm2 = A_eth * 1e6
    A_gox_mm2 = A_gox * 1e6

    # Ethanol (centric) is the inner element
    D_eth_inner = math.sqrt(4 * A_eth_mm2 / math.pi)

    # Assume a wall thickness for the ethanol post, e.g., 1 mm
    # So the OD is the ID + 2 * wall_thickness
    D_eth_post_OD = (
        D_eth_inner + 2 * P.coaxial_post_wall_thickness_mm
    )  # This is the "post" diameter

    # The area of the post itself
    A_post_mm2 = (math.pi / 4) * (D_eth_post_OD**2)

    # The GOX (annular) flows around the ethanol post.
    # The total area occupied by the GOX and the post is A_outer.
    A_outer_mm2 = A_gox_mm2 + A_post_mm2
    D_gox_outer = math.sqrt(4 * A_outer_mm2 / math.pi)

    vel_ratio = Vel_gox / Vel_eth
    J = (gox_inlet_density * (Vel_gox**2)) / (ethanol_inlet_density * (Vel_eth**2))
    A_ratio = A_gox / A_eth

    optional_print("\n--- Overall sizing outcomes ---", should_print)
    optional_print(f"Velocity ratio (gox/eth) {vel_ratio}", should_print)
    optional_print(f"J (g/l): {J}", should_print)
    optional_print(f"Area Ratio: (g/l): {A_ratio}", should_print)

    # --- Print Results for a Single Element ---
    optional_print(
        f"Mass Flow Rate per Element: {m_flow_rate_per_element:.4f} kg/s", should_print
    )
    optional_print(f"Required GOX Orifice Area: {A_gox_mm2:.4f} mm^2", should_print)
    optional_print(f"Required Ethanol Orifice Area: {A_eth_mm2:.4f} mm^2", should_print)
    optional_print("\n--- Single Element Dimensions ---", should_print)
    optional_print(f"Ethanol Inner Diameter (ID): {D_eth_inner:.4f} mm", should_print)
    optional_print(
        f"Ethanol Post Outer Diameter (OD): {D_eth_post_OD:.4f} mm", should_print
    )
    optional_print(
        f"GOX Annulus Outer Diameter (OD): {D_gox_outer:.4f} mm", should_print
    )

    return SizingOutcomes(
        vel_eth=Vel_eth,
        vel_gox=Vel_gox,
        V_ratio=Vel_gox / Vel_eth,
        J=J,
        A_ratio=A_ratio,
        A_gox=A_gox,
        A_eth=A_eth,
    )


def calculate_vel_at_fixed_A(
    m_dot, of, gox_inlet_p, eth_inlet_p, A_gox, A_eth
) -> tuple[float, float]:
    """
    Calculate the velocity of both propellants (assuming incompressibility)
    across an orifice for a given mass flow rate.
    """
    gox_m_flow_rate, ethanol_m_flow_rate = separate_m_flow_rate(m_dot, of)
    gox_inlet_density = get_gox_density(gox_inlet_p, GOX_INLET_T)
    ethanol_inlet_density = get_eth_density(eth_inlet_p, ETHANOL_INLET_T)
    return (
        gox_m_flow_rate / (gox_inlet_density * A_gox),
        ethanol_m_flow_rate / (ethanol_inlet_density * A_eth),
    )


params = Parameters(
    chamber_P=20,
    total_m_float_rate=TOTAL_M_FLOW_RATE,
    of=1.3,
    gox_inlet_dP_frac=0.25,
    ethanol_inlet_dP_frac=0.07,
    coaxial_post_wall_thickness_mm=0.5,
)

sizing = calculate_injector_element_geometry(
    num_elements=2, P=params, should_print=True
)

ofs = np.linspace(1.0, 5.0, 20)
vel_ratios_gox = []
gox_dps = []

for of in ofs:
    params.of = of
    design_gox_inlet_p = params.chamber_P * (1 + params.gox_inlet_dP_frac)
    design_eth_inlet_p = params.chamber_P * (1 + params.ethanol_inlet_dP_frac)

    gox_m_flow_rate, _ = separate_m_flow_rate(m_flow=params.total_m_float_rate, of=of)
    adjusted_gox_inlet_p = calculate_p1(
        target_mdot=gox_m_flow_rate / 2,
        A=sizing.A_gox,
        p1_guess=bar_to_pa(design_gox_inlet_p),
        p2=bar_to_pa(params.chamber_P),
        gamma=GOX_GAMMA,
        t=GOX_INLET_T,
        get_density=get_gox_density,
        max_iter=10000,
        tol=1e-6,
    )
    print(f"Adjusted GOX P: {adjusted_gox_inlet_p / bar}")

    out = calculate_vel_at_fixed_A(
        m_dot=params.total_m_float_rate,
        of=of,
        gox_inlet_p=adjusted_gox_inlet_p,
        eth_inlet_p=bar_to_pa(design_eth_inlet_p),
        A_gox=sizing.A_gox,
        A_eth=sizing.A_eth,
    )
    gox_dps.append(
        (adjusted_gox_inlet_p - bar_to_pa(params.chamber_P))
        / bar_to_pa(params.chamber_P)
    )
    print(of, out)

    vel_ratios_gox.append((out[0] / out[1]))

plt.figure(figsize=(8, 5))
plt.plot(ofs, vel_ratios_gox, label="Velocity Ratio (GOX/Ethanol)", marker="o")
plt.xlabel("O/F Ratio")
plt.ylabel("Ratio Value")
plt.title("Effect of O/F Ratio on Injector Ratios")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()

plt.figure(figsize=(8, 5))
plt.plot(ofs, gox_dps, label="GOX dP", marker="o")
plt.xlabel("O/F Ratio")
plt.ylabel("GOX dP")
plt.title("Effect of O/F Ratio on GOX dP")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()
