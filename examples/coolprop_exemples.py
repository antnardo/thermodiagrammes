"""Tour d'horizon de CoolProp : interface haut niveau, air humide, fluides
incompressibles, interface bas niveau et tracé de base.

Exemple généré à l'origine par le script ``example_generator.py`` d'Ian Bell
(CoolProp), adapté à CoolProp 6 et plus : ``CoolProp.Plots.PropsPlot`` n'existe
plus, remplacé par ``PropertyPlot``.
<https://coolprop.org/coolprop/HighLevelAPI.html#table-of-string-inputs-to-propssi-function>
"""

import CoolProp
from CoolProp.CoolProp import PhaseSI, PropsSI, get_global_param_string
from CoolProp.HumidAirProp import HAPropsSI
from CoolProp.Plots import PropertyPlot

print("**************** INFORMATIONS ***************")
print("Version de CoolProp :", get_global_param_string("version"))
print("Révision git :", get_global_param_string("gitrevision"))
print("Fluides :", get_global_param_string("FluidsList"))

print("*********** INTERFACE HAUT NIVEAU *****************")
print("Température critique de l'eau :", PropsSI("Water", "Tcrit"), "K")
print("Ébullition de l'eau sous 101325 Pa :", PropsSI("T", "P", 101325, "Q", 0, "Water"), "K")
print("Phase de l'eau à 101325 Pa et 300 K :", PhaseSI("P", 101325, "T", 300, "Water"))
print("c_p de l'eau à 101325 Pa et 300 K :", PropsSI("C", "P", 101325, "T", 300, "Water"), "J/kg/K")
print(
    "c_p de l'eau (par dérivée) à 101325 Pa et 300 K :",
    PropsSI("d(H)/d(T)|P", "P", 101325, "T", 300, "Water"),
    "J/kg/K",
)

print("*********** AIR HUMIDE *****************")
W = HAPropsSI("W", "T", 300, "P", 101325, "R", 0.5)
print(
    "Humidité absolue de l'air à 50 % d'humidité relative, 300 K, 101325 Pa :",
    W,
    "kg_eau/kg_air_sec",
)
print("Humidité relative recalculée :", HAPropsSI("R", "T", 300, "P", 101325, "W", W))

print("*********** FLUIDES INCOMPRESSIBLES ET SAUMURES *****************")
print(
    "Masse volumique d'un mélange eau/éthylène glycol à 50 % (en masse), 300 K, 101325 Pa :",
    PropsSI("D", "T", 300, "P", 101325, "INCOMP::MEG-50%"),
    "kg/m³",
)
print(
    "Viscosité du Therminol D12 à 350 K, 101325 Pa :",
    PropsSI("V", "T", 350, "P", 101325, "INCOMP::TD12"),
    "Pa·s",
)

print("*********** DÉRIVÉE SUR LA SATURATION (INTERFACE BAS NIVEAU) ***************")
AS_SAT = CoolProp.AbstractState("HEOS", "R245fa")
AS_SAT.update(CoolProp.PQ_INPUTS, 101325, 0)
print(
    "dP/dT sur la courbe de saturation :",
    AS_SAT.first_saturation_deriv(CoolProp.iP, CoolProp.iT),
    "Pa/K",
)

print("*********** INTERFACE BAS NIVEAU : MÉLANGE *****************")
AS = CoolProp.AbstractState("HEOS", "Water&Ethanol")
AS.set_mole_fractions([0.5, 0.5])
AS.update(CoolProp.PQ_INPUTS, 101325, 1)
print("Température de rosée du mélange équimolaire eau/éthanol sous 1 atm :", AS.T(), "K")

# Le volume massique (m³/kg) est l'inverse de la masse volumique (kg/m³), ici sous 1 bar.
fluide = "Water"
vL = 1 / PropsSI("D", "P", 1e5, "Q", 0, fluide)  # liquide saturant
vG = 1 / PropsSI("D", "P", 1e5, "Q", 1, fluide)  # vapeur saturante
print(f"Sous 1 bar : v_liquide = {vL:.4g} m³/kg, v_vapeur = {vG:.4g} m³/kg")

# Tracé de base de CoolProp ; pour des diagrammes étiquetés, voir thermodiagrammes.PH.
diagramme = PropertyPlot(fluide, "PH", unit_system="KSI")
diagramme.calc_isolines()
diagramme.savefig("coolprop_exemples.pdf")
