"""Tests d'intégration : concaténation, quarantaine justifiée, doublons, indicateurs."""
import pandas as pd

from processing.cleaning import nettoyer_dataframe
from processing.harmonizer import concatener_sources
from validation.validation import valider_dataframe

AUJOURDHUI = pd.Timestamp("2026-10-28")


def _ligne(**kw):
    base = dict(source="notaires", ligne_source=1, id_local="NOT-1", date="2024-01-10",
                region="Dakar", ville="Pikine", type_bien="Maison", type_transaction=None,
                prix=50_000_000, devise=None, surface=100.0, chambres=3, sdb=2,
                statut="Vendu", quartier=None, date_expiration=None)
    base.update(kw)
    return base


def _traiter(lignes):
    df = concatener_sources({"x": pd.DataFrame(lignes)})
    return valider_dataframe(nettoyer_dataframe(df), aujourd_hui=AUJOURDHUI)[0]


def test_concatenation_garde_provenance_et_id_unique():
    a = pd.DataFrame([_ligne(id_local="A")]); b = pd.DataFrame([_ligne(source="historique", id_local="A")])
    df = concatener_sources({"notaires": a, "historique": b})
    assert len(df) == 2 and df["id_bien"].is_unique
    assert set(df["source"]) == {"notaires", "historique"}


def test_ligne_conforme_est_retenue():
    r = _traiter([_ligne(type_transaction="vente")])
    assert r.loc[0, "statut_final"] == "retenu_conforme"


def test_transaction_deduite_compte_comme_correction():
    r = _traiter([_ligne()])                      # transaction absente, source = notaires
    assert r.loc[0, "type_transaction"] == "vente" and r.loc[0, "transaction_deduite"]
    assert r.loc[0, "statut_final"] == "retenu_corrige"


def test_chaque_quarantaine_a_un_motif():
    r = _traiter([
        _ligne(id_local="1", prix=None),
        _ligne(id_local="2", surface="quatre-vingt"),
        _ligne(id_local="3", date="32/13/2024"),
        _ligne(id_local="4", date="2099-01-01"),
        _ligne(id_local="5", prix=0),
        _ligne(id_local="6", type_bien="château"),
        _ligne(id_local=None),
    ])
    quar = r[r["statut_final"] == "quarantaine"]
    assert len(quar) == 7 and (quar["motifs_quarantaine"] != "").all()


def test_doublon_exact_en_quarantaine_original_conserve():
    r = _traiter([_ligne(type_transaction="vente"), _ligne(type_transaction="vente")])
    assert list(r["statut_final"]) == ["retenu_conforme", "quarantaine"]
    assert "doublon_exact" in r.loc[1, "motifs_quarantaine"]


def test_valeurs_atypiques_conservees_avec_avertissement():
    r = _traiter([_ligne(surface=3.0), _ligne(id_local="2", prix=50_000)])
    assert (r["statut_final"] == "retenu_avertissement").all()
    assert "surface_atypique" in r.loc[0, "avertissements"]
    assert "prix_vente_atypique" in r.loc[1, "avertissements"]


def test_region_ville_incoherentes_signalees_pas_corrigees():
    r = _traiter([_ligne(region="Thiès", ville="Pikine")])
    assert "region_ville_incoherente" in r.loc[0, "avertissements"]
    assert r.loc[0, "region"] == "Thiès"            # ne pas corriger sans preuve


def test_doublon_probable_entre_sources_signale_sans_fusion():
    a = _ligne(source="agence_teranga", id_local="A1", statut="Vendu")
    b = _ligne(source="particuliers", id_local="P1", statut="Vendu", surface=101.0, prix=51_000_000,
               date="2024-01-20")
    r = _traiter([a, b])
    assert len(r) == 2 and r["groupe_doublon"].notna().all() and r["groupe_doublon"].nunique() == 1


def test_surface_1_250_part_en_quarantaine():
    r = _traiter([_ligne(surface="1,250")])
    assert "surface_ambigu" in r.loc[0, "motifs_quarantaine"]
