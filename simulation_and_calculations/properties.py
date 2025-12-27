"""
Module to calculate fluid properties of using pyfluids.

The default unit system of pyfluids is SI with Celsius and precents (0 to 100):
https://github.com/portyanikhin/PyFluids?tab=readme-ov-file#available-units-systems
"""

from pyfluids import Fluid, FluidsList, Input
from scipy.constants import convert_temperature
from CoolProp import CoolProp

from conversions import psi_to_pa


def _get_gox_properties(p: float, t: float):
    return Fluid(FluidsList.Oxygen, 100).with_state(
        Input.pressure(p),
        Input.temperature(convert_temperature(t, "K", "C")),
    )


def _get_n2_properties(p: float, t: float):
    return Fluid(FluidsList.Nitrogen, 100).with_state(
        Input.pressure(p),
        Input.temperature(convert_temperature(t, "K", "C")),
    )


def _get_eth_properties(p: float, t: float):
    return Fluid(FluidsList.Ethanol, 100).with_state(
        Input.pressure(p),
        Input.temperature(convert_temperature(t, "K", "C")),
    )


def _get_water_properties(p: float, t: float):
    return Fluid(FluidsList.Water, 100).with_state(
        Input.pressure(p),
        Input.temperature(convert_temperature(t, "K", "C")),
    )


def get_gox_density(p: float, t: float) -> float:
    return _get_gox_properties(p, t).density


def get_gox_molar_mass() -> float:
    return _get_gox_properties(
        p=psi_to_pa(14.7),
        t=300,  # Arbitrary for molar mass
    ).molar_mass


def get_n2_density(p: float, t: float) -> float:
    return _get_n2_properties(p, t).density


def get_n2_molar_mass() -> float:
    return _get_n2_properties(
        p=psi_to_pa(14.7),
        t=300,  # Arbitrary for molar mass
    ).molar_mass


def get_eth_density(p: float, t: float) -> float:
    return _get_eth_properties(p, t).density


def get_water_density(p: float, t: float) -> float:
    return _get_water_properties(p, t).density


def get_compressibility_factor_n2(p: float, t: float) -> float:
    """Get compressibility factor for nitrogen using CoolProp.
    Args:
        p (float): Pressure in Pa
        t (float): Temperature in K
    Returns:
        float: Compressibility factor Z
    """
    return CoolProp.PropsSI("Z", "P", p, "T", t, "Nitrogen")


def get_compressibility_factor_o2(p: float, t: float) -> float:
    """Get compressibility factor for oxygen using CoolProp.
    Args:
        p (float): Pressure in Pa
        t (float): Temperature in K
    Returns:
        float: Compressibility factor Z
    """
    return CoolProp.PropsSI("Z", "P", p, "T", t, "Oxygen")
