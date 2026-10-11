"""Isothermes d'Andrews de l'eau dans le diagramme (P, v), pour le cours.

D'après J.-J. Fleck (lycée Kléber). Trois figures : le diagramme par défaut,
puis la fenêtre du cours sans et avec la courbe de saturation, dans deux
fichiers distincts (l'ancien script écrasait la première par la seconde).
"""

import matplotlib.pyplot as plt
import numpy as np

from thermodiagrammes import PV, Fluide, Unites

plt.rcParams.update({"text.usetex": True, "font.family": "serif", "font.size": 10})


def isothermes_d_andrews(
    fluide, T=None, vlim=None, plim=None, fichier="pv-eau.pdf", legende=True, saturation=False
):
    """Isothermes (T en K) d'Andrews de ``fluide`` dans la fenêtre vlim (m³/kg), plim (Pa).

    Par défaut : du point triple à 1,2·Tc par pas de 20 K, v entre le liquide au point
    triple et 10 fois la vapeur au point triple.
    """
    f = Fluide(fluide)
    if T is None:
        T = np.arange(f.Ttriple, 1.2 * f.Tcrit, 20)
    vlim = vlim or (f.V(T=f.Ttriple, Q=0), 10 * f.V(T=f.Ttriple, Q=1))
    diagramme = PV(f, unites=Unites(P="Pa", T="kelvin"), vlim=vlim, plim=plim, titre="")
    diagramme.cree(figsize=(8, 4))
    for Ti in T:
        diagramme.trace_isos("T", [Ti], etiquettes=[], color="red", label=f"$T={Ti:.0f}$")
    if saturation:
        diagramme.saturation(linewidth=2)
    if legende:
        diagramme.ax.legend()
    diagramme.ax.set_xlabel(r"$v$ (m$^3\,\cdot\,$kg$^{-1}$)")
    diagramme.ax.set_ylabel("$P$ (Pa)")
    diagramme.ax.grid(color=".5", which="major", linestyle="-", linewidth=0.5)
    diagramme.ax.grid(color=".75", which="minor", linestyle="-", linewidth=0.25)
    diagramme.enregistre(fichier, bbox_inches="tight", pad_inches=0)
    plt.close(diagramme.fig)


# Le fluide à étudier, parmi CoolProp.CoolProp.FluidsList()
FLUIDE = "Water"

isothermes_d_andrews(FLUIDE)  # le diagramme « par défaut »

# Fenêtre choisie après observation du diagramme par défaut (à adapter à un autre fluide)
cours = {
    "plim": (1e4, 5e7),
    "vlim": (5e-4, 3e1),
    "T": [293 + 40 * i for i in range(13)],
    "legende": False,
}
isothermes_d_andrews(FLUIDE, fichier="14_diagrammes_fig-Pv-eau.pdf", **cours)
isothermes_d_andrews(
    FLUIDE, fichier="14_diagrammes_fig-Pv-eau-saturation.pdf", saturation=True, **cours
)
