"""Diagramme (T, s) de l'eau : isobares, isotitres et isenthalpes.

D'après J.-J. Fleck (lycée Kléber), modifié par A. Marchand. Les isobares
s'arrêtent à la pression maximale du modèle de l'eau (1 GPa) : l'ancien script
les poussait jusqu'à 5 GPa. Valeurs en °C, bar, kJ/kg et kJ/K/kg.
"""

import matplotlib.pyplot as plt
import numpy as np

from thermodiagrammes import TS

diagramme = TS("Water", label="Water", slim=(0, 10.1), Tlim=(1, 440))

val_P, _ = diagramme.valeurs_auto_P(par_decade=(1, 2, 5))  # bar, jusqu'à 10 000 bar
val_P = np.sort(np.append(val_P[val_P >= 0.01], 7))
val_x = np.linspace(0.1, 0.9, 9)
val_h = [192, 417, 697, 1213, 1700, 2124, 2398, 2674, 2756, 2763]  # kJ/kg

diagramme.cree(figsize=(15, 10))
diagramme.saturation()
diagramme.trace_isos("P", val_P, position=0.9, linestyle="-.")
diagramme.trace_isos("Q", val_x, etiquettes=range(1, len(val_x), 2), position=0.05, chiffres=1)
diagramme.trace_isos("H", val_h, position=0.01)

plt.tight_layout()
diagramme.enregistre()  # Diagramme_Ts_coolprop_Water.pdf
