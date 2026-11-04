"""
Étape 3 — Normalisation (fonctions pures, testables, et réversibles).

Chaque fonction `normaliser_*` renvoie un couple (valeur, etat) :
  etat = "ok"        : valeur déjà conforme
         "corrige"   : valeur reformatée de façon fiable (documentée ci-dessous)
         "absent"    : valeur manquante
         "illisible" : non convertible de façon fiable
         "ambigu"    : plusieurs lectures possibles, on ne devine pas
Les valeurs d'origine sont conservées dans prix_brut / surface_brut / date_brut.
"""
import re
import unicodedata
from datetime import date, datetime

import numpy as np
import pandas as pd

import config

TEXTES_MANQUANTS = {"", "nan", "none", "null", "n/a", "na", "-"}


# ------------------------------------------------------------------ utilitaires
def est_vide(valeur):
    if valeur is None:
        return True
    try:
        if pd.isna(valeur):
            return True
    except (TypeError, ValueError):
        pass
    return isinstance(valeur, str) and valeur.strip().lower() in TEXTES_MANQUANTS


def cle_texte(texte):
    """Clé de comparaison : sans accents, minuscules, espaces normalisés."""
    t = unicodedata.normalize("NFKD", str(texte))
    t = "".join(c for c in t if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", t).strip().casefold()


def _nombre(valeur):
    return isinstance(valeur, (int, float, np.integer, np.floating)) and not isinstance(valeur, bool)


# ------------------------------------------------------------------ nombres
def normaliser_prix(valeur):
    """
    Règles de normalisation (regles_metier.md) :
      - séparateur de milliers espace ou virgule : '37 965 000', '1,250,000'
      - suffixes FCFA / F CFA / CFA, '/mois'
      - millions avec unité explicite : '58.29 millions' -> 58 290 000
    Tout le reste ('à négocier', 'quatre-vingt'...) est illisible.
    """
    if est_vide(valeur):
        return None, "absent"
    if _nombre(valeur):
        return float(valeur), "ok"

    txt = str(valeur).strip().lower().replace("\u202f", " ").replace("\xa0", " ")

    m = re.fullmatch(r"(-?\d+(?:[.,]\d+)?)\s*millions?(?:\s*(?:de\s*)?(?:f\s*cfa|cfa))?", txt)
    if m:
        return float(m.group(1).replace(",", ".")) * 1_000_000, "corrige"

    sans_suffixe = re.sub(r"\s*(?:f\s*cfa|cfa)\s*(?:/\s*mois)?$", "", txt).strip()
    suffixe = sans_suffixe != txt

    if re.fullmatch(r"-?\d{1,3}(?:[ ,]\d{3})+", sans_suffixe):
        return float(re.sub(r"[ ,]", "", sans_suffixe)), "corrige"
    if re.fullmatch(r"-?\d+(?:\.\d+)?", sans_suffixe):
        return float(sans_suffixe), ("corrige" if suffixe else "ok")
    return None, "illisible"


def normaliser_surface(valeur):
    """
    - virgule décimale : '53,0', '367,4' -> 53.0, 367.4
    - '1,250' / '1.250' : AMBIGU (1 250 m² ou 1,25 m² ?) -> jamais converti sans contexte
    - suffixes m² / m2 acceptés
    """
    if est_vide(valeur):
        return None, "absent"
    if _nombre(valeur):
        return float(valeur), "ok"

    txt = str(valeur).strip().lower().replace("\xa0", " ")
    sans_unite = re.sub(r"\s*(?:m²|m2|m\^2)$", "", txt).strip()
    unite = sans_unite != txt

    if re.fullmatch(r"\d{1,3}[.,]\d{3}", sans_unite):
        return None, "ambigu"
    if re.fullmatch(r"\d+,\d{1,2}", sans_unite):
        return float(sans_unite.replace(",", ".")), "corrige"
    if re.fullmatch(r"-?\d+(?:\.\d+)?", sans_unite):
        return float(sans_unite), ("corrige" if unite else "ok")
    return None, "illisible"


def normaliser_entier(valeur):
    """chambres / sdb : entier, sinon NaN (comptabilisé comme erreur de conversion)."""
    if est_vide(valeur):
        return None, "absent"
    try:
        v = float(str(valeur).replace(",", ".")) if not _nombre(valeur) else float(valeur)
    except ValueError:
        return None, "illisible"
    if v != int(v):
        return None, "illisible"
    return int(v), "ok"


# ------------------------------------------------------------------ dates
def normaliser_date(valeur):
    """
    Formats acceptés : ISO (AAAA-MM-JJ), JJ/MM/AAAA, '5 mars 2024'.
    JJ/MM/AAAA : le dictionnaire de données déclare ce format (jour en premier) ;
    la lecture est donc documentée et non devinée.
    'hier' : date relative, non résoluble sans date de référence -> refusée.
    Dates impossibles (32/13/2024) -> 'impossible'.
    """
    if est_vide(valeur):
        return pd.NaT, "absent"
    if isinstance(valeur, (pd.Timestamp, datetime, date)):
        return pd.Timestamp(valeur), "ok"

    txt = str(valeur).strip()
    low = cle_texte(txt)

    if low in {"hier", "avant-hier", "aujourd'hui", "aujourdhui", "demain"}:
        return pd.NaT, "relative"

    try:
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", txt):
            return pd.Timestamp(datetime.strptime(txt, "%Y-%m-%d")), "ok"
        if re.fullmatch(r"\d{2}/\d{2}/\d{4}", txt):
            return pd.Timestamp(datetime.strptime(txt, "%d/%m/%Y")), "corrige"
        m = re.fullmatch(r"(\d{1,2})\s+([a-zéèêûôîà]+)\s+(\d{4})", low)
        if m and m.group(2) in config.MOIS_FR:
            return pd.Timestamp(int(m.group(3)), config.MOIS_FR[m.group(2)], int(m.group(1))), "corrige"
    except ValueError:
        return pd.NaT, "impossible"
    return pd.NaT, "illisible"


# ------------------------------------------------------------------ catégories
def normaliser_periodicite(valeur):
    """'/mois', 'par mois', 'mensuel', 'mens.' -> 'mensuel' ; sinon None (jamais deviné)."""
    if est_vide(valeur):
        return None
    t = cle_texte(valeur)
    if re.search(r"(/\s*mois|par mois|mensuel|mens\.?$)", t):
        return "mensuel"
    if re.search(r"(/\s*trimestre|trimestriel|trim\.?$)", t):
        return "trimestriel"
    if re.search(r"(/\s*semestre|semestriel)", t):
        return "semestriel"
    if re.search(r"(/\s*an\b|par an|annuel)", t):
        return "annuel"
    return None


def normaliser_transaction(valeur):
    """-> ('vente'|'location'|None, etat)."""
    if est_vide(valeur):
        return None, "absent"
    t = cle_texte(valeur)
    if t in {"vente", "vendre", "a vendre", "achat"}:
        return "vente", "ok" if str(valeur).strip() == "vente" else "corrige"
    if t in {"location", "louer", "a louer", "loyer"}:
        return "location", "ok" if str(valeur).strip() == "location" else "corrige"
    return None, "illisible"


def deduire_transaction(source, statut):
    """
    Déduit la transaction quand elle est absente (jamais écrase une valeur présente).
    - notaires / historique : ne contiennent que des ventes (dictionnaire de données)
    - sinon d'après le statut (Loué/Disponible -> location ; En vente/Vendu... -> vente)
    """
    if source in config.SOURCES_VENTE_UNIQUEMENT:
        return "vente"
    if statut in config.STATUTS_LOCATION:
        return "location"
    if statut in config.STATUTS_VENTE:
        return "vente"
    return None


def normaliser_statut(valeur):
    if est_vide(valeur):
        return None
    cles = {cle_texte(s): s for s in config.STATUTS_CANONIQUES}
    return cles.get(cle_texte(valeur), str(valeur).strip())


# ------------------------------------------------------------------ référentiels
def charger_referentiels():
    geo = pd.read_csv(config.REF_GEO_PATH)
    cat = pd.read_csv(config.REF_CATEGORIES_PATH)

    villes = {cle_texte(v): (v, r) for v, r in zip(geo["ville"], geo["region"])}
    regions = {cle_texte(r): r for r in geo["region"].unique()}
    for alias, officiel in config.ALIAS_LIEUX.items():
        if cle_texte(officiel) in villes:
            villes[alias] = villes[cle_texte(officiel)]
        if cle_texte(officiel) in regions:
            regions[alias] = regions[cle_texte(officiel)]

    synonymes = {}
    for _, row in cat.iterrows():
        synonymes[cle_texte(row["categorie"])] = row["categorie"]
        for s in str(row["synonymes"]).split("|"):
            synonymes[cle_texte(s)] = row["categorie"]
    return {"villes": villes, "regions": regions, "synonymes": synonymes, "categories": cat}


def normaliser_type_bien(valeur, refs):
    if est_vide(valeur):
        return None, "absent"
    officiel = refs["synonymes"].get(cle_texte(valeur))
    if officiel is None:
        return str(valeur).strip(), "hors_referentiel"
    return officiel, ("ok" if officiel == str(valeur).strip() else "corrige")


def normaliser_lieu(valeur, table):
    """Ville ou région -> libellé officiel (casse/accents/alias). Inconnu : conservé tel quel."""
    if est_vide(valeur):
        return None, "absent"
    brut = re.sub(r"\s+", " ", str(valeur)).strip()
    officiel = table.get(cle_texte(brut))
    if officiel is None:
        return brut, "hors_referentiel"
    nom = officiel[0] if isinstance(officiel, tuple) else officiel
    return nom, ("ok" if nom == brut else "corrige")


# ------------------------------------------------------------------ orchestration
def nettoyer_dataframe(df):
    """
    Applique toutes les normalisations sur le DataFrame CONSOLIDÉ.
    Ajoute : colonnes nettoyées, `*_etat` (diagnostic), `*_brut` (valeurs d'origine),
    `corrections` (liste des champs reformatés par ligne).
    """
    df = df.copy()
    refs = charger_referentiels()
    n = len(df)
    corrections = [[] for _ in range(n)]

    def appliquer(colonne, fonction, nom_etat=None, brut=False):
        resultats = [fonction(v) for v in df[colonne]]
        valeurs = [r[0] for r in resultats]
        etats = [r[1] for r in resultats]
        if brut:
            df[f"{colonne}_brut"] = df[colonne]
        for i, e in enumerate(etats):
            if e == "corrige":
                corrections[i].append(colonne)
        df[colonne] = valeurs
        df[nom_etat or f"{colonne}_etat"] = etats

    # nombres et dates (on garde la valeur brute pour la traçabilité)
    appliquer("prix", normaliser_prix, brut=True)
    appliquer("surface", normaliser_surface, brut=True)
    appliquer("date", normaliser_date, brut=True)
    appliquer("date_expiration", normaliser_date)
    appliquer("chambres", normaliser_entier)
    appliquer("sdb", normaliser_entier)
    df["date"] = pd.to_datetime(df["date"])
    df["date_expiration"] = pd.to_datetime(df["date_expiration"])
    df["prix"] = pd.to_numeric(df["prix"], errors="coerce")
    df["surface"] = pd.to_numeric(df["surface"], errors="coerce")
    for col in ("chambres", "sdb"):
        df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")

    # catégories et lieux
    appliquer("type_bien", lambda v: normaliser_type_bien(v, refs))
    appliquer("region", lambda v: normaliser_lieu(v, refs["regions"]))
    appliquer("ville", lambda v: normaliser_lieu(v, refs["villes"]))
    df["statut"] = [normaliser_statut(v) for v in df["statut"]]

    # périodicité (issue de la devise 'FCFA/mois') puis transaction
    df["periodicite"] = [normaliser_periodicite(v) for v in df["devise"]]
    resultats = [normaliser_transaction(v) for v in df["type_transaction"]]
    df["type_transaction"] = [r[0] for r in resultats]
    df["type_transaction_etat"] = [r[1] for r in resultats]
    df["transaction_deduite"] = False
    for i in range(n):
        if df["type_transaction_etat"].iat[i] == "absent":
            deduite = deduire_transaction(df["source"].iat[i], df["statut"].iat[i])
            if deduite:
                df.iat[i, df.columns.get_loc("type_transaction")] = deduite
                df.iat[i, df.columns.get_loc("transaction_deduite")] = True
                corrections[i].append("type_transaction")

    df["corrections"] = [", ".join(c) for c in corrections]
    return df
