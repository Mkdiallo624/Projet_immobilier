"""
Étape 4 — Validation métier sur le dataset CONSOLIDÉ.

Trois niveaux de gravité (regles_metier.md) :
  - BLOQUANT      -> quarantaine, avec le(s) motif(s) de chaque ligne
  - CORRIGÉ       -> normalisation fiable déjà appliquée (cleaning.py)
  - AVERTISSEMENT -> ligne conservée et signalée

Chaque règle est comptée avec son dénominateur (lignes évaluables) ; les lignes non
évaluables sont comptées à part et jamais considérées comme conformes.
"""
import pandas as pd

import config
from processing.cleaning import charger_referentiels, est_vide
from validation import doublons

ETATS_NUM_OK = {"ok", "corrige"}


def _liste_vide(index):
    return pd.Series([[] for _ in index], index=index, dtype="object")


def _ajouter(listes, masque, code):
    for i in masque[masque].index:
        listes.at[i].append(code)


def valider_dataframe(df, aujourd_hui=None):
    """
    Entrée  : DataFrame consolidé et normalisé (sortie de nettoyer_dataframe).
    Sortie  : (df_enrichi, regles) où df_enrichi porte `motifs_quarantaine`,
              `avertissements`, `groupe_doublon`, `statut_final`, et `regles` est la
              table de conformité par règle.
    """
    df = df.copy()
    aujourd_hui = pd.Timestamp(aujourd_hui or pd.Timestamp.now().normalize())
    refs = charger_referentiels()
    cat = refs["categories"].set_index("categorie")
    idx = df.index
    motifs, avert = _liste_vide(idx), _liste_vide(idx)
    regles = []

    def regle(nom, evaluable, conforme):
        evaluable = evaluable.astype(bool)
        conforme = conforme.astype(bool) & evaluable
        regles.append({
            "regle": nom,
            "evaluables": int(evaluable.sum()),
            "conformes": int(conforme.sum()),
            "non_conformes": int((evaluable & ~conforme).sum()),
            "non_evaluables": int((~evaluable).sum()),
        })

    tout = pd.Series(True, index=idx)

    # ======================= 1. RÈGLES BLOQUANTES =======================
    id_ok = ~df["id_local"].map(est_vide)
    regle("identifiant local présent", tout, id_ok)
    _ajouter(motifs, ~id_ok, "id_absent")

    for champ, etat_col in (("prix", "prix_etat"), ("surface", "surface_etat")):
        etat = df[etat_col]
        positif = df[champ] > 0
        regle(f"{champ} numérique", tout, etat.isin(ETATS_NUM_OK))
        regle(f"{champ} > 0", etat.isin(ETATS_NUM_OK), positif.fillna(False))
        _ajouter(motifs, etat == "absent", f"{champ}_absent")
        _ajouter(motifs, etat == "illisible", f"{champ}_illisible")
        _ajouter(motifs, etat == "ambigu", f"{champ}_ambigu")
        _ajouter(motifs, etat.isin(ETATS_NUM_OK) & ~positif.fillna(False), f"{champ}_non_positif")

    etat_d = df["date_etat"]
    regle("date interprétable", tout, etat_d.isin(ETATS_NUM_OK))
    regle("date non future", etat_d.isin(ETATS_NUM_OK), df["date"] <= aujourd_hui)
    _ajouter(motifs, etat_d == "absent", "date_absente")
    _ajouter(motifs, etat_d == "impossible", "date_impossible")
    _ajouter(motifs, etat_d == "relative", "date_relative")
    _ajouter(motifs, etat_d == "illisible", "date_illisible")
    _ajouter(motifs, etat_d.isin(ETATS_NUM_OK) & (df["date"] > aujourd_hui), "date_future")

    trans_ok = df["type_transaction"].isin(["vente", "location"])
    regle("type_transaction renseigné ou déductible", tout, trans_ok)
    _ajouter(motifs, ~trans_ok, "transaction_non_interpretable")

    t_etat = df["type_bien_etat"]
    regle("type_bien dans le référentiel", t_etat != "absent", t_etat.isin({"ok", "corrige"}))
    _ajouter(motifs, t_etat == "absent", "type_bien_absent")
    _ajouter(motifs, t_etat == "hors_referentiel", "type_bien_hors_referentiel")

    copies = doublons.marquer_doublons_exacts(df)
    regle("pas de doublon exact", tout, ~copies)
    _ajouter(motifs, copies, "doublon_exact")

    # ======================= 2. AVERTISSEMENTS =======================
    vente = df["type_transaction"] == "vente"
    location = df["type_transaction"] == "location"
    prix, surf = df["prix"], df["surface"]
    p_ok, s_ok = prix > 0, surf > 0

    atyp_s = s_ok & ((surf < config.SURFACE_ATYPIQUE_MIN) | (surf > config.SURFACE_ATYPIQUE_MAX))
    regle("surface plausible", s_ok, ~atyp_s)
    _ajouter(avert, atyp_s, "surface_atypique")

    atyp_v = vente & p_ok & ((prix < config.PRIX_VENTE_ATYPIQUE_MIN) | (prix > config.PRIX_VENTE_ATYPIQUE_MAX))
    regle("prix de vente plausible", vente & p_ok, ~atyp_v)
    _ajouter(avert, atyp_v, "prix_vente_atypique")

    # le loyer n'est comparable qu'à une périodicité mensuelle (ou inconnue, signalée plus bas)
    loyer_eval = location & p_ok & df["periodicite"].isin(["mensuel"]) | (location & p_ok & df["periodicite"].isna())
    atyp_l = loyer_eval & ((prix < config.LOYER_ATYPIQUE_MIN) | (prix > config.LOYER_ATYPIQUE_MAX))
    regle("loyer plausible", loyer_eval, ~atyp_l)
    _ajouter(avert, atyp_l, "loyer_atypique")
    _ajouter(avert, location & df["periodicite"].isna(), "periodicite_inconnue")

    # géographie : on signale, on ne corrige jamais sans preuve
    ville_connue = df["ville_etat"].isin({"ok", "corrige"})
    _ajouter(avert, df["ville_etat"] == "absent", "ville_absente")
    _ajouter(avert, df["ville_etat"] == "hors_referentiel", "ville_hors_referentiel")
    _ajouter(avert, df["region_etat"] == "absent", "region_absente")
    _ajouter(avert, df["region_etat"] == "hors_referentiel", "region_hors_referentiel")
    ref_region = {nom: reg for nom, reg in refs["villes"].values()}
    reg_attendue = df["ville"].map(ref_region)
    coherence_eval = ville_connue & df["region_etat"].isin({"ok", "corrige"})
    incoh = coherence_eval & (reg_attendue != df["region"])
    regle("région cohérente avec la ville", coherence_eval, ~incoh)
    _ajouter(avert, incoh, "region_ville_incoherente")

    # fourchettes indicatives du référentiel de catégories
    for col_min, col_max, champ, nom_regle, code in (
        ("prix_min_indicatif", "prix_max_indicatif", "prix", "prix dans la fourchette de la catégorie", "prix_hors_fourchette_categorie"),
        ("surface_min_typique", "surface_max_typique", "surface", "surface dans la fourchette de la catégorie", "surface_hors_fourchette_categorie"),
    ):
        bas, haut = df["type_bien"].map(cat[col_min]), df["type_bien"].map(cat[col_max])
        valeur = df[champ]
        eval_ = (valeur > 0) & bas.notna() & (vente if champ == "prix" else tout)
        hors = eval_ & ((valeur < bas) | (valeur > haut))
        regle(nom_regle, eval_, ~hors)
        _ajouter(avert, hors, code)

    # cohérence chambres / salles de bain / type de bien
    ch, sd = df["chambres"], df["sdb"]
    compact = df["type_bien"].isin(["Appartement", "Studio"])
    trop = (ch > config.CHAMBRES_MAX_APPART_STUDIO).fillna(False) & compact
    _ajouter(avert, trop, "chambres_atypique")
    sdb_exc = (sd > ch + config.SDB_MARGE_SUR_CHAMBRES).fillna(False)
    _ajouter(avert, sdb_exc, "sdb_superieur_chambres_plus_2")
    terrain_bati = (df["type_bien"] == "Terrain") & (((ch > 0).fillna(False)) | ((sd > 0).fillna(False)))
    _ajouter(avert, terrain_bati, "terrain_avec_chambres")
    _ajouter(avert, (ch < 0).fillna(False) | (sd < 0).fillna(False), "nombre_negatif")
    regle("chambres/sdb cohérentes", ch.notna() & sd.notna(), ~(trop | sdb_exc | terrain_bati))

    # cohérence transaction / statut / devise
    incoh_statut = (location & df["statut"].isin(config.STATUTS_VENTE)) | (vente & df["statut"].isin(config.STATUTS_LOCATION))
    _ajouter(avert, incoh_statut & ~df["transaction_deduite"], "transaction_incoherente_statut")
    dev = df["devise"].astype("string").str.lower().fillna("")
    _ajouter(avert, (location & dev.eq("fcfa")) | (vente & dev.str.contains("mois")), "devise_incoherente")
    exp_ant = df["date_expiration"].notna() & df["date"].notna() & (df["date_expiration"] < df["date"])
    _ajouter(avert, exp_ant, "date_expiration_anterieure")

    # conflits d'identifiant
    conflit = doublons.marquer_conflits_id(df, copies)
    _ajouter(avert, conflit, "conflit_id")

    # ======================= 3. STATUT FINAL =======================
    df["motifs_quarantaine"] = motifs.map(lambda l: "; ".join(l))
    en_quarantaine = df["motifs_quarantaine"] != ""

    # doublons probables : calculés uniquement entre lignes retenues
    retenues = df[~en_quarantaine]
    groupes = doublons.trouver_doublons_probables(retenues)
    df["groupe_doublon"] = groupes.reindex(df.index)
    _ajouter(avert, df["groupe_doublon"].notna(), "doublon_probable")

    df["avertissements"] = avert.map(lambda l: "; ".join(l))
    a_avert = (df["avertissements"] != "") & ~en_quarantaine
    corrige = df["corrections"] != ""
    df["statut_final"] = "retenu_conforme"
    df.loc[corrige, "statut_final"] = "retenu_corrige"
    df.loc[a_avert, "statut_final"] = "retenu_avertissement"
    df.loc[en_quarantaine, "statut_final"] = "quarantaine"
    return df, pd.DataFrame(regles)
