import os
import pandas as pd

# ==========================================
# CONFIGURATION DES CHEMINS (PATHS)
# ==========================================
DATA_RAW_DIR = "data/raw"
REF_CATEGORIES_PATH = os.path.join(DATA_RAW_DIR, "referentiel_categories.csv")
REF_GEO_PATH = os.path.join(DATA_RAW_DIR, "referentiel_geographique.csv")


def charger_referentiels():
    """Charge les deux fichiers référentiels depuis data/raw/"""
    refs = {}
    if os.path.exists(REF_CATEGORIES_PATH):
        refs["categories"] = pd.read_csv(REF_CATEGORIES_PATH)
    if os.path.exists(REF_GEO_PATH):
        refs["geo"] = pd.read_csv(REF_GEO_PATH)
    return refs


def nettoyer_dataset(df, source_name):
    """
    Applique uniquement le nettoyage, la normalisation textuelle, 
    la conversion des types et l'utilisation des deux référentiels.
    """
    if df is None or df.empty:
        return df

    df = df.copy()

    # Chargement des référentiels
    refs = charger_referentiels()
    cat_df = refs.get("categories", pd.DataFrame())
    geo_df = refs.get("geo", pd.DataFrame())

    # 1. Normalisation textuelle de base (casse et espaces)
    for col in ["region", "ville", "type_bien", "statut"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip().str.capitalize()

    # 2. Normalisation des types de biens via le référentiel des catégories et synonymes
    if not cat_df.empty and "type_bien" in df.columns:
        syn_map = {}
        for _, row in cat_df.iterrows():
            cat = row["categorie"]
            syns = str(row["synonymes"]).split("|")
            for s in syns:
                syn_map[s.strip().lower()] = cat
        
        df["type_bien"] = df["type_bien"].str.lower().map(syn_map).fillna(df["type_bien"])

    # 3. Normalisation / Alignement géographique via le référentiel géographique
    # (Par exemple, s'assurer que les noms de villes correspondent exactement à l'officiel si nécessaire)
    if not geo_df.empty and "ville" in df.columns:
        # Création d'un dictionnaire de correspondance insensible à la casse
        villes_officielles = {v.strip().lower(): v for v in geo_df["ville"].dropna()}
        df["ville"] = df["ville"].str.lower().map(villes_officielles).fillna(df["ville"])

    # 4. Conversion et nettoyage des champs numériques (prix, surface)
    if "prix" in df.columns:
        df["prix"] = pd.to_numeric(df["prix"], errors="coerce")
    if "surface" in df.columns:
        df["surface"] = pd.to_numeric(df["surface"], errors="coerce")

    # Maintien de la traçabilité de la source
    df["source"] = source_name

    return df


def nettoyer_tous_les_datasets(datasets_mappes):
    """
    Parcourt le dictionnaire des DataFrames harmonisés et applique 
    le nettoyage sur chacun d'eux en mémoire.
    """
    datasets_nettoyes = {}
    
    for nom_source, df in datasets_mappes.items():
        df_nettoye = nettoyer_dataset(df, nom_source)
        datasets_nettoyes[nom_source] = df_nettoye
        print(f"🧹 Nettoyé : {nom_source} | Shape : {df_nettoye.shape}")
        
    return datasets_nettoyes