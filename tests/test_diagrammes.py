import math
import sys

import numpy as np
import pytest

pytest.importorskip("CoolProp")

from pyphysique.thermo.diagrammes import (
    HS,
    PH,
    PT,
    PV,
    TS,
    Diagramme,
    Etat,
    Unites,
    formate_nombre,
)
from pyphysique.thermo.fluide import Fluide


@pytest.fixture(scope="module")
def azote():
    return Fluide("N2")


@pytest.fixture(scope="module")
def eau():
    return Fluide("Water")


class TestUnites:
    @pytest.mark.parametrize(
        ("grandeur", "si", "affiche"),
        [("P", 1e5, 1.0), ("H", 2500e3, 2500.0), ("S", 1e3, 1.0), ("T", 373.15, 100.0)],
    )
    def test_conversion_aller_retour(self, grandeur, si, affiche):
        unites = Unites()
        assert unites.depuis_si(grandeur, si) == pytest.approx(affiche)
        assert unites.vers_si(grandeur, affiche) == pytest.approx(si)

    def test_unite_inconnue_refusee(self):
        with pytest.raises(ValueError, match="inconnue"):
            Unites(P="atm")

    def test_texte_compatible_mathtext(self):
        assert Unites().texte("S") == r"\mathrm{kJ/K/kg}"


@pytest.mark.parametrize(("valeur", "chiffres", "texte"), [(0.5, None, "0,5"), (2.0, 2, "2,00")])
def test_formate_nombre_ecrit_une_virgule(valeur, chiffres, texte):
    assert formate_nombre(valeur, chiffres) == texte


def test_limites_par_defaut_entourent_le_dome_de_l_azote(azote):
    # h_liq < 0 au point triple : la marge multiplicative coupait le dôme.
    diagramme = PH(azote)
    h_liquide = azote.H(T=azote.Ttriple, Q=0) / 1e3
    assert diagramme.xlim[0] < h_liquide < 0


def test_isotitre_finit_au_point_critique(eau):
    h, P = PH(eau).isoligne("Q", 0)
    assert h[-1] == pytest.approx(eau.H(T=eau.Tcrit, D=eau.rhocrit) / 1e3)
    assert P[-1] == pytest.approx(eau.Pcrit / 1e5)


def test_isotherme_a_un_palier_exact(eau):
    h, P = PH(eau).isoligne("T", 100)
    palier = np.isclose(P, eau.Psat(373.15) / 1e5, rtol=1e-12)
    assert palier.sum() == 2
    assert sorted(h[palier]) == pytest.approx(
        [eau.H(T=373.15, Q=0) / 1e3, eau.H(T=373.15, Q=1) / 1e3]
    )


def test_isobare_du_diagramme_entropique_a_un_palier_exact(eau):
    _, T = TS(eau).isoligne("P", 1)
    palier = np.isclose(T, eau.Tsat(1e5) - 273.15, rtol=1e-12)
    assert palier.sum() == 2


def test_isobare_hors_modele_donne_des_nan_avec_avertissement(eau):
    with pytest.warns(UserWarning, match="unités d'affichage"):
        s, _ = TS(eau).isoligne("P", 50_000)  # 5 GPa > pmax = 1 GPa
    assert np.isnan(s).all()


def test_isoligne_partiellement_hors_modele_sans_avertissement(eau, recwarn):
    TS(eau).isoligne("P", 1)
    assert not recwarn


@pytest.mark.parametrize("classe", [PH, TS, HS, PV, PT])
def test_chaque_diagramme_trace_saturation_et_isentropes(eau, classe):
    diagramme = classe(eau)
    diagramme.cree()
    lignes = diagramme.saturation() + diagramme.trace_isos("S", [2, 6])
    assert all(np.isfinite(ligne.get_xydata()).any() for ligne in lignes)


@pytest.mark.parametrize("classe", [PH, TS, HS, PV, PT])
def test_chaque_diagramme_a_la_meme_api_de_cycle(eau, classe, tmp_path):
    diagramme = classe(eau)
    diagramme.cree()
    un, deux = diagramme.coordonnees(T=100, Q=1), diagramme.coordonnees(T=200, P=1)
    diagramme.trace_chemin(un, deux, "P")
    diagramme.ajoute_point(*un, "1")
    assert isinstance(diagramme.etat(T=100, Q=1), Etat)
    assert diagramme.enregistre(tmp_path / "d.pdf").exists()


def test_isoligne_inconnue_refusee_avec_la_liste(eau):
    diagramme = PH(eau)
    diagramme.cree()
    with pytest.raises(ValueError, match=r"'X' inconnue.*'T', 'P', 'H'"):
        diagramme.trace_isos("X", [1])


def test_isochores_automatiques_triees_sans_doublon(eau):
    valeurs, _ = PH(eau).valeurs_auto_v(par_decade=(1, 2, 5))
    assert np.all(np.diff(valeurs) > 0)


@pytest.mark.parametrize(
    ("valeur", "pas", "attendu"), [(-20.9999, 10, -20), (0.01, 10, 10), (30, 10, 30)]
)
def test_arrondi_superieur_aussi_pour_les_negatifs(valeur, pas, attendu):
    assert Diagramme._arrondi_superieur(valeur, pas) == attendu


def test_valeurs_auto_T_commencent_au_dessus_du_point_triple(azote):
    valeurs, etiquettes = PH(azote).valeurs_auto_T(pas=20, arrondi=10, une_sur=4, debut=2)
    assert valeurs[0] == -200
    assert etiquettes[0] == 2


class TestEtiquettes:
    @pytest.mark.parametrize("position", [0.0, 1.0])
    def test_position_aux_extremites_acceptee(self, eau, position):
        diagramme = PH(eau)
        diagramme.cree()
        diagramme.trace_isos("S", [5.0], position=position)
        assert len(diagramme.ax.texts) == 1

    def test_rotation_numerique_et_relative_aux_donnees(self, eau):
        diagramme = PH(eau)
        diagramme.cree()
        diagramme.trace_isos("S", [5.0])
        texte = diagramme.ax.texts[0]
        assert isinstance(texte.get_rotation(), float)
        assert texte.get_transform_rotates_text()

    def test_courbe_invisible_sans_etiquette(self, eau):
        diagramme = PH(eau, plim=(1, 10))
        diagramme.cree()
        diagramme.trace_isos("T", [1000])
        assert len(diagramme.ax.texts) == 0

    def test_label_iso_avec_virgule_et_unite(self, eau):
        assert PH(eau).label_iso("S", 1.5) == r"$s=1{,}5$ $\mathrm{kJ/K/kg}$"

    def test_label_iso_sans_unite(self, eau):
        assert PH(eau).label_iso("S", 1.5, unite=False) == r"$s=1{,}5$"

    def test_trace_isos_sans_unite_etiquette_sans_unite(self, eau):
        diagramme = PH(eau)
        diagramme.cree()
        diagramme.trace_isos("S", [5.0], unite=False)
        assert diagramme.ax.texts[0].get_text() == "$s=5$"


def test_point_decale_en_points_typographiques_sur_axe_log(eau):
    diagramme = PH(eau)
    diagramme.cree()
    diagramme.ajoute_point(2800, 10, "A", angle=0, distance=10)
    annotation = diagramme.ax.texts[0]
    assert annotation.xy == (2800, 10)
    assert annotation.xyann == pytest.approx((10, 0))


def test_enregistre_sous_le_nom_par_defaut(eau, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    diagramme = TS(eau)
    diagramme.cree()
    assert diagramme.enregistre().name == "Diagramme_Ts_coolprop_Water.pdf"
    assert (tmp_path / "Diagramme_Ts_coolprop_Water.pdf").exists()


def test_graduations_avec_virgule(eau):
    diagramme = PH(eau, plim=(0.5, 300))
    axes = diagramme.cree()
    assert axes.yaxis.get_major_formatter()(0.5, 0) == "0,5"
    assert math.isclose(axes.get_ylim()[0], 0.5)


def test_axe_inconnu_refuse(eau):
    with pytest.raises(ValueError, match="Axe"):
        Diagramme(eau, "U", "P")


def test_module_charge_sans_locale_globale():
    import locale

    assert "diagrammes" in sys.modules["pyphysique.thermo.diagrammes"].__name__
    assert locale.setlocale(locale.LC_NUMERIC) in ("C", "en_US.UTF-8", "C.UTF-8")


class TestEtat:
    def test_etat_en_unites_d_affichage(self, eau):
        etat = PH(eau).etat(T=100, Q=1)
        assert etat == Etat(
            T=100.0,
            P=eau.Psat(373.15) / 1e5,
            h=eau.H(T=373.15, Q=1) / 1e3,
            s=eau.S(T=373.15, Q=1) / 1e3,
            v=eau.V(T=373.15, Q=1),
            x=1.0,
        )

    def test_etat_suit_les_unites_du_diagramme(self, eau):
        etat = PH(eau, unites=Unites(T="kelvin", P="Pa", H="J", V="L")).etat(T=373.15, Q=0)
        assert etat.T == 373.15
        assert pytest.approx(eau.Psat(373.15)) == etat.P
        assert etat.v == pytest.approx(1e3 * eau.V(T=373.15, Q=0))

    def test_titre_nan_hors_du_dome(self, eau):
        assert math.isnan(PH(eau).etat(T=300, P=1).x)

    def test_etat_est_gele(self, eau):
        with pytest.raises(AttributeError):
            PH(eau).etat(T=100, Q=1).T = 0

    def test_etat_en_si_par_erreur_avertit(self, eau):
        with pytest.warns(UserWarning, match=r"P = 100000\.0.*unités d'affichage"):
            etat = PH(eau).etat(P=1e5, Q=1)
        assert math.isnan(etat.h)

    @pytest.mark.parametrize("grandeurs", [{"T": 1}, {"T": 1, "P": 2, "Q": 3}, {"U": 1, "P": 2}])
    def test_grandeurs_invalides_refusees(self, eau, grandeurs):
        with pytest.raises(ValueError):
            PH(eau).etat(**grandeurs)


class TestCycle:
    def test_coordonnees_de_la_vapeur_saturante(self, eau):
        h, pression = PH(eau).coordonnees(T=100, Q=1)
        assert h == pytest.approx(eau.H(T=373.15, Q=1) / 1e3)
        assert pression == pytest.approx(eau.Psat(373.15) / 1e5)

    def test_coordonnees_en_si_par_erreur_avertissent(self, eau):
        with pytest.warns(UserWarning, match="unités d'affichage"):
            h, _ = PH(eau).coordonnees(P=1e5, Q=1)
        assert math.isnan(h)

    def test_chemin_sans_grandeur_est_un_segment(self, eau):
        h, P = PH(eau).chemin((2800, 10), (2600, 1))
        assert h.tolist() == [2800, 2600]
        assert P.tolist() == [10, 1]

    def test_isentrope_garde_l_entropie_du_depart(self, eau):
        diagramme = PH(eau)
        depart = diagramme.coordonnees(T=400, P=10)
        arrivee = diagramme.coordonnees(S=eau.S(T=673.15, P=1e6) / 1e3, P=1)
        h, P = diagramme.chemin(depart, arrivee, "S")
        s = eau.S(H=h * 1e3, P=P * 1e5) / 1e3
        assert s == pytest.approx(s[0], rel=1e-6)
        assert (h[-1], P[-1]) == pytest.approx(arrivee)

    def test_isotherme_traverse_le_palier_de_vaporisation(self, eau):
        diagramme = PH(eau)
        liquide = diagramme.coordonnees(T=100, P=10)
        vapeur = diagramme.coordonnees(T=100, P=0.5)
        _, P = diagramme.chemin(liquide, vapeur, "T", n=200)
        sur_le_palier = np.isclose(P, eau.Psat(373.15) / 1e5, rtol=1e-6)
        assert sur_le_palier.sum() > 10

    def test_isobare_du_diagramme_entropique_a_un_palier(self, eau):
        diagramme = TS(eau)
        liquide = diagramme.coordonnees(T=50, P=1)
        vapeur = diagramme.coordonnees(T=150, P=1)
        _, T = diagramme.chemin(liquide, vapeur, "P", n=100)
        palier = np.isclose(T, eau.Tsat(1e5) - 273.15, rtol=1e-6)
        assert palier.sum() > 10

    def test_grandeur_inconnue_refusee(self, eau):
        with pytest.raises(ValueError, match="constante inconnue"):
            PH(eau).chemin((2800, 10), (2600, 1), "U")

    def test_trace_chemin_pose_une_fleche_dans_le_sens_du_parcours(self, eau):
        diagramme = PH(eau)
        diagramme.cree()
        diagramme.trace_chemin((2000, 10), (3000, 10), "P")
        fleche = diagramme.ax.texts[0]
        assert fleche.xyann[0] < fleche.xy[0]
        assert fleche.xy[0] == pytest.approx(2530, abs=1)

    def test_trace_chemin_sans_fleche(self, eau):
        diagramme = PH(eau)
        diagramme.cree()
        ligne = diagramme.trace_chemin((2000, 10), (3000, 10), fleche=False, linestyle="--")
        assert len(diagramme.ax.texts) == 0
        assert ligne.get_linestyle() == "--"


class TestPT:
    def test_fenetre_par_defaut_descend_sous_le_point_triple(self, eau):
        diagramme = PT(eau)
        assert diagramme.xlim[0] < 0.01 < diagramme.xlim[1]
        assert diagramme.ylim[0] < diagramme.point_triple[1] < diagramme.ylim[1]

    def test_points_remarquables_en_unites_d_affichage(self, eau):
        diagramme = PT(eau)
        assert diagramme.point_triple == pytest.approx((0.01, 0.00611655), rel=1e-4)
        assert diagramme.point_critique == pytest.approx((373.946, 220.64), rel=1e-4)

    def test_vaporisation_du_point_triple_au_point_critique(self, eau):
        T, P = PT(eau).vaporisation(50)
        assert (T[0], P[0]) == pytest.approx(PT(eau).point_triple)
        assert (T[-1], P[-1]) == pytest.approx(PT(eau).point_critique)

    def test_fusion_de_l_eau_descend_avec_la_pression(self, eau):
        T, P = PT(eau).fusion(50)
        assert np.all(np.diff(P) > 0)
        assert T[0] == pytest.approx(0.01, abs=1e-2)  # glace Ih au point triple

    def test_sublimation_du_co2_sous_une_atmosphere(self):
        diagramme = PT("CO2", L_fusion=196)  # kJ/kg
        T, P = diagramme.sublimation(1000)
        assert (T[-1], P[-1]) == pytest.approx(diagramme.point_triple)
        assert np.interp(1.01325, P, T) == pytest.approx(-78.5, abs=2)  # Clausius-Clapeyron

    def test_sublimation_sans_enthalpie_de_fusion_refusee(self, eau):
        with pytest.raises(ValueError, match="L_fusion"):
            PT(eau).sublimation()

    def test_saturation_trace_trois_courbes_et_deux_points(self, eau):
        diagramme = PT(eau, L_fusion=333.5)
        diagramme.cree()
        lignes = diagramme.saturation()
        assert len(lignes) == 3
        assert [t.get_text() for t in diagramme.ax.texts] == ["T", "C"]

    def test_saturation_sans_loi_de_fusion_ni_sublimation(self):
        diagramme = PT("R134a")
        diagramme.cree()
        assert len(diagramme.saturation(points=False)) == 1
