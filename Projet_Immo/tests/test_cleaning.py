"""Tests unitaires du nettoyage : cas conformes, invalides et limites."""
import pandas as pd
import pytest

from processing.cleaning import (
    deduire_transaction, normaliser_date, normaliser_periodicite, normaliser_prix,
    normaliser_surface, normaliser_transaction, normaliser_type_bien, charger_referentiels,
)


# ----------------------------- prix
@pytest.mark.parametrize("brut, attendu, etat", [
    (37965000, 37965000.0, "ok"),                 # conforme
    ("37 965 000", 37965000.0, "corrige"),        # séparateur de milliers (espace)
    ("1,250,000", 1250000.0, "corrige"),          # séparateur de milliers (virgule)
    ("65575000 FCFA", 65575000.0, "corrige"),     # suffixe d'unité
    ("58.29 millions", 58290000.0, "corrige"),    # unité explicite
])
def test_prix_normalisables(brut, attendu, etat):
    assert normaliser_prix(brut) == (attendu, etat)


@pytest.mark.parametrize("brut, etat", [
    (None, "absent"), ("", "absent"), ("N/A", "absent"),
    ("à négocier", "illisible"), ("quatre-vingt", "illisible"),
])
def test_prix_non_convertibles(brut, etat):
    valeur, e = normaliser_prix(brut)
    assert valeur is None and e == etat


def test_prix_zero_ou_negatif_reste_numerique():
    # la conversion ne juge pas : c'est la règle de validation (> 0) qui rejette
    assert normaliser_prix(0) == (0.0, "ok")
    assert normaliser_prix(-5) == (-5.0, "ok")


# ----------------------------- surface
def test_surface_virgule_decimale():
    assert normaliser_surface("53,0") == (53.0, "corrige")
    assert normaliser_surface("367,4") == (367.4, "corrige")


def test_surface_1_250_est_ambigue_et_non_devinee():
    assert normaliser_surface("1,250") == (None, "ambigu")
    assert normaliser_surface("1.250") == (None, "ambigu")


def test_surface_texte_en_lettres_illisible():
    assert normaliser_surface("quatre-vingt") == (None, "illisible")


# ----------------------------- dates
def test_date_iso_et_francaise():
    assert normaliser_date("2024-03-01") == (pd.Timestamp("2024-03-01"), "ok")
    assert normaliser_date("01/03/2024") == (pd.Timestamp("2024-03-01"), "corrige")  # jour en premier
    assert normaliser_date("5 mars 2024") == (pd.Timestamp("2024-03-05"), "corrige")


@pytest.mark.parametrize("brut, etat", [
    ("32/13/2024", "impossible"), ("2024-02-30", "impossible"),
    ("hier", "relative"), (None, "absent"), ("n'importe quoi", "illisible"),
])
def test_date_invalide(brut, etat):
    valeur, e = normaliser_date(brut)
    assert pd.isna(valeur) and e == etat


# ----------------------------- catégories
def test_type_bien_synonymes_et_casse():
    refs = charger_referentiels()
    assert normaliser_type_bien("appart", refs) == ("Appartement", "corrige")
    assert normaliser_type_bien("TERRAIN", refs) == ("Terrain", "corrige")
    assert normaliser_type_bien("Villa", refs) == ("Villa", "ok")
    assert normaliser_type_bien("château", refs)[1] == "hors_referentiel"


def test_transaction_et_periodicite():
    assert normaliser_transaction("LOCATION") == ("location", "corrige")
    assert normaliser_transaction("???")[1] == "illisible"
    assert normaliser_periodicite("FCFA/mois") == "mensuel"
    assert normaliser_periodicite("par mois") == "mensuel"
    assert normaliser_periodicite("FCFA") is None          # jamais devinée


def test_deduction_transaction():
    assert deduire_transaction("notaires", None) == "vente"        # par nature de la source
    assert deduire_transaction("agence_teranga", "Loué") == "location"
    assert deduire_transaction("agence_teranga", "Vendu") == "vente"
    assert deduire_transaction("agence_teranga", None) is None      # pas de statut : on ne devine pas
