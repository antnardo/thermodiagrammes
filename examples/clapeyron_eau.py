"""Diagramme de Clapeyron (P, v) de l'eau : isothermes, isotitres, isenthalpes, isentropes.

D'après C. Cayssiols (2017). Rappel de la syntaxe de CoolProp :
``PropsSI("grandeur voulue", "param 1", valeur 1, "param 2", valeur 2, "fluide")``
avec T, P, D (masse volumique), Q (titre en vapeur), H, S…
<https://coolprop.org/coolprop/HighLevelAPI.html>. Ici, ``thermodiagrammes.PV``
s'en charge ; la saturation est échantillonnée en température, et non plus en
pression à partir de 0,1 bar.
"""

import matplotlib.pyplot as plt

from thermodiagrammes import PV, Unites

diagramme = PV(
    "Water",
    unites=Unites(P="bar", H="kJ", S="kJ", T="celsius"),
    vlim=(1e-4, 12),  # m³/kg
    plim=(1e-1, 1e3),  # bar
    titre="Diagramme de Clapeyron",
)
f = diagramme.fluide
Tc = f.Tcrit - 273.15  # °C
h_c = f.H(T=f.Tcrit, D=f.rhocrit) / 1e3  # kJ/kg, point critique
s_c = f.S(T=f.Tcrit, D=f.rhocrit) / 1e3  # kJ/K/kg

# Isothermes d'Andrews : 100 °C, Tc et 2·Tc (en kelvins)
T = [100, Tc, 2 * (Tc + 273.15) - 273.15]
x_vap = [0.25, 0.5, 0.75]
# Isenthalpes et isentropes passant par le liquide saturant à 100 °C, à 10 bar et au point critique
h = [f.H(T=373.15, Q=0) / 1e3, f.H(P=10e5, Q=0) / 1e3, h_c]
s = [f.S(T=373.15, Q=0) / 1e3, f.S(P=10e5, Q=0) / 1e3, s_c]

diagramme.cree()
diagramme.saturation(linewidth=1)[0].set_label("Courbe de saturation")
for grandeur, valeurs, couleur in (
    ("T", T, "red"),
    ("Q", x_vap, "gray"),
    ("H", h, "blue"),
    ("S", s, "green"),
):
    lignes = diagramme.trace_isos(grandeur, valeurs, etiquettes=[], color=couleur, n=400)
    lignes[0].set_label(f"iso-{grandeur.lower() if grandeur != 'Q' else 'x'}")
diagramme.ax.set_xlabel("$v$ (m$^3$/kg)")
diagramme.ax.set_ylabel("$p$ (bar)")
diagramme.ax.legend()
plt.show()
