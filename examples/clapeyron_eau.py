"""Diagramme de Clapeyron (P, v) de l'eau : isothermes, isotitres, isenthalpes, isentropes.

D'après C. Cayssiols (2017). Rappel de la syntaxe de CoolProp :
``PropsSI("grandeur voulue", "param 1", valeur 1, "param 2", valeur 2, "fluide")``
avec T, P, D (masse volumique), Q (titre en vapeur), H, S…
<https://coolprop.org/coolprop/HighLevelAPI.html>. Ici, ``thermodiagrammes.PV``
s'en charge ; la saturation est échantillonnée en température, et non plus en
pression à partir de 0,1 bar.

Les unités : ``Fluide`` (``diagramme.fluide``) parle en SI, le diagramme dans ses
unités d'affichage (ici bar, kJ/kg, kJ/K/kg, °C). On passe de l'un à l'autre par
``etat`` (deux grandeurs en unités d'affichage → un ``Etat`` complet), par
``etat_critique`` et ``etat_triple``, et par ``celsius`` / ``kelvin`` pour une
température ; jamais par un ``- 273.15`` ou un ``/ 1e3`` à la main.
"""

import matplotlib.pyplot as plt

from thermodiagrammes import PV, Unites, celsius

diagramme = PV(
    "Water",
    unites=Unites(P="bar", H="kJ", S="kJ", T="celsius"),
    vlim=(1e-4, 12),  # m³/kg
    plim=(1e-1, 1e3),  # bar
    titre="Diagramme de Clapeyron",
)
Tc = diagramme.fluide.Tcrit  # K, comme tout ce que donne Fluide
critique = diagramme.etat_critique()  # °C, bar, kJ/kg, kJ/K/kg : les unités du diagramme

# Isothermes d'Andrews : 100 °C, Tc et 2·Tc
T = [100, celsius(Tc), celsius(2 * Tc)]
x_vap = [0.25, 0.5, 0.75]
# Isenthalpes et isentropes passant par le liquide saturant à 100 °C, à 10 bar et au point critique
a, b = diagramme.etat(T=100, Q=0), diagramme.etat(P=10, Q=0)
h = [a.h, b.h, critique.h]
s = [a.s, b.s, critique.s]

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
diagramme.enregistre("clapeyron_eau.pdf")
plt.show()
