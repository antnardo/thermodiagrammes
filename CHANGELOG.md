# Changelog

Le format suit [Keep a Changelog](https://keepachangelog.com/fr/1.1.0/) et le
[versionnage sémantique](https://semver.org/lang/fr/).

## [0.1.1] - 2026-10-11

### Ajouté

- Les changements d'unités, documentés (README, « Changer d'unité ») et outillés :
  `celsius(T)` et `kelvin(T)` (aussi `Unites.celsius`, `Unites.kelvin`), les états
  `Diagramme.etat_critique()` et `etat_triple(x=0)` en unités d'affichage, et
  `Unites.depuis_si` / `vers_si` qui rendent un `float` pour un scalaire. Les
  exemples `clapeyron_eau`, `mollier_eau` et `diagrammes_simplifies_eau` n'ont plus
  de `- 273.15` ni de `/ 1e3` à la main.

### Modifié

- L'antériorité du README : la lignée remonte aux scripts py4phys de J.-J. Fleck
  (2014) adaptés en octobre 2015, non à 2024.

## [0.1.0] - 2026-10-11

Première version. Le paquet reprend `pyphysique.thermo.diagrammes` et
`pyphysique.thermo.fluide`, descendants de scripts de 2015 réécrits de 2023 à 2026 dans le dépôt privé `pyphysique`
pour les figures et les corrigés des exercices de cycles thermodynamiques, et les
publie tels quels : seuls les chemins d'import changent (`from thermodiagrammes import
PH, Fluide`).

### Ajouté

- `PH`, `TS`, `HS`, `PV`, `PT` : diagrammes (P, h), (T, s), (h, s) de Mollier, (P, v) de
  Clapeyron et de phases (P, T) d'un fluide pur de CoolProp, avec la même interface :
  `cree`, `saturation`, `trace_isos`, `etat`, `coordonnees`, `chemin`, `trace_chemin`,
  `ajoute_point`, `enregistre`, `isoligne`, `label_iso`, `valeurs_auto_*` ;
  `Diagramme(fluide, x, y)` pour tout autre couple d'axes.
- Isolignes T, P, H, S, V et Q calculées sur la plage visible, palier de vaporisation
  exact (points de saturation insérés), dôme fermé au point critique, `nan` sans erreur
  hors du modèle ; étiquettes parallèles à la courbe, posées à la position demandée,
  avec ou sans unité (`unite=False`), avec le nombre de décimales voulu.
- Cycles : `etat(**deux_grandeurs)` rend un `Etat` gelé (T, P, h, s, v, x) en unités
  d'affichage, `coordonnees` le couple (x, y) ; `trace_chemin` suit une isobare, une
  isenthalpe, une isentrope, une isotherme (palier compris), une isochore, un
  isotitre ou un segment, avec une flèche au milieu dans le sens du parcours.
- `PT` : vaporisation, fusion (loi de CoolProp) et sublimation (Clausius-Clapeyron
  depuis le point triple, `L_fusion` à donner), points triple et critique.
- `Unites` : bar, kJ/kg, kJ/K/kg, m³/kg, °C par défaut ; Pa, kPa, MPa, J, MJ, L, kelvin
  au choix ; `formate_nombre` et les graduations à virgule décimale sans `setlocale`.
- `Fluide` : `CoolProp.PropsSI` à arguments nommés, `nan` hors du modèle, volume
  massique `V`, `Psat`, `Tsat`, `L_vap`, `Tfus`, `Pfus`, courbes de saturation et de
  fusion, points remarquables, `M`, `r`, `phase`, `derivee`.
- Garde-fous : `ValueError` qui liste les grandeurs pour une isoligne, un état ou une
  transformation inconnus ; avertissement quand un état ou une isoligne est hors du
  modèle (« valeurs en unités d'affichage ? ») ; `ImportError` explicite sans
  CoolProp ; `ValueError` pour un fluide inconnu de CoolProp (dont `INCOMP::…`).
- Dix exemples : (P, h) de l'azote et de l'eau, (T, s), Mollier, Clapeyron, diagrammes
  simplifiés du cours, diagramme de phases, tutoriel de CoolProp nu.
- Licences : MIT pour le code, CC BY-NC-SA 4.0 pour les exemples. Intégration
  continue (pytest sous Python 3.11 et 3.14, ruff, mypy, `uv build`) et publication
  de la roue et du sdist à chaque release GitHub.

### Modifié

- Chemins d'import : `pyphysique.thermo.diagrammes` devient `thermodiagrammes`
  (tout est réexporté en tête de paquet), `pyphysique.thermo.fluide` devient
  `thermodiagrammes.fluide` (`Fluide` aussi en tête de paquet).
- CoolProp est une dépendance du paquet, non plus un extra : plus de chargement
  paresseux, et le message sans CoolProp dit `pip install CoolProp`.
