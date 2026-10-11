"""Diagramme de phases (P, T) de l'eau avec la classe ``PT``.

``saturation`` trace la courbe de vaporisation (du point triple T au point critique
C), la courbe de fusion (loi de CoolProp : glaces I à VII) et la courbe de
sublimation, que CoolProp ne connaît pas : elle suit Clausius-Clapeyron depuis le
point triple avec l'enthalpie de sublimation L_vap(T_t) + L_fusion, d'où l'argument
``L_fusion`` (333,5 kJ/kg pour l'eau, dans l'unité de h du diagramme).

Comme les autres diagrammes, ``PT`` accepte les isolignes (ici des isochores, qui
montrent que la vapeur se dilate et que le liquide ne bouge presque pas), les états
par deux grandeurs (``etat``, ``coordonnees``) et les transformations
(``trace_chemin``) : le chauffage isobare de 25 à 200 °C sous 1 bar traverse la
courbe de vaporisation.

D'après un exemple de la documentation de CoolProp. L'ancien script calculait la
courbe de fusion du CO₂ avec les constantes de l'eau et ajoutait à la main la
glace VI, que la loi de fusion de CoolProp couvre déjà.
"""

import matplotlib.pyplot as plt

from pyphysique.thermo import PT

diagramme = PT("Water", L_fusion=333.5, Tlim=(-60, 700), plim=(1e-4, 1e4))
ax = diagramme.cree(figsize=(8, 6))
diagramme.saturation()
diagramme.trace_isos("V", [1e-3, 1e-2, 1e-1, 1, 10], position=0.7, unite=False)

ambiant = diagramme.etat(T=25, P=1)
print(f"Eau à 25 °C sous 1 bar : v = {ambiant.v:.4g} m³/kg, s = {ambiant.s:.3f} kJ/K/kg")
print(f"Point triple : {diagramme.point_triple}, point critique : {diagramme.point_critique}")

depart, arrivee = diagramme.coordonnees(T=25, P=1), diagramme.coordonnees(T=200, P=1)
diagramme.trace_chemin(depart, arrivee, "P")
diagramme.ajoute_point(*depart, "A", angle=90)
diagramme.ajoute_point(*arrivee, "B", angle=90)

ax.text(-40, 1e2, "solide", ha="center")
ax.text(150, 1e2, "liquide", ha="center")
ax.text(300, 1e-2, "vapeur", ha="center")
ax.text(500, 1e3, "fluide supercritique", ha="center")
diagramme.enregistre()  # Diagramme_PT_coolprop_Water.pdf
plt.show()
