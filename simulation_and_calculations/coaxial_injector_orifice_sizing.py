import math
import dataclasses
import numpy as np
import matplotlib.pyplot as plt

from pyfluids import Fluid, FluidsList, Input
from scipy.constants import convert_temperature, bar, psi


def bar_to_pa(p):
    return p * bar


def bar_to_psi(p):
    return (p * bar) / psi


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


Cd = 0.7
GOX_GAMMA = 1.4
GOX_INLET_T = 300  # K
ETHANOL_INLET_T = 300  # K


def calculate_injector_element_geometry(num_elements: int, P: Parameters):
    """
    Calculates the geometry for a single injector element given the total
    number of elements on the faceplate.
    """
    print(f"\n-------- Calculating for {num_elements} Element(s) --------")

    gox_inlet_p = P.chamber_P * (1 + P.gox_inlet_dP_frac)
    eth_inlet_p = P.chamber_P * (1 + P.ethanol_inlet_dP_frac)
    gox_dP = gox_inlet_p - P.chamber_P  # bar
    eth_dP = eth_inlet_p - P.chamber_P  # bar
    print(f"ΔEthanol P: {bar_to_psi(eth_dP)} psi")
    print(f"ΔGOX P: {bar_to_psi(gox_dP)} psi")

    # --- Mass Flow Per Element ---
    m_flow_rate_per_element = P.total_m_float_rate / num_elements
    gox_m_flow_rate = m_flow_rate_per_element * (P.of / (1 + P.of))
    ethanol_m_flow_rate = m_flow_rate_per_element * (1 / (P.of + 1))

    # --- Fluid Properties ---
    gox_inlet_density = (
        Fluid(FluidsList.Oxygen, 100)
        .with_state(
            Input.pressure(gox_inlet_p * bar),
            Input.temperature(convert_temperature(GOX_INLET_T, "K", "C")),
        )
        .density
    )
    ethanol_inlet_density = (
        Fluid(FluidsList.Ethanol, 100)
        .with_state(
            Input.pressure(eth_inlet_p * bar),
            Input.temperature(convert_temperature(ETHANOL_INLET_T, "K", "C")),
        )
        .density
    )

    # --- GOX Orifice Area Calculation (Unchoked Flow) ---
    p_ratio = P.chamber_P / gox_inlet_p
    is_choked_flow = (P.chamber_P / gox_inlet_p) <= (
        (2 / (GOX_GAMMA + 1)) ** (GOX_GAMMA / (GOX_GAMMA - 1))
    )

    if is_choked_flow:
        print("----------> Calculating for compressible choked flow")
        A_gox = gox_m_flow_rate / (
            Cd
            * math.sqrt(
                GOX_GAMMA
                * gox_inlet_density
                * bar_to_pa(gox_inlet_p)
                * ((2 / (GOX_GAMMA + 1)) ** ((GOX_GAMMA + 1) / (GOX_GAMMA - 1)))
            )
        )
        Vel_gox = gox_m_flow_rate / (gox_inlet_density * A_gox)
        print(f"GOX orifice area: {A_gox * 1e6} mm^2")
        print(f"GOX velocity at the orifice: {Vel_gox} m/s")
    else:
        # https://en.wikipedia.org/wiki/Orifice_plate#Compressible_flow
        print("----------> Caculating for compressible un-choked flow")
        p_ratio = P.chamber_P / gox_inlet_p
        A_gox = gox_m_flow_rate / (
            Cd
            * math.sqrt(
                2
                * gox_inlet_density
                * (gox_inlet_p * bar)
                * (
                    (GOX_GAMMA / (GOX_GAMMA - 1))
                    * (
                        p_ratio ** (2 / GOX_GAMMA)
                        - p_ratio ** ((GOX_GAMMA + 1) / GOX_GAMMA)
                    )
                )
            )
        )
        Vel_gox = gox_m_flow_rate / (gox_inlet_density * A_gox)
        print(f"GOX orifice area: {A_gox * 1e6} mm^2")
        print(f"GOX velocity at the orifice: {Vel_gox} m/s")

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

    print("\n--- Overall sizing outcomes ---")
    print(f"Velocity ratio (gox/eth) {vel_ratio}")
    print(f"J (g/l): {J}")
    print(f"Area Ratio: (g/l): {A_ratio}")

    # --- Print Results for a Single Element ---
    print(f"Mass Flow Rate per Element: {m_flow_rate_per_element:.4f} kg/s")
    print(f"Required GOX Orifice Area: {A_gox_mm2:.4f} mm^2")
    print(f"Required Ethanol Orifice Area: {A_eth_mm2:.4f} mm^2")
    print("\n--- Single Element Dimensions ---")
    print(f"Ethanol Inner Diameter (ID): {D_eth_inner:.4f} mm")
    print(f"Ethanol Post Outer Diameter (OD): {D_eth_post_OD:.4f} mm")
    print(f"GOX Annulus Outer Diameter (OD): {D_gox_outer:.4f} mm")

    return SizingOutcomes(
        vel_eth=Vel_eth,
        vel_gox=Vel_gox,
        V_ratio=Vel_gox / Vel_eth,
        J=J,
        A_ratio=A_ratio,
    )


params = Parameters(
    chamber_P=20,
    total_m_float_rate=0.1442994641,
    of=1.3,
    gox_inlet_dP_frac=0.9,
    ethanol_inlet_dP_frac=0.07,
    coaxial_post_wall_thickness_mm=0.5,
)

# --- Run the calculation for different element counts ---
calculate_injector_element_geometry(num_elements=1, P=params)
calculate_injector_element_geometry(num_elements=2, P=params)

ethanol_fracs = np.linspace(0.07, 0.2, 10)
gox_fracs = np.linspace(0.1, 1.0, 15)

V_ratio_surface = np.zeros((len(ethanol_fracs), len(gox_fracs)))
J_surface = np.zeros_like(V_ratio_surface)

for i, eth_frac in enumerate(ethanol_fracs):
    for j, gox_frac in enumerate(gox_fracs):
        params.ethanol_inlet_dP_frac = eth_frac
        params.gox_inlet_dP_frac = gox_frac
        out = calculate_injector_element_geometry(num_elements=1, P=params)
        V_ratio_surface[i, j] = out.V_ratio
        J_surface[i, j] = out.J

E, G = np.meshgrid(gox_fracs, ethanol_fracs)

# --- 3D Velocity Ratio Surface ---
fig = plt.figure(figsize=(10, 6))
ax = fig.add_subplot(121, projection="3d")
surf1 = ax.plot_surface(E, G, V_ratio_surface, cmap="viridis")
ax.set_xlabel("GOX ΔP Fraction")
ax.set_ylabel("Ethanol ΔP Fraction")
ax.set_zlabel("Velocity Ratio (GOX/Ethanol)")
ax.set_title("Velocity Ratio Surface")
fig.colorbar(surf1, ax=ax, shrink=0.5, aspect=10)

# --- 3D Momentum Ratio Surface ---
ax2 = fig.add_subplot(122, projection="3d")
surf2 = ax2.plot_surface(E, G, J_surface, cmap="plasma")
ax2.set_xlabel("GOX ΔP Fraction")
ax2.set_ylabel("Ethanol ΔP Fraction")
ax2.set_zlabel("Momentum Ratio (J)")
ax2.set_title("Momentum Ratio Surface")
fig.colorbar(surf2, ax=ax2, shrink=0.5, aspect=10)

plt.tight_layout()
plt.show()
