"""Indicateurs de qualité (cahier des charges, §7) calculés sur le dataset consolidé."""
import pandas as pd

from processing.cleaning import est_vide

ETATS_ERREUR = {"illisible", "ambigu", "impossible", "relative"}


def calculer_metriques(df_consolide, df_valide, regles):
    """
    df_consolide : dataset concaténé AVANT nettoyage (pour les manquants d'origine)
    df_valide    : dataset normalisé + colonnes de validation (valider_dataframe)
    regles       : table de conformité par règle
    """
    total = len(df_valide)
    statuts = df_valide["statut_final"].value_counts()
    cat = {k: int(statuts.get(k, 0)) for k in
           ("quarantaine", "retenu_avertissement", "retenu_corrige", "retenu_conforme")}

    manquants = {c: int(df_consolide[c].map(est_vide).sum())
                 for c in df_consolide.columns if c not in ("id_bien", "source", "ligne_source")}

    erreurs_conversion = {}
    for champ, col in (("prix", "prix_etat"), ("surface", "surface_etat"), ("date", "date_etat"),
                       ("date_expiration", "date_expiration_etat"), ("chambres", "chambres_etat"),
                       ("sdb", "sdb_etat"), ("type_transaction", "type_transaction_etat")):
        erreurs_conversion[champ] = int(df_valide[col].isin(ETATS_ERREUR).sum())

    nb_copies = int(df_valide["motifs_quarantaine"].str.contains("doublon_exact").sum())
    motifs = df_valide.loc[df_valide["motifs_quarantaine"] != "", "motifs_quarantaine"] \
        .str.split("; ").explode().value_counts()
    avert = df_valide.loc[df_valide["statut_final"] != "quarantaine", "avertissements"]
    avert = avert[avert != ""].str.split("; ").explode().value_counts()

    par_source = []
    for src, g in df_valide.groupby("source", sort=False):
        q = int((g["statut_final"] == "quarantaine").sum())
        par_source.append({"source": src, "recus": len(g), "quarantaine": q,
                           "retenus": len(g) - q,
                           "taux_retenus_pct": round(100 * (len(g) - q) / len(g), 1)})

    return {
        "total_recus": total,
        "par_source": par_source,
        "repartition": cat,
        "enregistrements_corriges": int((df_valide["corrections"] != "").sum()),
        "enregistrements_quarantaine": cat["quarantaine"],
        "enregistrements_conserves_avec_avertissement": cat["retenu_avertissement"],
        "enregistrements_entierement_conformes": cat["retenu_conforme"],
        "taux_entierement_conformes_pct": round(100 * cat["retenu_conforme"] / total, 1),
        "doublons_exacts": nb_copies,
        "taux_doublons_exacts_pct": round(100 * nb_copies / total, 2),
        "doublons_probables_lignes": int(df_valide["groupe_doublon"].notna().sum()),
        "doublons_probables_groupes": int(df_valide["groupe_doublon"].nunique()),
        "manquants_par_colonne": manquants,
        "erreurs_conversion_par_champ": erreurs_conversion,
        "motifs_quarantaine": {k: int(v) for k, v in motifs.items()},
        "avertissements": {k: int(v) for k, v in avert.items()},
        "regles": regles.to_dict(orient="records"),
    }
