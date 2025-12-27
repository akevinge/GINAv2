from scipy.constants import bar, psi


def m3_to_gal(m3: float) -> float:
    return m3 * 264.17205234375


def m3_to_scft(m3: float) -> float:
    return m3 * 35.3147


def in2_to_m2(in2: float) -> float:
    return in2 * 0.00064516


def mm2_to_m2(mm2: float) -> float:
    return mm2 * 1e-6


def bar_to_pa(p) -> float:
    return p * bar


def pa_to_bar(p) -> float:
    return p / bar


def bar_to_psi(p) -> float:
    return (p * bar) / psi


def psi_to_pa(p) -> float:
    return p * psi


def pa_to_psi(p) -> float:
    return p / psi


def psi_to_pa(p) -> float:
    return p * psi
