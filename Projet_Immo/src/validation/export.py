"""Étape 5 — Exports : données propres, quarantaine, rapport de qualité."""
import json
import os

import pandas as pd

import config

COLS_PROPRES = ["id_bien", "source", "id_local", "ligne_source", "date", "region", "ville", "quartier",
                "type_bien", "type_transaction", "transaction_deduite", "prix", "periodicite",
                "surface", "chambres", "sdb", "statut", "date_expiration",
                "statut_final", "corrections", "avertissements", "groupe_doublon"]
COLS_QUARANTAINE = ["id_bien", "source", "id_local", "ligne_source", "motifs_quarantaine",
                    "date_brut", "prix_brut", "surface_brut", "region", "ville", "type_bien",
                    "type_transaction", "chambres", "sdb", "statut"]


def _dates_iso(df):
    df = df.copy()
    for c in ("date", "date_expiration"):
        if c in df.columns:
            df[c] = df[c].dt.strftime("%Y-%m-%d")
    return df


def exporter_resultats(df_valide, metriques):
    for d in (config.PROCESSED_DIR, config.QUARANTINE_DIR, config.REPORTS_DIR):
        os.makedirs(d, exist_ok=True)

    quar = df_valide["statut_final"] == "quarantaine"
    propres = _dates_iso(df_valide.loc[~quar, COLS_PROPRES])
    quarantaine = df_valide.loc[quar, COLS_QUARANTAINE]

    chemins = {
        "propres_csv": os.path.join(config.PROCESSED_DIR, "donnees_propres.csv"),
        "propres_json": os.path.join(config.PROCESSED_DIR, "donnees_propres.json"),
        "quarantaine": os.path.join(config.QUARANTINE_DIR, "quarantaine.csv"),
        "rapport_md": os.path.join(config.REPORTS_DIR, "rapport_qualite.md"),
        "rapport_json": os.path.join(config.REPORTS_DIR, "quality_report.json"),
        "resume_csv": os.path.join(config.REPORTS_DIR, "quality_summary.csv"),
    }
    propres.to_csv(chemins["propres_csv"], index=False, encoding="utf-8")
    propres.to_json(chemins["propres_json"], orient="records", force_ascii=False, indent=2)
    quarantaine.to_csv(chemins["quarantaine"], index=False, encoding="utf-8")
    with open(chemins["rapport_json"], "w", encoding="utf-8") as f:
        json.dump(metriques, f, ensure_ascii=False, indent=2)
    pd.DataFrame(metriques["regles"]).assign(
        taux_conformite_pct=lambda t: (100 * t["conformes"] / t["evaluables"]).round(1)
    ).to_csv(chemins["resume_csv"], index=False, encoding="utf-8")
    with open(chemins["rapport_md"], "w", encoding="utf-8") as f:
        f.write(generer_rapport_md(metriques))

    print(f"\n✅ {len(propres)} lignes propres  -> {chemins['propres_csv']}")
    print(f"⚠️  {len(quarantaine)} lignes en quarantaine -> {chemins['quarantaine']}")
    print(f"📄 Rapport -> {chemins['rapport_md']}")
    return chemins


# ---------------------------------------------------------------- rapport
def _tableau(entetes, lignes):
    sortie = ["| " + " | ".join(entetes) + " |", "|" + "|".join("---" for _ in entetes) + "|"]
    sortie += ["| " + " | ".join(str(c) for c in ligne) + " |" for ligne in lignes]
    return "\n".join(sortie)


def generer_rapport_md(m):
    t = m["total_recus"]
    r = m["repartition"]
    L = ["# Rapport de qualité — ImmoAnalyse", "",
         "Traitement réalisé sur le dataset **consolidé** (concaténation des 5 sources avant "
         "nettoyage, validation et export). Les données sources n'ont pas été modifiées.", "",
         "## 1. Synthèse", "",
         _tableau(["Indicateur", "Valeur"], [
             ("Enregistrements reçus (toutes sources)", t),
             ("Retenus, entièrement conformes (ni correction, ni avertissement)", f"{r['retenu_conforme']} ({m['taux_entierement_conformes_pct']} %)"),
             ("Retenus après correction de format, sans avertissement", r["retenu_corrige"]),
             ("Retenus avec avertissement", r["retenu_avertissement"]),
             ("Mis en quarantaine", r["quarantaine"]),
             ("Dont doublons exacts", f"{m['doublons_exacts']} ({m['taux_doublons_exacts_pct']} %)"),
             ("Doublons probables signalés (non fusionnés)", f"{m['doublons_probables_lignes']} lignes en {m['doublons_probables_groupes']} groupes"),
         ]), "",
         f"*Définition du taux global : enregistrements entièrement conformes / enregistrements reçus ({t}). "
         "Les 4 catégories (quarantaine, avertissement, corrigé, conforme) sont exclusives : "
         "un enregistrement n'est compté qu'une fois, selon la priorité quarantaine > avertissement > corrigé > conforme. "
         f"Au total, {m['enregistrements_corriges']} enregistrements ont subi au moins une correction de format "
         "(y compris ceux qui ont aussi un avertissement).*", "",
         "## 2. Volumes par source", "",
         _tableau(["Source", "Reçus", "Quarantaine", "Retenus", "% retenus"],
                  [(s["source"], s["recus"], s["quarantaine"], s["retenus"], s["taux_retenus_pct"]) for s in m["par_source"]]), "",
         "## 3. Conformité par règle", "",
         "Taux = conformes / évaluables. Les lignes non évaluables sont comptées à part et ne sont pas considérées comme conformes.", "",
         _tableau(["Règle", "Évaluables (dénominateur)", "Conformes", "Non conformes", "Non évaluables", "Taux"],
                  [(x["regle"], x["evaluables"], x["conformes"], x["non_conformes"], x["non_evaluables"],
                    f"{100 * x['conformes'] / x['evaluables']:.1f} %" if x["evaluables"] else "n/a")
                   for x in m["regles"]]), "",
         "## 4. Quarantaine : motifs", "",
         "Chaque ligne en quarantaine porte ses motifs dans `data/quarantine/quarantaine.csv` (colonne `motifs_quarantaine`). "
         "Une ligne peut cumuler plusieurs motifs.", "",
         _tableau(["Motif", "Lignes"], list(m["motifs_quarantaine"].items())), "",
         "## 5. Avertissements (lignes conservées)", "",
         _tableau(["Avertissement", "Lignes"], list(m["avertissements"].items())), "",
         "## 6. Valeurs manquantes par colonne (avant nettoyage, dataset consolidé)", "",
         _tableau(["Colonne", "Manquants", "Taux"],
                  [(c, v, f"{100 * v / t:.1f} %") for c, v in m["manquants_par_colonne"].items()]), "",
         "## 7. Erreurs de conversion par champ", "",
         "Valeurs présentes mais non convertibles de façon fiable (illisible, ambigu, date impossible ou relative).", "",
         _tableau(["Champ", "Erreurs"], list(m["erreurs_conversion_par_champ"].items())), "",
         "## 8. Décisions de traitement", "",
         "- **Concaténation avant validation** : les 5 sources sont harmonisées puis réunies en un seul tableau, ce qui permet d'appliquer des règles identiques et de détecter les doublons entre sources. Chaque ligne garde `source`, `id_local` et `ligne_source`.",
         "- **Identifiants** : `id_local` n'est jamais utilisé comme clé. Un `id_bien` technique unique est généré ; un même identifiant local portant des contenus différents est signalé (`conflit_id`).",
         "- **Dates `JJ/MM/AAAA`** : lues jour en premier, conformément au dictionnaire de données ; `32/13/2024` est impossible, `hier` est relative donc refusée (quarantaine).",
         "- **Dates futures** : mises en quarantaine pour toutes les transactions (le dictionnaire de données l'exige pour les annonces ; `regles_metier.md` ne cite que les ventes — nous appliquons la règle la plus stricte).",
         "- **Prix** : `58.29 millions` → 58 290 000 (unité explicite) ; `37 965 000` et `1,250,000` → séparateurs de milliers ; `à négocier` et `quatre-vingt` → illisibles, donc quarantaine (pas de conversion de texte en lettres).",
         "- **Surfaces** : `53,0` → 53.0 ; `1,250` serait ambigu (1 250 m² ou 1,25 m²) → quarantaine, jamais deviné.",
         "- **Transaction** : valeur d'origine conservée si présente. Sinon `notaires` et `historique` = vente (par nature de la source) ; autres sources déduites du statut (`Loué`, `Disponible` → location). Ces lignes sont marquées `transaction_deduite = True`.",
         "- **Périodicité** : lue depuis la devise (`FCFA/mois` → mensuel). Absente ⇒ signalée, jamais devinée. Ventes et locations ne doivent pas être agrégées ensemble (un loyer n'est pas un prix de vente).",
         "- **Type de bien hors référentiel** : quarantaine (cahier des charges §6.1), alors que `regles_metier.md` ne prévoit qu'un avertissement. Aucun cas dans ces données.",
         "- **Doublons** : copies exactes mises en quarantaine (traçables, rien n'est supprimé) ; doublons probables signalés sans fusion (surface ±2 %, prix ±5 %, date ±30 jours, même ville, type et transaction). Seuils dans `src/config.py`.",
         "- **Fourchettes du référentiel** : prix et surface hors fourchette indicative → avertissement uniquement.", "",
         "## 9. Limites", "",
         "- Données synthétiques : ces indicateurs n'ont pas de valeur de marché.",
         "- Les prix de vente sont des prix demandés (annonces), pas nécessairement des prix de transaction.",
         "- Les seuils de plausibilité et de rapprochement sont des hypothèses pédagogiques, à valider avec le formateur sur les cas ambigus.",
         "- La déduction de la transaction à partir du statut repose sur la cohérence observée dans `plateforme_immo` et `particuliers`.",
         ]
    return "\n".join(L) + "\n"
