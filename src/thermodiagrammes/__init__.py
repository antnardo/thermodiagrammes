"""Diagrammes thermodynamiques d'un fluide réel, étiquetés, avec leurs cycles.

Diagrammes (P, h) des frigoristes, (T, s) entropique, (h, s) de Mollier, (P, v) de
Clapeyron et de phases (P, T), calculés par CoolProp : courbe de saturation, isolignes
étiquetées, états fixés par deux grandeurs, transformations d'un cycle. Tout ce que
l'on donne ou que l'on lit est dans les unités d'affichage du diagramme (bar, kJ/kg,
°C… au choix), les nombres s'écrivent avec une virgule.

Usage ::

    from thermodiagrammes import PH

    diagramme = PH("R134a", hlim=(150, 500), plim=(0.5, 50))
    diagramme.cree(figsize=(12, 8))
    diagramme.saturation()
    diagramme.trace_isos("T", [-20, 0, 20, 40, 60, 80], position=0.6)
    vapeur = diagramme.etat(T=40, Q=1)  # Etat(T=40.0, P=10.17, h=…, s=…, v=…, x=1.0)
    diagramme.enregistre()  # Diagramme_Ph_coolprop_R134a.pdf

La tête de paquet expose les cinq diagrammes (``PH``, ``TS``, ``HS``, ``PV``, ``PT``),
leur base ``Diagramme``, ``Etat``, ``Unites``, ``celsius``, ``kelvin`` et ``formate_nombre``
(``thermodiagrammes.diagrammes``), et ``Fluide`` (``thermodiagrammes.fluide``), les
propriétés d'un fluide CoolProp en SI.
"""

from thermodiagrammes.diagrammes import (
    HS,
    PH,
    PT,
    PV,
    TS,
    Diagramme,
    Etat,
    Unites,
    celsius,
    formate_nombre,
    kelvin,
)
from thermodiagrammes.fluide import Fluide

__version__ = "0.1.3"

__all__ = [
    "HS",
    "PH",
    "PT",
    "PV",
    "TS",
    "Diagramme",
    "Etat",
    "Fluide",
    "Unites",
    "__version__",
    "celsius",
    "formate_nombre",
    "kelvin",
]
