"""
Étape 2 — Harmonisation et CONCATÉNATION des sources.

1. charge les 5 sources brutes (loaders),
2. renomme leurs colonnes vers le schéma commun (config/mapping_schema.json),
3. concatène le tout en UN SEUL DataFrame, avant tout nettoyage/validation.

Chaque ligne garde sa provenance (`source`, `id_local`, `ligne_source`) et reçoit un
identifiant technique unique `id_bien`. Les identifiants locaux ne sont pas des clés
(ils peuvent être dupliqués ou contradictoires) : ils sont conservés tels quels.
"""
import json

import pandas as pd

import config
from loaders.main_loader import charger_tous_les_fichiers_bruts


def charger_et_mapper_tous_les_fichiers():
    """Charge les sources brutes et applique le mapping de colonnes de chacune."""
    with open(config.MAPPING_PATH, "r", encoding="utf-8") as f:
        mapping_schema = json.load(f)

    datasets_bruts = charger_tous_les_fichiers_bruts(config.RAW_DIR)

    datasets_mappes = {}
    for nom_source, df in datasets_bruts.items():
        if df is None or df.empty:
            continue
        if nom_source not in mapping_schema:
            raise KeyError(f"Aucun mapping défini pour la source '{nom_source}' "
                           f"dans {config.MAPPING_PATH}")
        df = df.rename(columns=mapping_schema[nom_source]).copy()
        df["source"] = nom_source
        df["ligne_source"] = range(1, len(df) + 1)
        datasets_mappes[nom_source] = df
    return datasets_mappes


def concatener_sources(datasets_mappes):
    """
    Concatène toutes les sources harmonisées en un seul DataFrame.
    Les colonnes absentes d'une source sont créées vides (jamais imputées).
    """
    morceaux = []
    for nom_source, df in datasets_mappes.items():
        d = df.copy()
        for col in config.COLONNES_STANDARD:
            if col not in d.columns:
                d[col] = pd.NA
        d = d[["source", "ligne_source"] + config.COLONNES_STANDARD]
        morceaux.append(d.astype(object))

    df_total = pd.concat(morceaux, ignore_index=True)
    df_total.insert(0, "id_bien", [f"IMM-{i:06d}" for i in range(1, len(df_total) + 1)])
    return df_total
