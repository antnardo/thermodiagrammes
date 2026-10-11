"""Diagramme de Mollier (h, s) de l'eau, autour de la courbe de rosée.

D'après C. Cayssiols (2017). La saturation est calculée du point triple au point
critique (l'ancien script allait de 273 à 973 K : 47 % des points au-dessus de
Tc) ; ``matplotlib2tikz``, abandonné, est remplacé par un PDF.
"""

import matplotlib.pyplot as plt

from thermodiagrammes import HS, Fluide, Unites

f = Fluide("Water")
s_c = f.S(T=f.Tcrit, D=f.rhocrit) / 1e3  # kJ/K/kg, point critique
unites = Unites(P="bar", H="kJ", S="kJ", T="kelvin")
diagramme = HS(f, unites=unites, slim=(s_c, 11), hlim=(1800, 4000), titre="Diagramme de Mollier")

x_vap = [0.25, 0.5, 0.75]
T = [f.Tcrit, 2 * f.Tcrit, 373]  # K
P = [1, f.Pcrit / 1e5, 1e-2]  # bar

diagramme.cree()
for grandeur, valeurs, couleur, nom in (
    ("Q", x_vap, "gray", "iso-x"),
    ("T", T, "red", "iso-T"),
    ("P", P, "orange", "iso-P"),
):
    lignes = diagramme.trace_isos(grandeur, valeurs, etiquettes=[], color=couleur)
    lignes[0].set_label(nom)
diagramme.saturation()[0].set_label("Courbe de saturation")
diagramme.ax.legend()
plt.savefig("08_diagrammes_fig-mollier_eau.pdf")
plt.show()
