import re
from pathlib import Path

import pytest

import thermodiagrammes
from thermodiagrammes import diagrammes, fluide

# Ce que les exercices et les exemples importent de la tête de paquet.
NOMS_DES_EXERCICES = {
    "PH",
    "TS",
    "HS",
    "PV",
    "PT",
    "Diagramme",
    "Etat",
    "Fluide",
    "Unites",
    "formate_nombre",
}


def test_version_lue_par_pyproject():
    pyproject = (Path(__file__).parents[1] / "pyproject.toml").read_text()
    assert 'path = "src/thermodiagrammes/__init__.py"' in pyproject
    assert re.fullmatch(r"\d+\.\d+\.\d+", thermodiagrammes.__version__)


def test_la_tete_de_paquet_reexporte_tous_les_modules():
    assert set(diagrammes.__all__) | set(fluide.__all__) <= set(thermodiagrammes.__all__)


def test_les_noms_des_exercices_sont_exposes():
    assert set(thermodiagrammes.__all__) >= NOMS_DES_EXERCICES


@pytest.mark.parametrize("nom", sorted(NOMS_DES_EXERCICES))
def test_chaque_nom_vient_de_son_module(nom):
    objet = getattr(thermodiagrammes, nom)
    module = "thermodiagrammes.fluide" if nom == "Fluide" else "thermodiagrammes.diagrammes"
    assert objet is getattr(__import__(module, fromlist=[nom]), nom)
