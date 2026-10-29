# src/loaders/loader_json.py
import pandas as pd
import json
import os

def charger_json(chemin_fichier: str) -> pd.DataFrame:
    """
    Fonction utilitaire pour lire et aplatir un fichier JSON avec Pandas.
    """
    try:
        with open(chemin_fichier, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Aplatissement de la structure JSON imbriquée en DataFrame
        df = pd.json_normalize(data)
        return df
    except Exception as e:
        print(f"Erreur lors de la lecture du fichier JSON {chemin_fichier} : {e}")
        raise

def charger_source_json(nom_fichier: str = "particuliers.json", nom_source: str = "particuliers", dossier_data: str = "data/raw") -> pd.DataFrame:
    """
    Charge le fichier JSON des particuliers depuis data/raw,
    lui applique son étiquette de source, et retourne le DataFrame.
    """
    chemin_complet = os.path.join(dossier_data, nom_fichier)
    
    # Chargement et aplatissement
    df = charger_json(chemin_complet)
    
    # Ajout de la colonne de traçabilité
    df['source'] = nom_source
    
    print(f"✓ JSON '{nom_fichier}' chargé avec succès : {len(df)} lignes (source: {nom_source})")
    return df

if __name__ == "__main__":
    # Test direct du module
    charger_source_json()