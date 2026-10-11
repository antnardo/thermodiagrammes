"""Diagrammes simplifiés de l'eau : (T, s) avec isotitres, (P, h) avec isothermes,
(h, s) avec isobares.

D'après J.-J. Fleck (lycée Kléber). Trois figures de 3 × 3 pouces, en LaTeX, peu
d'étiquettes pour rester lisibles à cette taille.
"""

import matplotlib.pyplot as plt
import numpy as np

from thermodiagrammes import HS, PH, TS, Diagramme, Fluide, Unites

plt.rcParams.update({"text.usetex": True, "font.family": "serif", "font.size": 10})

EAU = Fluide("Water")  # parle en SI
UNITES = Unites(P="bar", H="kJ", S="J", T="kelvin")  # les diagrammes parlent dans celles-ci
si = UNITES.depuis_si  # une seule porte entre les deux, aucun facteur à la main
TAILLE = (3, 3)  # pouces


def isobares_courantes() -> np.ndarray:
    """1 et 3 × 10ⁿ bar, de 5 % de la pression triple à 1,1 × la pression critique."""
    p_min, p_max = si("P", 0.05 * EAU.Ptriple), si("P", 1.1 * EAU.Pcrit)
    decades = range(int(np.floor(np.log10(p_min))) + 1, int(np.ceil(np.log10(p_max))))
    return np.array([a * 10.0**b for b in decades for a in (1, 3)])


def finalise(diagramme: Diagramme, fichier: str, xlabel: str, ylabel: str | None) -> None:
    ax = diagramme.ax
    assert ax is not None
    ax.grid(color=".5", which="major", linestyle="-", linewidth=0.5)
    ax.grid(color=".75", which="minor", linestyle="-", linewidth=0.25)
    ax.set_xlabel(xlabel)
    if ylabel is None:
        ax.set_yticks([])
        ax.set_ylabel("")
    else:
        ax.set_ylabel(ylabel)
    diagramme.enregistre(fichier, bbox_inches="tight", pad_inches=0)
    plt.close(diagramme.fig)


def ts_isotitres() -> None:
    s_l = si("S", EAU.S(T=EAU.Ttriple + 1, Q=0))
    s_v = si("S", EAU.S(T=EAU.Ttriple + 1, Q=1))
    ts = TS(
        EAU,
        unites=UNITES,
        slim=(0.9 * s_l, 1.1 * s_v),
        Tlim=(si("T", EAU.Ttriple + 1), si("T", 1.5 * EAU.Tcrit)),
        titre="",
    )
    ts.cree(figsize=TAILLE)
    ts.saturation(linewidth=0.8)
    ts.trace_isos(
        "Q", np.linspace(0.1, 0.9, 9), position=0.25, linewidth=0.8, style_etiquette={"fontsize": 6}
    )
    finalise(ts, "diagrammes_simplifies_eau_Ts.pdf", r"$s$ (J/K/kg)", None)


def ph_isothermes() -> None:
    # Isothermes à partir de 300 K : à 273 K on serait sous le point triple.
    T = np.arange(300, si("T", 1.8 * EAU.Tcrit), 50)
    h_l = si("H", EAU.H(P=EAU.Ptriple + 1, Q=0))
    h_v = si("H", EAU.H(P=EAU.Ptriple + 1, Q=1))
    ph = PH(
        EAU,
        unites=UNITES,
        hlim=(0.5 * h_l, 1.7 * h_v),
        plim=(si("P", EAU.Ptriple + 1), si("P", 5 * EAU.Pcrit)),
        titre="",
    )
    ph.cree(figsize=TAILLE)
    ph.saturation(linewidth=2)
    ph.trace_isos(
        "T",
        T,
        etiquettes=range(2, len(T) - 4, 2),
        position=0.8,
        color="red",
        style_etiquette={"fontsize": 6},
    )
    finalise(ph, "diagrammes_simplifies_eau_Ph.pdf", r"$h$ (kJ/kg)", "P (bar)")


def hs_isobares() -> None:
    hs = HS(EAU, unites=UNITES, titre="")
    hs.cree(figsize=TAILLE)
    hs.saturation(linewidth=0.8)
    P = isobares_courantes()
    hs.trace_isos(
        "P",
        P,
        etiquettes=range(5, len(P), 2),
        position=0.6,
        color="darkgreen",
        style_etiquette={"fontsize": 6},
    )
    finalise(hs, "diagrammes_simplifies_eau_hs.pdf", r"$s$ (J/K/kg)", r"$h$ (kJ/kg)")


if __name__ == "__main__":
    ts_isotitres()
    ph_isothermes()
    hs_isobares()
