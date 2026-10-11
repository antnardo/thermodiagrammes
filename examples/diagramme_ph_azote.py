"""Diagramme (P, h) de l'azote, côté vapeur, avec deux points A et B.

D'après J.-J. Fleck (lycée Kléber), modifié par A. Marchand. Les valeurs sont
en bar, kJ/kg, °C et kJ/K/kg.
"""

import matplotlib.pyplot as plt
import numpy as np

from thermodiagrammes import PH

diagramme = PH("R728", label="R728 (azote)", hlim=(75, 400), plim=(1, 40))

val_T = np.arange(-180, 80, 20)  # °C
val_x = np.linspace(0.1, 0.9, 9)
val_s = np.arange(2.5, 7.5, 0.1)  # kJ/K/kg

diagramme.cree(figsize=(8, 6.5))
diagramme.ax.set_xticks(np.arange(80, 401, 10), minor=True)
diagramme.saturation()
diagramme.trace_isos("T", val_T, etiquettes=range(2, len(val_T), 4), position=0.6)
diagramme.trace_isos("S", val_s, etiquettes=range(2, len(val_s), 4), position=0.8, chiffres=1)
diagramme.trace_isos("Q", val_x, etiquettes=[4], position=0.1, chiffres=1)
diagramme.ajoute_point(350, 20, "A")
diagramme.ajoute_point(150, 4, "B")

plt.tight_layout()
diagramme.enregistre("Diagramme_Ph_coolprop_R728.pdf")
