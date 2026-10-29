# src/loaders/loader_excel.py
import pandas as pd
import os

def charger_excel(chemin_fichier: str, sheet_name=0) -> pd.DataFrame:
    """
    Fonction utilitaire pour lire un fichier Excel avec Pandas (nécessite openpyxl).
    """
    try:
        df = pd.read_excel(chemin_fichier, sheet_name=sheet_name)
        return df
    except Exception as e:
        print(f"Erreur lors de la lecture du fichier Excel {chemin_fichier} : {e}")
        raise

def charger_source_excel(nom_fichier: str = "agence_teranga.xlsx", nom_source: str = "agence_teranga", dossier_data: str = "data/raw", sheet_name=0) -> pd.DataFrame:
    """
    Charge le fichier Excel depuis data/raw,
    lui applique son étiquette de source, et retourne le DataFrame.
    """
    chemin_complet = os.path.join(dossier_data, nom_fichier)
    
    # Chargement du fichier Excel
    df = charger_excel(chemin_complet, sheet_name=sheet_name)
    
    # Ajout de la colonne de traçabilité
    df['source'] = nom_source
    
    print(f"✓ Excel '{nom_fichier}' chargé avec succès : {len(df)} lignes (source: {nom_source})")
    return df

if __name__ == "__main__":
    # Test direct du module
    charger_source_excel()