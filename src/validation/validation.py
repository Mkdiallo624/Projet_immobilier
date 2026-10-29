import os
import pandas as pd

# ==========================================
# CONFIGURATION DES CHEMINS (PATHS)
# ==========================================
DATA_RAW_DIR = "data/raw"
REF_GEO_PATH = os.path.join(DATA_RAW_DIR, "referentiel_geographique.csv")
REF_CATEGORIES_PATH = os.path.join(DATA_RAW_DIR, "referentiel_categories.csv")


def charger_referentiel_geo():
    """Charge le référentiel géographique officiel."""
    if os.path.exists(REF_GEO_PATH):
        return pd.read_csv(REF_GEO_PATH)
    return pd.DataFrame()


def charger_referentiel_categories():
    """Charge le référentiel des catégories de biens."""
    if os.path.exists(REF_CATEGORIES_PATH):
        return pd.read_csv(REF_CATEGORIES_PATH)
    return pd.DataFrame()


def valider_dataset(df, source_name):
    """
    Applique les règles de validation bloquantes (quarantaine) et vérifie 
    les référentiels géographiques et de catégories.
    """
    if df is None or df.empty:
        return pd.DataFrame(), pd.DataFrame(), {}

    df = df.copy()

    # Masque pour identifier les lignes en erreur (bloquantes -> Quarantaine)
    invalides = pd.Series(False, index=df.index)
    
    metrics = {
        "total_lignes": len(df),
        "erreurs_id": 0,
        "erreurs_prix": 0,
        "erreurs_surface": 0,
        "erreurs_date": 0,
        "avertissements_geo": 0,
        "avertissements_categorie": 0
    }

    # ==========================================
    # 1. RÈGLES BLOQUANTES (Direction Quarantaine)
    # ==========================================
    
    # - Identifiant absent
    id_col = "id_bien" if "id_bien" in df.columns else ("ref_plateforme" if "ref_plateforme" in df.columns else None)
    if id_col:
        id_missing = df[id_col].isnull() | (df[id_col].astype(str).str.strip() == "")
        invalides |= id_missing
        metrics["erreurs_id"] = int(id_missing.sum())

    # - Prix absent, non numérique ou <= 0
    if "prix" in df.columns:
        prix_num = pd.to_numeric(df["prix"], errors="coerce")
        prix_invalide = prix_num.isnull() | (prix_num <= 0)
        invalides |= prix_invalide
        metrics["erreurs_prix"] = int(prix_invalide.sum())

    # - Surface absente, non numérique ou <= 0
    if "surface" in df.columns:
        surf_num = pd.to_numeric(df["surface"], errors="coerce")
        surf_invalide = surf_num.isnull() | (surf_num <= 0)
        invalides |= surf_invalide
        metrics["erreurs_surface"] = int(surf_invalide.sum())

    # - Date non interprétable ou future si vendu
    if "date" in df.columns:
        dates_parsed = pd.to_datetime(df["date"], errors="coerce", dayfirst=True)
        date_invalide = dates_parsed.isnull()
        
        if "statut" in df.columns:
            est_vendu = df["statut"].astype(str).str.strip().str.lower().str.contains("vendu")
            date_future_vendu = est_vendu & (dates_parsed > pd.Timestamp.now())
            date_invalide |= date_future_vendu

        invalides |= date_invalide
        metrics["erreurs_date"] = int(date_invalide.sum())

    # ==========================================
    # 2. CONTRÔLES VIA LES RÉFÉRENTIELS (Géo & Catégories)
    # ==========================================
    
    # - Contrôle géographique (referentiel_geographique.csv)
    ref_geo = charger_referentiel_geo()
    if not ref_geo.empty and "ville" in df.columns:
        villes_officielles = set(ref_geo["ville"].astype(str).str.strip().str.lower())
        ville_inconnue = df["ville"].notnull() & (~df["ville"].astype(str).str.strip().str.lower().isin(villes_officielles))
        metrics["avertissements_geo"] = int(ville_inconnue.sum())

    # - Contrôle des catégories de biens (referentiel_categories.csv)
    ref_cat = charger_referentiel_categories()
    if not ref_cat.empty and "type_bien" in df.columns:
        categories_officielles = set(ref_cat["categorie"].astype(str).str.strip().str.lower())
        cat_inconnue = df["type_bien"].notnull() & (~df["type_bien"].astype(str).str.strip().str.lower().isin(categories_officielles))
        metrics["avertissements_categorie"] = int(cat_inconnue.sum())

    # ==========================================
    # 3. SÉPARATION FINALE
    # ==========================================
    df_valide = df[~invalides].copy()
    df_quarantaine = df[invalides].copy()

    # Traçabilité de la source
    df_valide["source"] = source_name
    df_quarantaine["source"] = source_name

    return df_valide, df_quarantaine, metrics


def valider_tous_les_datasets(datasets_nettoyes):
    """
    Parcourt tous les datasets nettoyés, applique la validation 
    et retourne les dictionnaires de DataFrames valides et en quarantaine.
    """
    datasets_valides = {}
    datasets_quarantaine = {}

    print("\n================ RAPPORT DE VALIDATION MÊTIER ================")
    for nom_source, df in datasets_nettoyes.items():
        df_val, df_quar, metrics = valider_dataset(df, nom_source)
        datasets_valides[nom_source] = df_val
        datasets_quarantaine[nom_source] = df_quar
        
        print(f"\n📁 Source : {nom_source}")
        print(f"   - Total lignes : {metrics['total_lignes']}")
        print(f"   - ✅ Valides : {len(df_val)}")
        print(f"   - ⚠️ Quarantaine : {len(df_quar)} "
              f"(ID: {metrics['erreurs_id']}, Prix: {metrics['erreurs_prix']}, "
              f"Surface: {metrics['erreurs_surface']}, Date: {metrics['erreurs_date']})")
        print(f"   - ℹ️ Avertissements -> Villes inconnues : {metrics['avertissements_geo']} | Types atypiques : {metrics['avertissements_categorie']}")

    print("===============================================================\n")
    return datasets_valides, datasets_quarantaine