import subprocess
import sys

import numpy as np
import pytest

pytest.importorskip("CoolProp")

from pyphysique.thermo.fluide import Fluide


@pytest.fixture(scope="module")
def eau():
    return Fluide("Water")


def test_nom_inconnu_refuse():
    with pytest.raises(ValueError, match="inconnu"):
        Fluide("Eau")


def test_alias_ramene_au_nom_coolprop():
    assert Fluide("R728").nom == "Nitrogen"


def test_points_remarquables_de_l_eau(eau):
    assert eau.Ttriple == pytest.approx(273.16)
    assert eau.Tcrit == pytest.approx(647.096)
    assert eau.Pmax == pytest.approx(1e9)


def test_etat_hors_modele_scalaire_donne_nan(eau):
    assert np.isnan(eau.H(P=1e5, T=200.0))


def test_etat_hors_modele_dans_un_tableau_donne_nan(eau):
    h = eau.H(P=1e5, T=np.array([200.0, 300.0]))
    assert np.isnan(h[0])
    assert h[1] == pytest.approx(112_654, rel=1e-4)


def test_tableau_d_un_seul_point_invalide_donne_nan(eau):
    assert np.isnan(eau.H(P=1e5, T=np.array([200.0]))).all()


def test_volume_massique_inverse_de_la_masse_volumique(eau):
    assert eau.V(P=1e5, T=300.0) == pytest.approx(1 / eau.D(P=1e5, T=300.0))


def test_volume_massique_accepte_en_entree(eau):
    v = eau.V(P=1e5, Q=1)
    assert eau.T(P=1e5, V=v) == pytest.approx(eau.Tsat(1e5))


def test_grandeur_inconnue_refusee(eau):
    with pytest.raises(ValueError, match="not valid"):
        eau.prop("X", P=1e5, T=300.0)


def test_ebullition_sous_une_atmosphere(eau):
    assert eau.Tsat(101325) == pytest.approx(373.124, abs=1e-3)


def test_phase_avec_le_bon_nom_de_fonction(eau):
    assert eau.phase(P=101325, T=300) == "liquid"


def test_derivee_donne_cp(eau):
    assert eau.derivee("H", "T", "P", P=1e5, T=300) == pytest.approx(4180, rel=1e-3)


def test_courbe_de_saturation_finit_au_point_critique(eau):
    T, P = eau.courbe_saturation(50)
    assert (T[-1], P[-1]) == (eau.Tcrit, eau.Pcrit)
    assert np.all(np.diff(P) > 0)


def test_courbe_de_fusion_utilise_pmax_de_coolprop():
    T, _ = Fluide("N2").courbe_fusion(20)
    assert np.isfinite(T).all()
    assert T[0] == pytest.approx(63.151, abs=1e-3)


def test_fusion_dans_les_deux_sens():
    azote = Fluide("N2")
    P = 1e7
    assert azote.Pfus(azote.Tfus(P)) == pytest.approx(P, rel=1e-6)


def test_masse_molaire_et_constante_massique(eau):
    assert pytest.approx(18.015e-3, rel=1e-3) == eau.M
    assert eau.r == pytest.approx(461.5, rel=1e-3)


def test_enthalpie_de_vaporisation_sous_une_atmosphere(eau):
    assert eau.L_vap(373.124) == pytest.approx(2256e3, rel=1e-3)


@pytest.mark.parametrize(
    ("sortie", "entrees"),
    [
        ("T", {"H": 2_675_570, "P": 101_418}),
        ("P", {"S": 7354.1, "T": 373.15}),
        ("Q", {"H": 2_000_000, "P": 101_418}),
    ],
)
def test_chaque_paire_d_entrees_de_coolprop_acceptee(eau, sortie, entrees):
    assert np.isfinite(eau.prop(sortie, **entrees))


def test_message_explicite_sans_coolprop():
    code = (
        "import sys; sys.modules['CoolProp'] = None\n"
        "try:\n    import pyphysique.thermo.fluide\n"
        "except ImportError as e:\n    print(e)"
    )
    sortie = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, check=True
    )
    assert sortie.stdout.strip() == "CoolProp manque : pip install 'pyphysique[coolprop]'"
