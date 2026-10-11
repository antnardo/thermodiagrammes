"""Diagramme des frigoristes de l'eau, de 0,4 à 500 bar et de 0 à 5000 kJ/kg.

D'après J.-J. Fleck (lycée Kléber), modifié par Y. Alméras puis A. Marchand.
L'ancien script reposait sur ``CoolProp.Plots.PropsPlot`` (CoolProp 5) et
mélangeait Pa et kPa, J et kJ : tout est maintenant en bar, kJ/kg, K, kJ/K/kg
et m³/kg.
"""

import matplotlib.pyplot as plt
import numpy as np

from pyphysique.thermo import PH
from pyphysique.thermo.diagrammes import Unites

diagramme = PH(
    "Water",
    label="eau",
    unites=Unites(T="kelvin"),
    hlim=(0, 5000),  # kJ/kg
    plim=(0.4, 500),  # bar
    titre="",
)

val_T = np.arange(300, 1500, 50)  # K
val_x = np.linspace(0.1, 0.9, 9)
val_s, _ = diagramme.valeurs_auto_s(pas=0.5, arrondi=0.5)  # kJ/K/kg
val_v = [0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08, 0.09, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6]
val_v += [0.7, 0.8, 0.9, 1, 2, 3, 4, 5, 6, 7, 8, 9]  # m³/kg

diagramme.cree(figsize=(16, 10))
diagramme.saturation()
diagramme.trace_isos("Q", val_x, etiquettes=range(0, len(val_x), 2), position=0.15, chiffres=1)
diagramme.trace_isos("T", val_T, etiquettes=range(2, len(val_T) - 2, 4), position=0.09)
diagramme.trace_isos("S", val_s, etiquettes=range(2, len(val_s) - 6, 2), position=0.88, chiffres=1)
diagramme.trace_isos("V", val_v, etiquettes=[2, 5, 9, 11, 14, 18, 20], position=0.81)
diagramme.ax.set_xlabel("Enthalpie massique (kJ/kg)")
diagramme.ax.set_ylabel("Pression (bar)")

plt.tight_layout()
diagramme.enregistre("DiagrammeWater.png", dpi=200, transparent=True)
