"""Propriétés d'un fluide réel calculées par CoolProp, en unités SI.

``Fluide`` enrobe ``CoolProp.PropsSI`` pour trois raisons :

- les arguments nommés (``fluide.H(P=1e5, T=300)``) sont plus lisibles que la
  liste positionnelle ``PropsSI("H", "P", 1e5, "T", 300, "Water")`` ;
- un état hors du domaine du modèle donne ``nan`` au lieu d'une exception (un
  scalaire) ou d'un ``inf`` (un tableau) : les courbes s'interrompent
  simplement là où le fluide n'est plus décrit (solide, au-delà de pmax…) ;
- le volume massique ``V`` est traité comme l'inverse de ``D``, la masse
  volumique, que CoolProp seul connaît.

Les noms de grandeurs sont ceux de CoolProp : T, P, Q (titre en vapeur), H, S,
U, D, C (c_p), O (c_v), A (vitesse du son), L (conductivité), V (viscosité chez
CoolProp, mais volume massique ici)…
<https://coolprop.org/coolprop/HighLevelAPI.html#parameter-table>.
"""

from contextlib import suppress
from typing import Any

import numpy as np
import numpy.typing as npt

try:
    from CoolProp import CoolProp as CP
except ModuleNotFoundError as erreur:
    raise ImportError("CoolProp manque : pip install CoolProp") from erreur

__all__ = ["Fluide"]

# float pour des entrées scalaires, np.ndarray sinon ; Any évite à l'appelant des
# vérifications de type que numpy rend illisibles.
Valeur = Any


class Fluide:
    """Un fluide pur de CoolProp et ses points remarquables (unités SI).

    Points remarquables : ``Ttriple``, ``Ptriple``, ``Tcrit``, ``Pcrit``, ``rhocrit``,
    limites du modèle ``Tmax``, ``Pmax`` ; masse molaire ``M`` (kg/mol) et constante
    massique ``r`` = R/M (J/K/kg).

    Toute grandeur se calcule à partir de deux autres (``prop``), dans les deux sens :
    ``H(T=300, P=1e5)`` comme ``T(H=112_654, P=1e5)``, ``Psat(T)`` comme ``Tsat(P)``,
    ``Tfus(P)`` comme ``Pfus(T)``.
    """

    def __init__(self, nom: str, moteur: str = "HEOS") -> None:
        try:
            self.nom = CP.get_fluid_param_string(nom, "name")
        except ValueError as erreur:
            raise ValueError(
                f"Fluide {nom!r} inconnu de CoolProp ; voir CP.FluidsList()."
            ) from erreur
        self.moteur = moteur
        self.etat = CP.AbstractState(moteur, self.nom)
        self.Ttriple: float = CP.PropsSI("Ttriple", self.nom)
        self.Ptriple: float = CP.PropsSI("ptriple", self.nom)
        self.Tcrit: float = CP.PropsSI("Tcrit", self.nom)
        self.Pcrit: float = CP.PropsSI("pcrit", self.nom)
        self.rhocrit: float = CP.PropsSI("rhocrit", self.nom)
        self.Tmax: float = CP.PropsSI("Tmax", self.nom)  # limite haute du modèle
        self.Pmax: float = CP.PropsSI("pmax", self.nom)
        self.M: float = CP.PropsSI("molemass", self.nom)  # masse molaire, kg/mol
        self.r: float = CP.PropsSI("gas_constant", self.nom) / self.M  # R/M, J/K/kg

    def __repr__(self) -> str:
        return f"Fluide({self.nom!r})"

    # --- propriétés ----------------------------------------------------------------

    def prop(self, sortie: str, **entrees: npt.ArrayLike) -> Valeur:
        """Grandeur ``sortie`` dans l'état fixé par deux grandeurs nommées.

        Une des entrées (ou les deux, de même taille) peut être un tableau.
        ``V`` (volume massique) est accepté en entrée comme en sortie.
        """
        if len(entrees) != 2:
            raise ValueError(f"Il faut exactement deux grandeurs d'entrée (reçu {list(entrees)}).")
        (k1, v1), (k2, v2) = entrees.items()
        k1, v1 = self._masse_volumique(k1, v1)
        k2, v2 = self._masse_volumique(k2, v2)
        cle = "D" if sortie == "V" else sortie
        for nom in (cle, k1, k2):
            CP.get_parameter_index(nom)  # ValueError explicite si la grandeur n'existe pas
        scalaire = np.ndim(v1) == 0 and np.ndim(v2) == 0
        a1, a2 = np.broadcast_arrays(
            np.atleast_1d(np.asarray(v1, float)), np.atleast_1d(np.asarray(v2, float))
        )
        try:
            resultat = np.asarray(CP.PropsSI(cle, k1, a1, k2, a2, self.nom), float)
        except ValueError:
            # CoolProp lève une exception pour un état invalide unique (y compris dans
            # un tableau d'un seul élément) : on reprend point par point.
            resultat = np.array(
                [self._propsSI(cle, k1, x1, k2, x2) for x1, x2 in zip(a1, a2, strict=True)]
            )
        resultat[~np.isfinite(resultat)] = np.nan
        if sortie == "V":
            resultat = 1 / resultat
        return float(resultat[0]) if scalaire else resultat

    def _propsSI(self, sortie: str, k1: str, v1: float, k2: str, v2: float) -> float:
        try:
            return float(CP.PropsSI(sortie, k1, v1, k2, v2, self.nom))
        except ValueError:
            return np.nan

    @staticmethod
    def _masse_volumique(cle: str, valeur: npt.ArrayLike) -> tuple[str, npt.ArrayLike]:
        if cle == "V":
            return "D", 1 / np.asarray(valeur, float)
        return cle, valeur

    def T(self, **entrees: npt.ArrayLike) -> Valeur:
        return self.prop("T", **entrees)

    def P(self, **entrees: npt.ArrayLike) -> Valeur:
        return self.prop("P", **entrees)

    def Q(self, **entrees: npt.ArrayLike) -> Valeur:
        return self.prop("Q", **entrees)

    def H(self, **entrees: npt.ArrayLike) -> Valeur:
        return self.prop("H", **entrees)

    def S(self, **entrees: npt.ArrayLike) -> Valeur:
        return self.prop("S", **entrees)

    def U(self, **entrees: npt.ArrayLike) -> Valeur:
        return self.prop("U", **entrees)

    def D(self, **entrees: npt.ArrayLike) -> Valeur:
        return self.prop("D", **entrees)

    def V(self, **entrees: npt.ArrayLike) -> Valeur:
        return self.prop("V", **entrees)

    def Psat(self, T: npt.ArrayLike) -> Valeur:
        """Pression de vapeur saturante à la température T (nan hors de [Ttriple, Tcrit])."""
        return self.prop("P", Q=0, T=T)

    def Tsat(self, P: npt.ArrayLike) -> Valeur:
        """Température d'ébullition sous la pression P (nan hors de [Ptriple, Pcrit])."""
        return self.prop("T", Q=0, P=P)

    def L_vap(self, T: npt.ArrayLike) -> Valeur:
        """Enthalpie massique de vaporisation h_vap − h_liq à la température T (J/kg)."""
        return self.prop("H", Q=1, T=T) - self.prop("H", Q=0, T=T)

    def phase(self, **entrees: float) -> str:
        """Nom de la phase (``"liquid"``, ``"gas"``, ``"twophase"``, ``"supercritical"``…)."""
        (k1, v1), (k2, v2) = entrees.items()
        return str(CP.PhaseSI(k1, v1, k2, v2, self.nom))

    def derivee(self, fonction: str, variable: str, constante: str, **entrees: float) -> float:
        """Dérivée partielle (∂fonction/∂variable) à ``constante`` fixée, par exemple
        ``derivee("H", "T", "P", P=1e5, T=300)`` donne c_p."""
        (k1, v1), (k2, v2) = entrees.items()
        return float(
            CP.PropsSI(f"d({fonction})/d({variable})|{constante}", k1, v1, k2, v2, self.nom)
        )

    # --- courbes de changement d'état ------------------------------------------------

    def temperatures_saturation(self, n: int = 200) -> np.ndarray:
        """n températures du point triple au point critique, resserrées près de Tc.

        La courbe de saturation devient verticale au point critique (h_l et h_v s'y
        rejoignent en racine carrée) : un échantillonnage uniforme en T laisse un
        sommet de dôme anguleux. Le point critique lui-même est exclu, CoolProp
        refusant Q fixé à T = Tc.
        """
        u = np.linspace(0, 1, n + 1)[:-1]
        return self.Ttriple + (self.Tcrit - self.Ttriple) * (1 - (1 - u) ** 3)

    def courbe_saturation(self, n: int = 200) -> tuple[np.ndarray, np.ndarray]:
        """(T, Psat) du point triple au point critique (inclus)."""
        T = np.append(self.temperatures_saturation(n), self.Tcrit)
        P = np.append(self.Psat(T[:-1]), self.Pcrit)
        return T, P

    def courbe_fusion(self, n: int = 200) -> tuple[np.ndarray, np.ndarray]:
        """(Tfus, P) sur tout le domaine de la loi de fusion de CoolProp."""
        if not self.etat.has_melting_line():
            raise ValueError(f"CoolProp ne donne pas de courbe de fusion pour {self.nom}.")
        P_min = self.etat.melting_line(CP.iP_min, CP.iT, 0)
        P_max = self.etat.melting_line(CP.iP_max, CP.iT, 0)
        P = np.geomspace(P_min, P_max, n)
        return self.Tfus(P), P

    def Tfus(self, P: npt.ArrayLike) -> Valeur:
        """Température de fusion sous la pression P (nan hors du domaine connu)."""
        return self._fusion(CP.iT, CP.iP, P)

    def Pfus(self, T: npt.ArrayLike) -> Valeur:
        """Pression de fusion à la température T (nan hors du domaine connu)."""
        return self._fusion(CP.iP, CP.iT, T)

    def _fusion(self, sortie: int, entree: int, valeurs: npt.ArrayLike) -> Valeur:
        if not self.etat.has_melting_line():
            raise ValueError(f"CoolProp ne donne pas de courbe de fusion pour {self.nom}.")
        tableau = np.atleast_1d(np.asarray(valeurs, float))
        resultat = np.full(tableau.shape, np.nan)
        for i, valeur in enumerate(tableau):
            with suppress(ValueError):  # hors du domaine de la loi de fusion : nan
                resultat[i] = self.etat.melting_line(sortie, entree, valeur)
        return float(resultat[0]) if np.ndim(valeurs) == 0 else resultat
