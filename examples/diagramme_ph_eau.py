"""Diagramme (P, h) de l'eau avec toutes les isolignes, valeurs choisies automatiquement.

Antonin Marchand, sur une idée de J.-J. Fleck. Toutes les valeurs (limites,
isolignes, points) sont dans les unités d'affichage : ici bar, MJ/kg, °C,
kJ/K/kg et m³/kg.
"""

import matplotlib.pyplot as plt

from pyphysique.thermo import PH
from pyphysique.thermo.diagrammes import Unites

diagramme = PH(
    "Water",
    label="Eau",
    unites=Unites(P="bar", H="MJ", T="celsius"),
    plim=(0.006, 450),  # bar : du point triple au double de la pression critique
)  # hlim par défaut : le dôme, plus 5 % et 50 % de L au point triple
f = diagramme.fluide
print(f"Pc = {f.Pcrit:g} Pa, Tc = {f.Tcrit:g} K")
print(f"Ptriple = {f.Ptriple:g} Pa, Ttriple = {f.Ttriple:g} K")

val_T, etiq_T = diagramme.valeurs_auto_T(pas=20, arrondi=10, une_sur=4, debut=2)
# ou à la main : val_T = np.arange(-180, 80, 20) ; etiq_T = range(2, len(val_T), 4)
val_x, etiq_x = diagramme.valeurs_auto_x()
val_s, etiq_s = diagramme.valeurs_auto_s(pas=0.5, arrondi=1, une_sur=5, debut=1)
val_v, etiq_v = diagramme.valeurs_auto_v(par_decade=(1, 2, 5))

diagramme.cree(figsize=(16, 8))
diagramme.saturation()
diagramme.trace_isos("Q", val_x, etiquettes=[4], position=0.1, linestyle="--")
diagramme.trace_isos("T", val_T, etiquettes=etiq_T, position=0.6, color="C1")
diagramme.trace_isos("S", val_s, etiquettes=etiq_s, position=0.3, color="C2")
diagramme.trace_isos("V", val_v, etiquettes=etiq_v, position=0.95, color="C3")
# diagramme.ajoute_point(3, 20, "A")  # en MJ/kg et bar

# on peut continuer à travailler sur la figure avec diagramme.ax
plt.tight_layout()
diagramme.enregistre()  # Diagramme_Ph_coolprop_Water.pdf
plt.show()
