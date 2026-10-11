"""Diagrammes thermodynamiques d'un fluide réel : (P, h), (T, s), (h, s), (P, v), (P, T).

Reprise complète d'un code de J.-J. Fleck (lycée Kléber), modifié par A. Marchand :
le tracé de base de CoolProp (``PropertyPlot``) se prête mal aux diagrammes
étiquetés que l'on distribue en exercice.

Un seul algorithme sert les quatre diagrammes. Une isoligne Z = z₀ est
paramétrée par une grandeur W telle que le couple (Z, W) soit une entrée de
CoolProp, puis on calcule l'abscisse et l'ordonnée du diagramme en chaque
point :

====== =================== ==================================================
Z      W                   remarque
====== =================== ==================================================
Q      T (Ttriple → Tc)    resserré près du point critique, qui ferme le dôme
T      P (échelle log)     points de saturation insérés : palier exact
P      T                   points de saturation insérés : palier exact
H, S   P (échelle log)
V      T                   couple (D, T)
====== =================== ==================================================

Les plages de T et de P échantillonnées se déduisent des coins de la fenêtre
tracée, pour ne calculer que ce qui se voit. Un point hors du modèle donne
``nan`` et interrompt la courbe sans erreur.

Un cycle se dessine par ses états (``etat`` donne T, P, h, s, v et x à partir
de deux grandeurs, ``coordonnees`` les seules coordonnées du diagramme), et par
les transformations qui les relient (``trace_chemin``) : isobare, isenthalpe,
isentrope, isotherme, isochore, ou simple segment.

Le diagramme de phases ``PT`` ajoute les courbes de fusion (loi de CoolProp) et
de sublimation (Clausius-Clapeyron depuis le point triple, si l'enthalpie de
fusion est donnée), le point triple et le point critique.

Toutes les valeurs fournies par l'utilisateur (limites, isolignes, points) sont
dans les **unités d'affichage** du diagramme (bar, kJ/kg, °C… au choix). Les
nombres s'écrivent avec une virgule décimale sans passer par ``locale`` :
``locale.format`` n'existe plus depuis Python 3.12, et ``setlocale`` à
l'import modifiait tout le programme appelant.
"""

import math
import warnings
from collections.abc import Sequence
from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path
from typing import Any, ClassVar

import matplotlib.pyplot as plt
import numpy as np
import numpy.typing as npt
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
from matplotlib.ticker import (
    AutoLocator,
    AutoMinorLocator,
    FuncFormatter,
    LogLocator,
    NullFormatter,
)

from pyphysique.thermo.fluide import Fluide

__all__ = [
    "HS",
    "PH",
    "PT",
    "PV",
    "TS",
    "Diagramme",
    "Etat",
    "Unites",
    "formate_nombre",
]

TK = 273.15

COULEURS = {
    "T": "darkred",
    "P": "darkcyan",
    "H": "darkgreen",
    "V": "darkblue",
    "S": "darkorange",
    "Q": "black",
}
LETTRES = {"T": "T", "P": "P", "H": "h", "S": "s", "V": "v", "Q": "x"}
NOMS = {
    "T": "Température",
    "P": "Pression",
    "H": "Enthalpie massique",
    "S": "Entropie massique",
    "V": "Volume massique",
}
STYLE_BOITE = {"boxstyle": "round", "facecolor": "white", "edgecolor": "none", "alpha": 0.85}

# Marges par défaut des axes h et s, en fraction de l'écart liquide/vapeur au point
# triple. Additives : l'ancienne marge multiplicative (0,9·h_liq) dépendait de l'état
# de référence arbitraire de CoolProp et coupait le dôme de l'azote, dont h_liq < 0.
_MARGES = {"H": (0.05, 0.5), "S": (0.05, 0.1)}

# Transformation à Z constante : paramètre W qui la parcourt, (Z, W) étant une entrée
# de CoolProp valable jusque dans le dôme, et échantillonnage géométrique ou non de W.
# Une isotherme se paramètre par la masse volumique : le couple (T, P), dégénéré sur le
# palier de vaporisation, ne le traverserait pas.
_PARAMETRES = {
    "P": ("H", False),
    "H": ("P", True),
    "S": ("P", True),
    "T": ("D", True),
    "V": ("T", False),
    "Q": ("T", False),
}

_HORS_MODELE = (
    "hors du modèle de CoolProp : les valeurs sont-elles bien en unités d'affichage "
    "(bar, kJ/kg, °C… selon Unites) et non en SI ?"
)


def formate_nombre(valeur: float, chiffres: int | None = None) -> str:
    """Écrit un nombre avec une virgule décimale (``chiffres`` décimales, ou %g)."""
    texte = f"{valeur:.{chiffres}f}" if chiffres is not None else f"{valeur:g}"
    return texte.replace(".", ",")


def _formateur(valeur: float, _position: int | None = None) -> str:
    """Graduation : 0,05 ou 2000 en clair, 5·10⁷ hors de [10⁻³, 10⁵[."""
    if valeur == 0 or 1e-3 <= abs(valeur) < 1e5:
        return formate_nombre(valeur)
    exposant = math.floor(math.log10(abs(valeur)))
    mantisse = round(valeur / 10**exposant, 6)
    facteur = "" if mantisse == 1 else formate_nombre(mantisse).replace(",", "{,}") + r"\cdot"
    return f"${facteur}10^{{{exposant}}}$"


@dataclass(frozen=True, slots=True)
class Unites:
    """Unités d'affichage : P en Pa, kPa, bar ou MPa ; H en J, kJ ou MJ par kg ;
    S en J ou kJ par K et par kg ; V en m^3 ou L par kg ; T en kelvin ou celsius."""

    P: str = "bar"
    H: str = "kJ"
    S: str = "kJ"
    V: str = "m^3"
    T: str = "celsius"

    _FACTEURS: ClassVar[dict[str, dict[str, float]]] = {
        "P": {"Pa": 1, "kPa": 1e3, "bar": 1e5, "MPa": 1e6},
        "H": {"J": 1, "kJ": 1e3, "MJ": 1e6},
        "S": {"J": 1, "kJ": 1e3},
        "V": {"m^3": 1, "L": 1e-3},
        "T": {"kelvin": 1, "celsius": 1},
        "Q": {"": 1},
    }
    _TEXTES: ClassVar[dict[str, str]] = {
        "P": r"\mathrm{{{}}}",
        "H": r"\mathrm{{{}/kg}}",
        "S": r"\mathrm{{{}/K/kg}}",
        "V": r"\mathrm{{{}/kg}}",
    }

    def __post_init__(self) -> None:
        for grandeur in "PHSVT":
            unite = getattr(self, grandeur)
            if unite not in self._FACTEURS[grandeur]:
                raise ValueError(
                    f"Unité {unite!r} inconnue pour {grandeur} : {list(self._FACTEURS[grandeur])}"
                )

    def _unite(self, grandeur: str) -> str:
        return getattr(self, grandeur) if grandeur != "Q" else ""

    def depuis_si(self, grandeur: str, valeur: npt.ArrayLike) -> Any:
        """Valeur SI → unité d'affichage."""
        tableau = np.asarray(valeur, float)
        if grandeur == "T":
            return tableau - TK if self.T == "celsius" else tableau
        return tableau / self._FACTEURS[grandeur][self._unite(grandeur)]

    def vers_si(self, grandeur: str, valeur: npt.ArrayLike) -> Any:
        """Valeur en unité d'affichage → SI."""
        tableau = np.asarray(valeur, float)
        if grandeur == "T":
            return tableau + TK if self.T == "celsius" else tableau
        return tableau * self._FACTEURS[grandeur][self._unite(grandeur)]

    def texte(self, grandeur: str) -> str:
        """Unité en mathtext (sans les $), compatible avec ``text.usetex``."""
        if grandeur == "T":
            return r"{}^\circ\mathrm{C}" if self.T == "celsius" else r"\mathrm{K}"
        if grandeur == "Q":
            return ""
        unite = getattr(self, grandeur).replace("^3", "^{3}")
        return self._TEXTES[grandeur].format(unite)


@dataclass(frozen=True, slots=True)
class Etat:
    """État d'un fluide dans les unités d'affichage du diagramme qui l'a calculé.

    ``T``, ``P``, ``h``, ``s``, ``v`` : température, pression, enthalpie, entropie et
    volume massiques ; ``x`` : titre en vapeur, ``nan`` hors du dôme de saturation.
    """

    T: float
    P: float
    h: float
    s: float
    v: float
    x: float


class Diagramme:
    """Diagramme (x, y) d'un fluide, x et y parmi T, P, H, S, V.

    Usage ::

        d = PH("Water", label="Eau", plim=(0.01, 300))
        d.cree(figsize=(16, 8))
        d.saturation()
        d.trace_isos("T", np.arange(0, 400, 50), position=0.6)
        d.ajoute_point(2800, 10, "A")
        d.enregistre()

    ``xlim`` et ``ylim`` sont en unités d'affichage ; par défaut, la fenêtre
    entoure le dôme de saturation.
    """

    type_diagramme = "xy"
    titre_diagramme = "Diagramme"

    def __init__(
        self,
        fluide: str | Fluide,
        x: str,
        y: str,
        *,
        label: str | None = None,
        unites: Unites | None = None,
        xlim: tuple[float, float] | None = None,
        ylim: tuple[float, float] | None = None,
        xlog: bool = False,
        ylog: bool = False,
        titre: str | None = None,
    ) -> None:
        for axe in (x, y):
            if axe not in NOMS:
                raise ValueError(f"Axe {axe!r} impossible : choisir parmi {list(NOMS)}.")
        self.fluide = fluide if isinstance(fluide, Fluide) else Fluide(fluide)
        self.x, self.y = x, y
        self.label = label or self.fluide.nom
        self.unites = unites or Unites()
        self.xlog, self.ylog = xlog, ylog
        self.xlim = xlim or self._limites_defaut(x)
        self.ylim = ylim or self._limites_defaut(y)
        self.titre = (
            titre if titre is not None else f"{self.titre_diagramme} pour le fluide {self.label}"
        )
        self.style_boite = dict(STYLE_BOITE)
        self.fig: Figure | None = None
        self.ax: Axes | None = None

    # --- fenêtre et échantillonnage ------------------------------------------------------

    def _limites_defaut(self, grandeur: str) -> tuple[float, float]:
        f = self.fluide
        bornes: tuple[Any, Any]
        if grandeur == "P":
            bornes = (f.Ptriple, 1.5 * f.Pcrit)
        elif grandeur == "T":
            bornes = (f.Ttriple, 1.2 * f.Tcrit)
        elif grandeur == "V":
            bornes = (f.V(T=f.Ttriple, Q=0) / 2, 2 * f.V(T=f.Ttriple, Q=1))
        else:
            liquide, vapeur = f.prop(grandeur, T=f.Ttriple, Q=0), f.prop(grandeur, T=f.Ttriple, Q=1)
            gauche, droite = _MARGES[grandeur]
            ecart = vapeur - liquide
            bornes = (liquide - gauche * ecart, vapeur + droite * ecart)
        bas, haut = self.unites.depuis_si(grandeur, bornes)
        return float(bas), float(haut)

    def _coins(self, sortie: str) -> np.ndarray:
        """Valeurs SI de ``sortie`` aux quatre coins de la fenêtre (nan si hors modèle)."""
        xs = self.unites.vers_si(self.x, self.xlim)
        ys = self.unites.vers_si(self.y, self.ylim)
        if sortie == self.x:
            return np.repeat(xs, 2)
        if sortie == self.y:
            return np.tile(ys, 2)
        X, Y = np.meshgrid(xs, ys)
        return np.asarray(self.fluide.prop(sortie, **{self.x: X.ravel(), self.y: Y.ravel()}))

    def _bornes_echantillonnage(self) -> tuple[tuple[float, float], tuple[float, float]]:
        """Plages de T et de P à parcourir pour couvrir la fenêtre, dans le modèle."""
        f = self.fluide
        T_coins = self._coins("T")
        P_coins = self._coins("P")
        T_haut = np.nanmax(T_coins) if np.isfinite(T_coins).any() else f.Tmax
        P_bas = np.nanmin(P_coins) if np.isfinite(P_coins).any() else f.Ptriple
        P_haut = np.nanmax(P_coins) if np.isfinite(P_coins).any() else f.Pmax
        bornes_T = (f.Ttriple, float(min(f.Tmax, 1.05 * T_haut)))
        bornes_P = (float(max(f.Ptriple, P_bas / 2)), float(min(f.Pmax, 2 * P_haut)))
        return bornes_T, bornes_P

    def _temperatures(self, n: int) -> np.ndarray:
        # Recalculé à chaque isoligne (8 appels à CoolProp) : xlim et ylim restent modifiables.
        return np.linspace(*self._bornes_echantillonnage()[0], n)

    def _pressions(self, n: int) -> np.ndarray:
        return np.geomspace(*self._bornes_echantillonnage()[1], n)

    # --- isolignes -----------------------------------------------------------------------

    def isoligne(self, grandeur: str, valeur: float, n: int = 200) -> tuple[np.ndarray, np.ndarray]:
        """Points (x, y), en unités d'affichage, de l'isoligne ``grandeur = valeur``.

        ``valeur`` est en unité d'affichage (°C, bar, kJ/kg…), ``grandeur`` parmi
        T, P, H, S, V et Q (titre en vapeur). Un avertissement signale une isoligne
        entièrement hors du modèle (que des ``nan``).
        """
        return self._isoligne(grandeur, valeur, n, niveau=3)

    def _isoligne(
        self, grandeur: str, valeur: float, n: int, niveau: int
    ) -> tuple[np.ndarray, np.ndarray]:
        """``isoligne``, l'avertissement visant l'appelant ``niveau`` cadres plus haut."""
        if grandeur not in LETTRES:
            raise ValueError(f"Isoligne {grandeur!r} inconnue : choisir parmi {list(LETTRES)}.")
        z = float(self.unites.vers_si(grandeur, valeur))
        f = self.fluide
        if grandeur == "Q":
            T = f.temperatures_saturation(n)
            x, y = f.prop(self.x, Q=z, T=T), f.prop(self.y, Q=z, T=T)
            critique = {"T": f.Tcrit, "D": f.rhocrit}
            x = np.append(x, f.prop(self.x, **critique))
            y = np.append(y, f.prop(self.y, **critique))
        elif grandeur in ("T", "P"):
            x, y = self._isoligne_avec_palier(grandeur, z, n)
        elif grandeur in ("H", "S"):
            entrees: dict[str, Any] = {grandeur: z, "P": self._pressions(n)}
            x, y = f.prop(self.x, **entrees), f.prop(self.y, **entrees)
        else:  # "V"
            T = self._temperatures(n)
            x, y = f.prop(self.x, D=1 / z, T=T), f.prop(self.y, D=1 / z, T=T)
        if not (np.isfinite(x) & np.isfinite(y)).any():
            warnings.warn(
                f"Isoligne {LETTRES[grandeur]} = {valeur} {_HORS_MODELE}", stacklevel=niveau
            )
        return self.unites.depuis_si(self.x, x), self.unites.depuis_si(self.y, y)

    def _isoligne_avec_palier(self, grandeur: str, z: float, n: int) -> tuple[Any, Any]:
        """Isotherme (parcourue en P croissant) ou isobare (en T croissant), avec les
        deux points de saturation insérés pour tracer le palier diphasique exactement."""
        f = self.fluide
        libre = "P" if grandeur == "T" else "T"
        w = self._pressions(n) if libre == "P" else self._temperatures(n)
        entrees: dict[str, Any] = {grandeur: z, libre: w}
        x, y = f.prop(self.x, **entrees), f.prop(self.y, **entrees)
        dans_le_dome = f.Ttriple < z < f.Tcrit if grandeur == "T" else f.Ptriple < z < f.Pcrit
        if not dans_le_dome:
            return x, y
        w_sat = f.prop(libre, **{grandeur: z, "Q": 0})
        # En P croissant on passe de la vapeur au liquide, en T croissant l'inverse.
        titres = (1, 0) if libre == "P" else (0, 1)
        i = int(np.searchsorted(w, w_sat))
        x_sat = [f.prop(self.x, **{grandeur: z, "Q": q}) for q in titres]
        y_sat = [f.prop(self.y, **{grandeur: z, "Q": q}) for q in titres]
        return np.insert(x, i, x_sat), np.insert(y, i, y_sat)

    def label_iso(
        self, grandeur: str, valeur: float, chiffres: int | None = None, unite: bool = True
    ) -> str:
        """Étiquette « $T=20$ °C » d'une isoligne (valeur en unité d'affichage), avec
        ``chiffres`` décimales, ou au plus court (%g) par défaut ; sans l'unité si
        ``unite`` est faux (« $s=1{,}5$ », l'unité étant donnée dans le titre)."""
        texte = formate_nombre(valeur, chiffres)
        symbole = self.unites.texte(grandeur) if unite else ""
        suffixe = f" ${symbole}$" if symbole else ""
        return f"${LETTRES[grandeur]}={texte.replace(',', '{,}')}${suffixe}"

    # --- tracé ---------------------------------------------------------------------------

    def cree(self, **kwargs: Any) -> Axes:
        """Crée la figure (``kwargs`` passés à ``plt.subplots``) et prépare les axes."""
        self.fig, ax = plt.subplots(**kwargs)
        self.ax = ax
        # L'échelle d'abord : set_xscale remet à zéro localisateurs et formateurs.
        if self.xlog:
            ax.set_xscale("log")
        if self.ylog:
            ax.set_yscale("log")
        ax.set_xlim(*self.xlim)
        ax.set_ylim(*self.ylim)
        for axe, log in ((ax.xaxis, self.xlog), (ax.yaxis, self.ylog)):
            if log:
                axe.set_major_locator(LogLocator(base=10, subs=(1, 2, 5)))
                axe.set_minor_locator(LogLocator(base=10, subs=tuple(range(1, 10))))
                axe.set_minor_formatter(NullFormatter())
            else:
                axe.set_major_locator(AutoLocator())
                axe.set_minor_locator(AutoMinorLocator())
            axe.set_major_formatter(FuncFormatter(_formateur))
        ax.grid(which="major", linewidth=0.6)
        ax.grid(which="minor", linewidth=0.3, alpha=0.5)
        ax.set_xlabel(self._titre_axe(self.x))
        ax.set_ylabel(self._titre_axe(self.y))
        ax.set_title(self.titre)
        return ax

    def _titre_axe(self, grandeur: str) -> str:
        return f"{NOMS[grandeur]} ${LETTRES[grandeur]}$ (en ${self.unites.texte(grandeur)}$)"

    def _axes(self) -> Axes:
        if self.ax is None:
            self.cree()
        assert self.ax is not None
        return self.ax

    def trace_isos(
        self,
        grandeur: str,
        valeurs: Sequence[float] | np.ndarray,
        position: float = 0.5,
        etiquettes: Sequence[int] | None = None,
        n: int = 200,
        chiffres: int | None = None,
        style_etiquette: dict[str, Any] | None = None,
        unite: bool = True,
        **style: Any,
    ) -> list[Line2D]:
        """Trace les isolignes ``grandeur = v`` pour v dans ``valeurs`` (unités d'affichage).

        ``etiquettes`` : indices (dans ``valeurs``) des courbes à étiqueter, toutes par
        défaut ; ``position`` : emplacement de l'étiquette le long de la courbe, entre
        0 et 1 ; ``chiffres`` : décimales de l'étiquette (%g par défaut) ;
        ``style_etiquette`` : options de ``Axes.text`` (``fontsize``…) ; ``unite`` :
        faux pour des étiquettes sans unité ; ``style`` : options de ``Axes.plot``
        (couleur par défaut selon la grandeur).
        """
        if grandeur not in COULEURS:
            raise ValueError(f"Isoligne {grandeur!r} inconnue : choisir parmi {list(COULEURS)}.")
        ax = self._axes()
        style.setdefault("color", COULEURS[grandeur])
        style.setdefault("linewidth", 0.8)
        a_etiqueter = set(range(len(valeurs)) if etiquettes is None else etiquettes)
        lignes = []
        for i, valeur in enumerate(valeurs):
            x, y = self._isoligne(grandeur, valeur, n, niveau=3)
            (ligne,) = ax.plot(x, y, **style)
            lignes.append(ligne)
            if i in a_etiqueter:
                texte = {"color": ligne.get_color(), **(style_etiquette or {})}
                self.place_label(
                    x, y, self.label_iso(grandeur, valeur, chiffres, unite), position, **texte
                )
        return lignes

    def saturation(self, **style: Any) -> list[Line2D]:
        """Courbes d'ébullition et de rosée, en trait épais."""
        style.setdefault("color", "black")
        style.setdefault("linewidth", 1.5)
        return self.trace_isos("Q", [0, 1], etiquettes=[], **style)

    def _visibles(self, x: np.ndarray, y: np.ndarray, marge: float = 0.03) -> np.ndarray:
        """Points à l'intérieur de la fenêtre, à ``marge`` (fraction des axes) des bords."""

        def fraction(v: np.ndarray, lim: tuple[float, float], log: bool) -> np.ndarray:
            with np.errstate(divide="ignore", invalid="ignore"):
                t = np.log10 if log else np.asarray
                return (t(v) - t(lim[0])) / (t(lim[1]) - t(lim[0]))

        fx = fraction(x, self.xlim, self.xlog)
        fy = fraction(y, self.ylim, self.ylog)
        dedans = (marge < fx) & (fx < 1 - marge) & (marge < fy) & (fy < 1 - marge)
        return np.isfinite(fx) & np.isfinite(fy) & dedans

    def place_label(
        self, x: np.ndarray, y: np.ndarray, label: str, position: float = 0.5, **texte: Any
    ) -> None:
        """Étiquette semi-transparente posée sur la courbe, parallèle à elle.

        On vise l'indice ``position·(len − 1)`` ; s'il est hors de la fenêtre, on
        prend le point visible le plus proche, et on renonce si aucun ne l'est. L'angle
        est donné en coordonnées de données avec ``transform_rotates_text`` : matplotlib
        le convertit au moment du dessin, échelle logarithmique et mise en page finale
        comprises.
        """
        ax = self._axes()
        candidats = np.flatnonzero(self._visibles(x, y)[1:-1]) + 1
        if candidats.size == 0:
            return
        cible = position * (len(x) - 1)
        i = int(candidats[np.argmin(np.abs(candidats - cible))])
        dx, dy = x[i + 1] - x[i - 1], y[i + 1] - y[i - 1]
        if not (np.isfinite(dx) and np.isfinite(dy)):
            dx, dy = 1.0, 0.0
        if dx < 0:  # texte lisible de gauche à droite
            dx, dy = -dx, -dy
        texte.setdefault("ha", "center")
        texte.setdefault("va", "center")
        artiste = ax.text(
            x[i],
            y[i],
            label,
            rotation=math.degrees(math.atan2(dy, dx)),
            transform_rotates_text=True,
            rotation_mode="anchor",
            **texte,
        )
        artiste.set_bbox(self.style_boite)

    def ajoute_point(
        self,
        x: float,
        y: float,
        label: str | None = None,
        angle: float = 45,
        distance: float = 8,
        color: str = "black",
    ) -> None:
        """Point (x, y) en unités d'affichage, étiqueté à ``distance`` points typographiques
        dans la direction ``angle`` (en degrés) : le décalage ne dépend pas de l'échelle."""
        ax = self._axes()
        ax.plot([x], [y], "o", color=color)
        if label is not None:
            decalage = (
                distance * math.cos(math.radians(angle)),
                distance * math.sin(math.radians(angle)),
            )
            ax.annotate(
                label,
                (x, y),
                xytext=decalage,
                textcoords="offset points",
                ha="center",
                va="center",
                color=color,
                bbox=self.style_boite,
            )

    # --- états et transformations d'un cycle ---------------------------------------------

    def etat(self, **grandeurs: float) -> Etat:
        """État fixé par deux grandeurs parmi T, P, H, S, V et Q, tout en unités
        d'affichage : ``PH("Water").etat(T=100, Q=1)`` donne la vapeur saturante à
        100 °C, avec ``.P`` en bar, ``.h`` en kJ/kg, ``.s`` en kJ/K/kg, ``.v`` en m³/kg.

        Un état hors du modèle a ses valeurs à ``nan``, avec un avertissement.
        """
        return self._etat(grandeurs, niveau=3)

    def _etat(self, grandeurs: dict[str, float], niveau: int) -> Etat:
        if len(grandeurs) != 2:
            raise ValueError(f"Il faut exactement deux grandeurs (reçu {list(grandeurs)}).")
        for grandeur in grandeurs:
            if grandeur not in LETTRES:
                raise ValueError(f"Grandeur {grandeur!r} inconnue : choisir parmi {list(LETTRES)}.")
        si = {grandeur: self.unites.vers_si(grandeur, v) for grandeur, v in grandeurs.items()}
        valeurs = {}
        for grandeur, champ in LETTRES.items():
            valeur = self.fluide.prop(grandeur, **si)
            if grandeur == "Q" and not 0 <= valeur <= 1:  # CoolProp rend −1 hors du dôme
                valeur = math.nan
            valeurs[champ] = float(self.unites.depuis_si(grandeur, valeur))
        if any(math.isnan(v) for champ, v in valeurs.items() if champ != "x"):
            entrees = ", ".join(f"{LETTRES[g]} = {v}" for g, v in grandeurs.items())
            warnings.warn(f"État ({entrees}) {_HORS_MODELE}", stacklevel=niveau)
        return Etat(**valeurs)

    def coordonnees(self, **grandeurs: float) -> tuple[float, float]:
        """Coordonnées (x, y) de l'état fixé par deux grandeurs parmi T, P, H, S, V et Q,
        tout en unités d'affichage : ``PH("Water").coordonnees(T=100, Q=1)`` donne
        (h, P) de la vapeur saturante à 100 °C. Voir ``etat``."""
        etat = self._etat(grandeurs, niveau=3)
        return getattr(etat, LETTRES[self.x]), getattr(etat, LETTRES[self.y])

    def chemin(
        self,
        depart: tuple[float, float],
        arrivee: tuple[float, float],
        grandeur: str | None = None,
        n: int = 60,
    ) -> tuple[np.ndarray, np.ndarray]:
        """Points (x, y) de la transformation de ``depart`` à ``arrivee`` (coordonnées
        du diagramme, en unités d'affichage) à ``grandeur`` constante : P (isobare), H
        (isenthalpe), S (isentrope), T (isotherme), V (isochore) ou Q (isotitre).

        La grandeur garde sa valeur au départ, et la transformation est parcourue
        jusqu'à l'arrivée en h (isobare), en P (isenthalpe, isentrope), en masse
        volumique (isotherme, palier de vaporisation compris) ou en T (isochore,
        isotitre). Sans ``grandeur``, c'est le segment qui joint les deux points.
        """
        if grandeur is None:
            return np.array([depart[0], arrivee[0]]), np.array([depart[1], arrivee[1]])
        if grandeur not in _PARAMETRES:
            raise ValueError(
                f"Transformation à {grandeur!r} constante inconnue : choisir parmi "
                f"{list(_PARAMETRES)}."
            )
        f = self.fluide
        etats = [
            {self.x: self.unites.vers_si(self.x, x), self.y: self.unites.vers_si(self.y, y)}
            for x, y in (depart, arrivee)
        ]
        z = f.prop(grandeur, **etats[0])
        parametre, geometrique = _PARAMETRES[grandeur]
        debut, fin = (float(f.prop(parametre, **etat)) for etat in etats)
        w = np.geomspace(debut, fin, n) if geometrique else np.linspace(debut, fin, n)
        entrees: dict[str, Any] = {grandeur: z, parametre: w}
        x, y = f.prop(self.x, **entrees), f.prop(self.y, **entrees)
        return self.unites.depuis_si(self.x, x), self.unites.depuis_si(self.y, y)

    def trace_chemin(
        self,
        depart: tuple[float, float],
        arrivee: tuple[float, float],
        grandeur: str | None = None,
        fleche: bool = True,
        n: int = 60,
        **style: Any,
    ) -> Line2D:
        """Trace la transformation de ``depart`` à ``arrivee`` (voir ``chemin``), en
        rouge épais par défaut, avec une flèche en son milieu dans le sens du parcours.

        ``style`` : options de ``Axes.plot`` (``linestyle="--"`` pour une
        transformation de comparaison, par exemple, avec ``fleche=False``).
        """
        ax = self._axes()
        style.setdefault("color", "red")
        style.setdefault("linewidth", 2)
        x, y = self.chemin(depart, arrivee, grandeur, n)
        (ligne,) = ax.plot(x, y, **style)
        if fleche:
            self._fleche(x, y, ligne.get_color())
        return ligne

    def _fleche(self, x: np.ndarray, y: np.ndarray, couleur: Any) -> None:
        """Pointe de flèche au milieu d'un chemin, milieu pris à l'écran : sur un axe
        logarithmique, le milieu des données n'est pas celui que l'on voit."""
        ax = self._axes()
        ecran = ax.transData.transform(np.c_[x, y])
        ecran = ecran[np.isfinite(ecran).all(axis=1)]
        longueur = np.r_[0, np.cumsum(np.hypot(*np.diff(ecran, axis=0).T))]
        if len(ecran) < 2 or longueur[-1] == 0:
            return
        queue, pointe = (
            [np.interp(fraction * longueur[-1], longueur, ecran[:, k]) for k in (0, 1)]
            for fraction in (0.47, 0.53)
        )
        queue, pointe = ax.transData.inverted().transform([queue, pointe])
        ax.annotate(
            "",
            xy=tuple(pointe),
            xytext=tuple(queue),
            arrowprops={
                "arrowstyle": "-|>",
                "color": couleur,
                "linewidth": 0,
                "mutation_scale": 16,
                "shrinkA": 0,
                "shrinkB": 0,
            },
        )

    def enregistre(self, chemin: str | Path | None = None, **kwargs: Any) -> Path:
        """Enregistre la figure (``Diagramme_<type>_coolprop_<fluide>.pdf`` par défaut)."""
        assert self.fig is not None, "Créez d'abord la figure (cree)."
        fichier = Path(chemin or f"Diagramme_{self.type_diagramme}_coolprop_{self.fluide.nom}.pdf")
        self.fig.savefig(fichier, **kwargs)
        return fichier

    # --- valeurs automatiques des isolignes ---------------------------------------------

    @staticmethod
    def _une_sur(nombre: int, une_sur: int, debut: int) -> list[int]:
        return list(range(debut, nombre, une_sur))

    @staticmethod
    def _arrondi_superieur(valeur: float, pas: float) -> float:
        return math.ceil(valeur / pas - 1e-9) * pas

    def valeurs_auto_T(
        self, pas: float, arrondi: float = 10, une_sur: int = 5, debut: int = 0
    ) -> tuple[np.ndarray, list[int]]:
        """Isothermes du point triple (arrondi au-dessus) à 1,5·Tc, et indices à étiqueter."""
        T_min = self._arrondi_superieur(
            float(self.unites.depuis_si("T", self.fluide.Ttriple)), arrondi
        )
        T_max = float(self.unites.depuis_si("T", 1.5 * self.fluide.Tcrit))
        valeurs = np.arange(T_min, T_max, pas)
        return valeurs, self._une_sur(len(valeurs), une_sur, debut)

    def valeurs_auto_x(
        self, pas: float = 0.1, une_sur: int = 1, debut: int = 0
    ) -> tuple[np.ndarray, list[int]]:
        """Isotitres de ``pas`` à 1 − ``pas``."""
        valeurs = np.round(np.arange(pas, 1 - pas / 2, pas), 10)
        return valeurs, self._une_sur(len(valeurs), une_sur, debut)

    def _valeurs_auto_triple(
        self, grandeur: str, pas: float, arrondi: float, une_sur: int, debut: int, etendue: float
    ) -> tuple[np.ndarray, list[int]]:
        f = self.fluide
        liquide = float(self.unites.depuis_si(grandeur, f.prop(grandeur, T=f.Ttriple, Q=0)))
        vapeur = float(self.unites.depuis_si(grandeur, f.prop(grandeur, T=f.Ttriple, Q=1)))
        debut_valeurs = self._arrondi_superieur(liquide, arrondi)
        valeurs = np.arange(debut_valeurs, vapeur + etendue * (vapeur - liquide), pas)
        return valeurs, self._une_sur(len(valeurs), une_sur, debut)

    def valeurs_auto_s(
        self, pas: float, arrondi: float = 0.1, une_sur: int = 1, debut: int = 0
    ) -> tuple[np.ndarray, list[int]]:
        """Isentropes de s_liq au point triple (arrondie au-dessus) à s_vap + 20 % de l'écart."""
        return self._valeurs_auto_triple("S", pas, arrondi, une_sur, debut, 0.2)

    def valeurs_auto_h(
        self, pas: float, arrondi: float = 100, une_sur: int = 1, debut: int = 0
    ) -> tuple[np.ndarray, list[int]]:
        """Isenthalpes de h_liq au point triple (arrondie au-dessus) à h_vap + 50 % de l'écart."""
        return self._valeurs_auto_triple("H", pas, arrondi, une_sur, debut, 0.5)

    def valeurs_auto_v(
        self, par_decade: Sequence[float] = (1, 2, 5), une_sur: int = 1, debut: int = 0
    ) -> tuple[np.ndarray, list[int]]:
        """Isochores m·10ⁿ (m dans ``par_decade``) entre v critique et v vapeur au point triple."""
        f = self.fluide
        v_min = float(self.unites.depuis_si("V", 1 / f.rhocrit))
        v_max = float(self.unites.depuis_si("V", f.V(T=f.Ttriple, Q=1)))
        return self._valeurs_decades(v_min, v_max, par_decade, une_sur, debut)

    def valeurs_auto_P(
        self, par_decade: Sequence[float] = (1, 2, 5), une_sur: int = 1, debut: int = 0
    ) -> tuple[np.ndarray, list[int]]:
        """Isobares m·10ⁿ (m dans ``par_decade``) entre P triple et P max du modèle."""
        f = self.fluide
        p_min = float(self.unites.depuis_si("P", f.Ptriple))
        p_max = float(self.unites.depuis_si("P", f.Pmax))
        return self._valeurs_decades(p_min, p_max, par_decade, une_sur, debut)

    def _valeurs_decades(
        self, v_min: float, v_max: float, par_decade: Sequence[float], une_sur: int, debut: int
    ) -> tuple[np.ndarray, list[int]]:
        decades = range(math.floor(math.log10(v_min)), math.ceil(math.log10(v_max)) + 1)
        candidats = {float(f"{m * 10.0**d:.12g}") for d in decades for m in par_decade}
        valeurs = np.array(sorted(v for v in candidats if v_min <= v <= v_max))
        return valeurs, self._une_sur(len(valeurs), une_sur, debut)


class PH(Diagramme):
    """Diagramme des frigoristes : pression (log) en fonction de l'enthalpie massique."""

    type_diagramme = "Ph"
    titre_diagramme = "Diagramme Pression/Enthalpie"

    def __init__(
        self,
        fluide: str | Fluide,
        *,
        hlim: tuple[float, float] | None = None,
        plim: tuple[float, float] | None = None,
        Plogscale: bool = True,
        **kwargs: Any,
    ) -> None:
        super().__init__(fluide, "H", "P", xlim=hlim, ylim=plim, ylog=Plogscale, **kwargs)


class TS(Diagramme):
    """Diagramme entropique : température en fonction de l'entropie massique."""

    type_diagramme = "Ts"
    titre_diagramme = "Diagramme Température/Entropie"

    def __init__(
        self,
        fluide: str | Fluide,
        *,
        slim: tuple[float, float] | None = None,
        Tlim: tuple[float, float] | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(fluide, "S", "T", xlim=slim, ylim=Tlim, **kwargs)


class HS(Diagramme):
    """Diagramme de Mollier : enthalpie massique en fonction de l'entropie massique."""

    type_diagramme = "hs"
    titre_diagramme = "Diagramme de Mollier"

    def __init__(
        self,
        fluide: str | Fluide,
        *,
        slim: tuple[float, float] | None = None,
        hlim: tuple[float, float] | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(fluide, "S", "H", xlim=slim, ylim=hlim, **kwargs)


class PV(Diagramme):
    """Diagramme de Clapeyron : pression en fonction du volume massique (log-log)."""

    type_diagramme = "Pv"
    titre_diagramme = "Diagramme de Clapeyron"

    def __init__(
        self,
        fluide: str | Fluide,
        *,
        vlim: tuple[float, float] | None = None,
        plim: tuple[float, float] | None = None,
        **kwargs: Any,
    ) -> None:
        kwargs.setdefault("xlog", True)
        kwargs.setdefault("ylog", True)
        super().__init__(fluide, "V", "P", xlim=vlim, ylim=plim, **kwargs)


class PT(Diagramme):
    """Diagramme de phases : pression (log) en fonction de la température.

    ``saturation`` trace les courbes de vaporisation (du point triple au point
    critique), de fusion (loi de CoolProp, quand il en a une) et de sublimation, avec
    le point triple et le point critique. CoolProp n'a pas de loi de sublimation : la
    courbe suit Clausius-Clapeyron depuis le point triple, avec une enthalpie de
    sublimation L_vap(T_t) + ``L_fusion`` constante et une vapeur parfaite ; elle n'est
    tracée que si ``L_fusion`` (enthalpie massique de fusion, dans l'unité d'affichage
    de h : 333,5 kJ/kg pour l'eau, 196 pour le CO₂) est donnée. Par défaut, la fenêtre
    descend sous le point triple pour la montrer.
    """

    type_diagramme = "PT"
    titre_diagramme = "Diagramme de phases"

    def __init__(
        self,
        fluide: str | Fluide,
        *,
        Tlim: tuple[float, float] | None = None,
        plim: tuple[float, float] | None = None,
        Plogscale: bool = True,
        L_fusion: float | None = None,
        **kwargs: Any,
    ) -> None:
        self.L_fusion = L_fusion
        super().__init__(fluide, "T", "P", xlim=Tlim, ylim=plim, ylog=Plogscale, **kwargs)

    def _limites_defaut(self, grandeur: str) -> tuple[float, float]:
        f = self.fluide
        if grandeur == "T":
            bornes = (f.Ttriple - 0.2 * (f.Tcrit - f.Ttriple), 1.2 * f.Tcrit)
        else:
            bornes = (f.Ptriple / 100, 10 * f.Pcrit)
        bas, haut = self.unites.depuis_si(grandeur, bornes)
        return float(bas), float(haut)

    # --- courbes de changement d'état, en unités d'affichage -----------------------------

    def _affiche(self, T: np.ndarray, P: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        return self.unites.depuis_si("T", T), self.unites.depuis_si("P", P)

    @property
    def point_triple(self) -> tuple[float, float]:
        """(T, P) du point triple."""
        T, P = self._affiche(np.array(self.fluide.Ttriple), np.array(self.fluide.Ptriple))
        return float(T), float(P)

    @property
    def point_critique(self) -> tuple[float, float]:
        """(T, P) du point critique."""
        T, P = self._affiche(np.array(self.fluide.Tcrit), np.array(self.fluide.Pcrit))
        return float(T), float(P)

    def vaporisation(self, n: int = 200) -> tuple[np.ndarray, np.ndarray]:
        """(T, P) de la courbe de vaporisation, du point triple au point critique."""
        return self._affiche(*self.fluide.courbe_saturation(n))

    def fusion(self, n: int = 200) -> tuple[np.ndarray, np.ndarray]:
        """(T, P) de la courbe de fusion de CoolProp (``ValueError`` s'il n'en a pas)."""
        return self._affiche(*self.fluide.courbe_fusion(n))

    def sublimation(self, n: int = 200, Tmin: float | None = None) -> tuple[np.ndarray, np.ndarray]:
        """(T, P) de la courbe de sublimation, de ``Tmin`` (bas de la fenêtre par défaut)
        au point triple, par Clausius-Clapeyron : ln(P/P_t) = −(L_sub/r)·(1/T − 1/T_t)."""
        if self.L_fusion is None:
            raise ValueError("Donnez L_fusion (enthalpie de fusion) pour tracer la sublimation.")
        f = self.fluide
        L_sub = f.L_vap(f.Ttriple) + float(self.unites.vers_si("H", self.L_fusion))
        T_bas = float(self.unites.vers_si("T", self.xlim[0] if Tmin is None else Tmin))
        T = np.linspace(min(T_bas, 0.8 * f.Ttriple), f.Ttriple, n)
        P = f.Ptriple * np.exp(-L_sub / f.r * (1 / T - 1 / f.Ttriple))
        return self._affiche(T, P)

    def saturation(self, points: bool = True, **style: Any) -> list[Line2D]:
        """Courbes de vaporisation, de fusion et de sublimation (voir la classe), en trait
        épais ; avec ``points``, le point triple et le point critique, étiquetés T et C."""
        ax = self._axes()
        style.setdefault("color", "black")
        style.setdefault("linewidth", 1.5)
        courbes = [self.vaporisation()]
        with suppress(ValueError):  # CoolProp sans loi de fusion pour ce fluide
            courbes.append(self.fusion())
        if self.L_fusion is not None:
            courbes.append(self.sublimation())
        lignes = [ax.plot(T, P, **style)[0] for T, P in courbes]
        if points:
            self.ajoute_point(*self.point_triple, "T", angle=-45, color=style["color"])
            self.ajoute_point(*self.point_critique, "C", angle=-45, color=style["color"])
        return lignes
