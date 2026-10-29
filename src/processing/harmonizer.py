import json
# Importez vos fonctions de chargement depuis le dossier loaders
from loaders.main_loader import charger_tous_les_fichiers_bruts  # (ou l'équivalent selon vos fonctions)

def charger_et_mapper_tous_les_fichiers():
    # 1. Charger le mapping global depuis config
    config_path = "config/mapping_schema.json"
    with open(config_path, "r", encoding="utf-8") as f:
        mapping_schema = json.load(f)
    
    # 2. Récupérer les DataFrames bruts via vos loaders modulaires
    datasets_bruts = charger_tous_les_fichiers_bruts()
    
    datasets_traites = {}
    
    # 3. Appliquer le mapping des colonnes sur chaque dataset brut
    for nom_source, df in datasets_bruts.items():
        if df is not None and not df.empty:
            # Récupérer le schéma de mapping correspondant à la source
            schema_mapping = mapping_schema.get(nom_source, {})
            
            # Renommer les colonnes selon le schéma
            df = df.rename(columns=schema_mapping)
            
            # Ajouter la traçabilité de la source
            df["source"] = nom_source
            datasets_traites[nom_source] = df
            
    return datasets_traites