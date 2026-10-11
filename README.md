# thermodiagrammes

Diagrammes thermodynamiques d'un fluide réel, étiquetés et prêts à distribuer en
exercice : (P, h) des frigoristes, (T, s) entropique, (h, s) de Mollier, (P, v) de
Clapeyron et diagramme de phases (P, T). Les propriétés viennent de
[CoolProp](https://coolprop.org/) ; le paquet trace la courbe de saturation et les
isolignes avec leurs étiquettes, calcule les états d'un cycle fixés par deux grandeurs
et dessine les transformations qui les relient, le tout dans les unités d'affichage
choisies (bar, kJ/kg, °C… par défaut), les nombres écrits avec une virgule.

```python
from thermodiagrammes import PH

diagramme = PH("R134a", hlim=(100, 500), plim=(0.5, 50))  # kJ/kg, bar
diagramme.cree(figsize=(12, 8))
diagramme.saturation()
diagramme.trace_isos("T", [-40, -20, 0, 20, 40, 60, 80], position=0.6)  # °C
vapeur = diagramme.etat(T=-10, Q=1)  # Etat(T=-10.0, P=2.006, h=392.7, s=1.733, v=0.0996, x=1.0)
diagramme.ajoute_point(vapeur.h, vapeur.P, "1")
diagramme.enregistre()  # Diagramme_Ph_coolprop_R134a.pdf
```

Le paquet s'installe depuis GitHub (ci-dessous). Pas de PyPI.

## Sommaire

- [Ce qu'il fait](#ce-quil-fait)
- [Installation](#installation)
- [Prérequis](#prérequis)
- [Prise en main](#prise-en-main)
- [Les cinq diagrammes](#les-cinq-diagrammes)
- [Les unités d'affichage](#les-unités-daffichage)
- [Fluide : les propriétés en SI](#fluide--les-propriétés-en-si)
- [Pièges](#pièges)
- [Les modules](#les-modules)
- [Exemples](#exemples)
- [Tester](#tester)
- [Antériorité](#antériorité)
- [Licence](#licence)

## Ce qu'il fait

- **Cinq diagrammes avec la même interface** : `PH`, `TS`, `HS`, `PV` et `PT`, tous
  avec `cree`, `saturation`, `trace_isos`, `etat`, `coordonnees`, `trace_chemin`,
  `ajoute_point` et `enregistre` ; la fenêtre par défaut entoure le dôme de
  saturation.
- **Des isolignes exactes** : isothermes, isobares, isenthalpes, isentropes, isochores
  et isotitres, calculées sur la plage que l'on voit, avec le palier de vaporisation
  inséré exactement et le dôme fermé au point critique ; une étiquette par courbe,
  posée parallèlement à elle, là où on la demande (`position`), avec ou sans unité.
- **Des cycles** : `etat(T=…, P=…)` donne un `Etat` (T, P, h, s, v, x) à partir de
  deux grandeurs parmi T, P, H, S, V et Q ; `trace_chemin` dessine une isobare, une
  isenthalpe, une isentrope, une isotherme (palier compris), une isochore ou un
  segment entre deux états, avec une flèche dans le sens du parcours.
- **Un diagramme de phases** `PT` avec les courbes de vaporisation, de fusion (loi de
  CoolProp) et de sublimation (Clausius-Clapeyron depuis le point triple), le point
  triple et le point critique.
- **Les unités d'affichage au choix** (`Unites`) : bar, kJ/kg, kJ/K/kg, m³/kg et °C par
  défaut ; Pa, kPa, MPa, J, MJ, L/kg, kelvin… Tout ce que l'on donne et tout ce que
  l'on lit est dans ces unités ; la virgule décimale ne touche pas à la locale.
- **`Fluide`**, les propriétés CoolProp en SI avec des arguments nommés
  (`eau.H(T=373.15, Q=1)`), `nan` hors du modèle au lieu d'une exception, le volume
  massique, les courbes de saturation et de fusion.

## Installation

**Avec pip depuis PyPI**, quand le réseau et pip sont disponibles :

```bash
pip install thermodiagrammes
```

(ou `uv add thermodiagrammes`). **Depuis GitHub**, pour la version de développement :

```bash
pip install git+https://github.com/antnardo/thermodiagrammes
```

**Avec la roue d'une release**, pour un poste qui a pip mais pas git : chaque
[release](https://github.com/antnardo/thermodiagrammes/releases) porte
`thermodiagrammes-<version>-py3-none-any.whl` (et le sdist `.tar.gz`, avec
`examples/`), qui s'installe par `pip install thermodiagrammes-<version>-py3-none-any.whl`.

**Copier le dossier**, sans pip ni réseau : le dossier `src/thermodiagrammes/` se pose
à côté des scripts, et `from thermodiagrammes import PH` fonctionne, à condition
d'exécuter le script depuis son dossier et que CoolProp, numpy et matplotlib soient
déjà installés.

**Pour développer**, un clone et [uv](https://docs.astral.sh/uv/) :

```bash
git clone https://github.com/antnardo/thermodiagrammes
cd thermodiagrammes && uv sync && uv run pytest
```

## Prérequis

Python 3.11 ou plus récent, avec CoolProp (6.6 ou plus, testé avec 8), numpy (1.26 ou
plus) et matplotlib (3.8 ou plus). CoolProp est une dépendance du paquet, pas une
option : pip et uv l'installent avec lui (roue binaire, rien à compiler). Le paquet est
testé sous Python 3.11 et 3.14.

## Prise en main

Un diagramme se construit avec le nom CoolProp du fluide (`"Water"`, `"R134a"`,
`"Nitrogen"` ou un alias : `"N2"`, `"R728"`, `"CO2"`) ou un `Fluide` déjà créé, et la
fenêtre dans les unités d'affichage (`hlim`, `plim`, `slim`, `Tlim`, `vlim` selon le
diagramme ; par défaut, le dôme de saturation). `cree` ouvre la figure (ses arguments
vont à `plt.subplots`) et règle les axes : échelle logarithmique de la pression,
grilles, graduations à virgule ; la figure et les axes restent accessibles par
`diagramme.fig` et `diagramme.ax`.

```python
import numpy as np
from thermodiagrammes import PH

diagramme = PH("R134a", hlim=(100, 500), plim=(0.5, 50))  # kJ/kg, bar
diagramme.cree(figsize=(12, 8))
diagramme.saturation()
diagramme.trace_isos("T", np.arange(-40, 121, 20), position=0.6)  # °C
diagramme.trace_isos("S", np.arange(1.0, 2.01, 0.1), unite=False, chiffres=1)  # « s=1,7 »

# Cycle frigorifique : évaporation à −10 °C, condensation à 40 °C
un = diagramme.etat(T=-10, Q=1)  # vapeur saturante à la sortie de l'évaporateur
trois = diagramme.etat(T=40, Q=0)  # liquide saturant à la sortie du condenseur
deux = diagramme.etat(S=un.s, P=trois.P)  # compression isentropique
quatre = diagramme.etat(H=trois.h, P=un.P)  # détente isenthalpique
print(f"w = {deux.h - un.h:.1f} kJ/kg, q_froid = {un.h - quatre.h:.1f} kJ/kg, x4 = {quatre.x:.2f}")
# w = 33.8 kJ/kg, q_froid = 136.3 kJ/kg, x4 = 0.34
points = {nom: (e.h, e.P) for nom, e in zip("1234", (un, deux, trois, quatre))}
for depart, arrivee, grandeur in (("1", "2", "S"), ("2", "3", "P"), ("3", "4", "H"), ("4", "1", "P")):
    diagramme.trace_chemin(points[depart], points[arrivee], grandeur)
for nom, angle in zip("1234", (-90, 90, 90, -90)):
    diagramme.ajoute_point(*points[nom], nom, angle=angle)
diagramme.enregistre()  # Diagramme_Ph_coolprop_R134a.pdf
```

Les méthodes, communes aux cinq diagrammes :

| Méthode | Ce qu'elle fait |
| --- | --- |
| `cree(**kwargs)` | crée la figure et les axes (`kwargs` : `figsize`…) et les rend |
| `saturation(**style)` | courbes d'ébullition et de rosée en trait épais (`PT` : vaporisation, fusion, sublimation, points T et C) |
| `trace_isos(grandeur, valeurs, position=0.5, etiquettes=None, n=200, chiffres=None, style_etiquette=None, unite=True, **style)` | isolignes `grandeur` = chaque valeur, `grandeur` parmi `"T"`, `"P"`, `"H"`, `"S"`, `"V"`, `"Q"` ; `etiquettes` : indices des courbes à étiqueter (toutes par défaut, `[]` pour aucune) ; `position` : où le long de la courbe, entre 0 et 1 ; `chiffres` : décimales ; `style` : options de `Axes.plot` |
| `etat(**deux_grandeurs)` | `Etat(T, P, h, s, v, x)` gelé, `x` à `nan` hors du dôme |
| `coordonnees(**deux_grandeurs)` | le couple (x, y) de cet état dans le diagramme |
| `chemin(depart, arrivee, grandeur=None, n=60)` | les points de la transformation à `grandeur` constante entre deux couples (x, y), ou du segment |
| `trace_chemin(depart, arrivee, grandeur=None, fleche=True, n=60, **style)` | la trace, rouge et épaisse par défaut, avec une flèche au milieu |
| `ajoute_point(x, y, label=None, angle=45, distance=8, color="black")` | un point et son étiquette, décalée de `distance` points typographiques dans la direction `angle` (degrés) |
| `isoligne(grandeur, valeur, n=200)` | les points (x, y) d'une isoligne, sans la tracer |
| `label_iso(grandeur, valeur, chiffres=None, unite=True)` | le texte d'une étiquette : `$T=20$ $^\circ\mathrm{C}$`, `$s=1{,}5$` |
| `valeurs_auto_T(pas, …)`, `valeurs_auto_x`, `valeurs_auto_s`, `valeurs_auto_h`, `valeurs_auto_v`, `valeurs_auto_P` | des valeurs d'isolignes raisonnables pour le fluide, et les indices à étiqueter |
| `enregistre(chemin=None, **kwargs)` | `fig.savefig` sous `Diagramme_<type>_coolprop_<fluide>.pdf` par défaut ; rend le chemin |

`trace_isos` et `saturation` rendent les `Line2D` tracées, `trace_chemin` la sienne :
on peut leur donner un `label` pour une légende, ou les retoucher.

Les isothermes et les isobares traversent le dôme par leur palier exact (les deux
points de saturation sont insérés) ; les isotitres se referment au point critique ; une
isoligne est calculée sur la plage de T et de P que la fenêtre montre, pas au-delà, et
s'interrompt sans erreur là où le modèle du fluide s'arrête.

## Les cinq diagrammes

| Classe | Axes | Fenêtre | Échelles | Fichier par défaut |
| --- | --- | --- | --- | --- |
| `PH(fluide, hlim, plim, Plogscale=True)` | h en abscisse, P en ordonnée | kJ/kg, bar | P en log | `Diagramme_Ph_coolprop_<fluide>.pdf` |
| `TS(fluide, slim, Tlim)` | s, T | kJ/K/kg, °C | linéaires | `Diagramme_Ts_…` |
| `HS(fluide, slim, hlim)` | s, h (Mollier) | kJ/K/kg, kJ/kg | linéaires | `Diagramme_hs_…` |
| `PV(fluide, vlim, plim)` | v, P (Clapeyron) | m³/kg, bar | log-log | `Diagramme_Pv_…` |
| `PT(fluide, Tlim, plim, Plogscale=True, L_fusion=None)` | T, P (phases) | °C, bar | P en log | `Diagramme_PT_…` |

Tous acceptent aussi `label` (nom du fluide dans le titre), `unites` (un `Unites`) et
`titre` (`""` pour aucun). `Diagramme(fluide, x, y, …)`, leur base, trace n'importe
quel couple parmi T, P, H, S, V.

`PT` : `saturation` trace la vaporisation du point triple au point critique, la fusion
quand CoolProp a une loi de fusion pour le fluide (eau, azote, CO₂…), et la
sublimation si `L_fusion` (enthalpie massique de fusion, dans l'unité de h : 333,5 kJ/kg
pour l'eau, 196 pour le CO₂) est donnée, par Clausius-Clapeyron depuis le point triple
avec L_sub = L_vap(T_t) + L_fusion. `point_triple`, `point_critique`,
`vaporisation()`, `fusion()` et `sublimation()` donnent ces courbes en unités
d'affichage ; par défaut, la fenêtre descend sous le point triple.

## Les unités d'affichage

Limites, isolignes, états, points, enthalpie de fusion : tout ce que l'on passe à un
diagramme, et tout ce qu'il rend (`Etat`, `coordonnees`, `isoligne`, les courbes de
`PT`), est dans ses unités d'affichage, un `Unites` :

| Grandeur | Défaut | Choix |
| --- | --- | --- |
| `P` | `"bar"` | `"Pa"`, `"kPa"`, `"bar"`, `"MPa"` |
| `H` | `"kJ"` (par kg) | `"J"`, `"kJ"`, `"MJ"` |
| `S` | `"kJ"` (par K et par kg) | `"J"`, `"kJ"` |
| `V` | `"m^3"` (par kg) | `"m^3"`, `"L"` |
| `T` | `"celsius"` | `"kelvin"`, `"celsius"` |

```python
from thermodiagrammes import PH, Unites

diagramme = PH("Water", unites=Unites(T="kelvin", P="MPa", H="MJ"), hlim=(0, 4), plim=(0.001, 50))
diagramme.etat(T=373.15, Q=0)  # P en MPa, h en MJ/kg, s en kJ/K/kg, v en m³/kg
```

`Unites.texte(grandeur)` écrit l'unité en mathtext. Les nombres s'écrivent avec une
virgule (`formate_nombre(1.5)` donne `"1,5"`, les graduations aussi) sans
`setlocale` : rien ne change pour le programme appelant.

### Changer d'unité

Deux mondes, une règle : **`Fluide` parle en SI** (K, Pa, J/kg, J/K/kg, m³/kg, comme
CoolProp), **un diagramme parle dans ses unités d'affichage**. Entre les deux, le
paquet fournit les passages ; un `- 273.15` ou un `/ 1e3` écrit à la main est le
signe qu'il en manque un.

| Besoin | Passage |
| --- | --- |
| un état complet (T, P, h, s, v, x) en unités d'affichage | `diagramme.etat(T=100, Q=0)`, deux grandeurs en unités d'affichage |
| le point critique, le point triple | `diagramme.etat_critique()`, `diagramme.etat_triple(x=0)` (liquide) ou `etat_triple(1)` (vapeur) |
| une température de `Fluide` (K) vers des °C, et retour | `celsius(fluide.Tcrit)`, `kelvin(100)` (aussi `Unites.celsius`, `Unites.kelvin`) |
| une valeur SI quelconque vers l'unité d'affichage, et retour | `unites.depuis_si("P", fluide.Pcrit)`, `unites.vers_si("H", 2500)` |

Un scalaire rend un `float`, un tableau un tableau. Avant et après :

```python
from thermodiagrammes import PV, celsius

diagramme = PV("Water", vlim=(1e-4, 12), plim=(0.1, 1000))
f = diagramme.fluide  # SI
# Avant : des conversions à la main, et une erreur en embuscade
Tc = f.Tcrit - 273.15
T = [100, Tc, 2 * (Tc + 273.15) - 273.15]
h_c = f.H(T=f.Tcrit, D=f.rhocrit) / 1e3
# Après : Tc reste en kelvin, le diagramme fait les conversions
Tc = f.Tcrit
T = [100, celsius(Tc), celsius(2 * Tc)]
h_c = diagramme.etat_critique().h
```

`Fluide` ne prend pas d'unités : c'est la couche CoolProp, et la cohérence des unités
tient à ce qu'elle n'en ait qu'un jeu. Pour un calcul en SI à partir d'un état lu sur
le diagramme, `unites.vers_si("H", etat.h)` ou `kelvin(etat.T)`.

## Fluide : les propriétés en SI

`Fluide` enrobe `CoolProp.PropsSI` pour un fluide pur, en SI (K, Pa, J/kg, J/K/kg,
m³/kg) : les diagrammes s'en servent, et il sert seul pour un calcul.

```python
from thermodiagrammes import Fluide

eau = Fluide("Water")
eau.H(T=373.15, Q=1)           # enthalpie de la vapeur saturante à 100 °C, J/kg
eau.T(H=2_675_570, P=101_325)  # et réciproquement : toute paire de grandeurs
eau.prop("D", P=1e5, T=300)    # grandeur quelconque de CoolProp (ici la masse volumique)
eau.Psat(373.15), eau.Tsat(1e5), eau.L_vap(373.15)
eau.Tfus(1e8), eau.Pfus(260)   # courbe de fusion (CoolProp), nan hors de son domaine
eau.courbe_saturation(), eau.courbe_fusion()   # (T, P) du point triple au point critique
eau.Ttriple, eau.Ptriple, eau.Tcrit, eau.Pcrit, eau.rhocrit, eau.Tmax, eau.Pmax, eau.M, eau.r
```

`prop(sortie, **deux_entrees)` accepte toute paire d'entrées que CoolProp accepte (T,
P, Q, H, S, D, V, U…) et des tableaux ; `T`, `P`, `Q`, `H`, `S`, `U`, `D`, `V` sont des
raccourcis, `V` le volume massique (l'inverse de `D`). Un état hors du modèle vaut
`nan`, scalaire ou dans un tableau, au lieu d'une exception. `phase(P=…, T=…)` nomme
la phase, `derivee("H", "T", "P", P=…, T=…)` donne une dérivée partielle (ici c_p).

## Pièges

- **Des valeurs en SI données à un diagramme.** `diagramme.etat(P=1e5, Q=1)` cherche
  10⁵ bar : l'état vaut `nan` et un avertissement demande si les valeurs sont bien en
  unités d'affichage. Même chose pour une isoligne entièrement hors du modèle
  (`trace_isos("P", [50_000])`). En SI, c'est `Fluide` qu'il faut.
- **CoolProp manquant.** `import thermodiagrammes` lève alors
  `ImportError: CoolProp manque : pip install CoolProp` ; cela n'arrive qu'au dossier
  copié sans installation, pip et uv l'installant avec le paquet.
- **Fluides purs seulement.** `Fluide("INCOMP::MEG-50%")` (fluide incompressible) lève
  `ValueError: inconnu de CoolProp` ; un mélange `"Water&Ethanol"` est réduit à son
  premier composant par CoolProp, sans erreur : vérifier `fluide.nom`.
- `etat` et `coordonnees` veulent exactement deux grandeurs, parmi T, P, H, S, V et Q ;
  `trace_isos("X", …)` ou `chemin(…, "U")` lèvent un `ValueError` qui liste les
  grandeurs possibles.
- `enregistre` avant `cree` échoue (`AssertionError`) ; les autres méthodes de tracé
  créent la figure d'elles-mêmes.
- `PT(...).sublimation()` sans `L_fusion` lève `ValueError` ; `fusion()` lève
  `ValueError` pour un fluide dont CoolProp n'a pas la loi de fusion, et `saturation`
  passe alors la courbe sous silence.
- `plt.tight_layout()` déplace le cadre des axes : à éviter quand un corrigé pose ses
  points en TikZ à des coordonnées fixes sur la figure (les exercices appellent
  `ax.set_position`).
- L'étiquette d'une isoligne n'est posée que si un point de la courbe est visible ; une
  courbe entièrement hors de la fenêtre n'en a pas.

## Les modules

| Module | Contenu |
| --- | --- |
| `thermodiagrammes` | la tête de paquet : `PH`, `TS`, `HS`, `PV`, `PT`, `Diagramme`, `Etat`, `Unites`, `celsius`, `kelvin`, `formate_nombre`, `Fluide`, `__version__` |
| `thermodiagrammes.diagrammes` | les diagrammes, `Etat`, `Unites`, `celsius`, `kelvin`, `formate_nombre` |
| `thermodiagrammes.fluide` | `Fluide` |

## Exemples

Le dossier `examples/` montre chaque diagramme ; les scripts s'exécutent depuis un
dossier de travail, où ils écrivent leurs figures :

| Script | Ce qu'il trace |
| --- | --- |
| `diagramme_ph_azote.py` | (P, h) de l'azote côté vapeur, isothermes, isentropes, isotitres, deux points |
| `diagramme_ph_eau.py` | (P, h) de l'eau, toutes les isolignes aux valeurs automatiques (`valeurs_auto_*`) |
| `diagramme_ph_eau_T6.py` | (P, h) de l'eau en kelvin, de 0,4 à 500 bar, pour le tome 6 du cours |
| `diagramme_ts_eau.py` | (T, s) de l'eau : isobares, isotitres, isenthalpes |
| `mollier_eau.py` | (h, s) de l'eau autour de la courbe de rosée, légende |
| `clapeyron_eau.py` | (P, v) de l'eau : isothermes d'Andrews, isotitres, isenthalpes, isentropes |
| `pv_eau.py` | isothermes d'Andrews en LaTeX pour le cours, trois figures |
| `diagrammes_simplifies_eau.py` | trois petits diagrammes (T, s), (P, h), (h, s) en LaTeX pour le cours |
| `diagramme_pt_eau.py` | diagramme de phases de l'eau : vaporisation, fusion, sublimation, isochores, un chauffage isobare |
| `coolprop_exemples.py` | un tutoriel de CoolProp nu : `PropsSI`, air humide, fluides incompressibles, mélanges, `PropertyPlot` |

`pv_eau.py` et `diagrammes_simplifies_eau.py` demandent une distribution LaTeX
(`text.usetex`).

## Tester

```bash
uv run --python 3.11 pytest
uv run --python 3.14 pytest
uv run ruff check src tests examples && uv run ruff format --check src tests examples
uv run mypy
uv build
```

Les tests vérifient les isolignes contre `Fluide` (palier exact, dôme fermé au point
critique, `nan` hors du modèle avec avertissement), les unités, les étiquettes, les
états et les chemins d'un cycle, le diagramme de phases (points triple et critique,
sublimation du CO₂ à −78,5 °C sous une atmosphère) et la tête de paquet. L'intégration
continue (`.github/workflows/ci.yml`) rejoue tout cela à chaque push sous Python 3.11
et 3.14 ; à chaque release publiée, `publish.yml` vérifie que l'étiquette est la
version du paquet et joint la roue et le sdist à la release.

## Antériorité

Le code descend des scripts py4phys de J.-J. Fleck (lycée Kléber, 2014) pour les
diagrammes (P, h), (T, s) et (P, v) sur CoolProp, développés depuis 2015 pour les
figures d'exercices de thermodynamique en CPGE, jusqu'aux cinq diagrammes, aux états
et aux cycles d'aujourd'hui.

`CoolProp.Plots.PropertyPlot` trace les mêmes isolignes, mais sans étiquettes ni cycle ;
[fluprodia](https://fluprodia.readthedocs.io/) étiquette les isolignes et place des
états, mais sans virgule décimale ni transformations tracées entre deux états.
[luacoolprop](https://ctan.org/pkg/luacoolprop) de Christophe Jorssen (CTAN, septembre
2026) fait la même chose dans LuaTeX : la bibliothèque partagée de CoolProp chargée par
FFI, les cinq mêmes diagrammes tracés par pgfplots avec la courbe de saturation, les
isotitres, les chemins de transformation et des étiquettes placées automatiquement
(`pgfplots-autonode`), pour LaTeX, plain TeX et ConTeXt ; il demande `--shell-escape` et
une CoolProp installée à part. Ici, Python et matplotlib sans TeX : les états se
calculent et les figures se tracent dans le même script, celui d'un corrigé pythontex
ou d'une feuille d'exercices.

## Licence

Le code — le paquet (`src/`) et les tests — est sous licence MIT (`LICENSE`). Les
exemples (`examples/`), qui sont du contenu scientifique et pédagogique plutôt que
des algorithmes, sont sous licence Creative Commons Attribution - Pas d'utilisation
commerciale - Partage dans les mêmes conditions 4.0 International, CC BY-NC-SA 4.0
(`LICENSE-CC-BY-NC-SA-4.0`).
