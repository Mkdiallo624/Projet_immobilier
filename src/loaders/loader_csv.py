# src/loaders/loader_csv.py
import pandas as pd
import os

def charger_csv(chemin_fichier: str, sep: str = ';', encoding: str = 'latin1') -> pd.DataFrame:
    """
    Fonction utilitaire pour lire un fichier CSV avec Pandas.
    """
    return pd.read_csv(chemin_fichier, sep=sep, encoding=encoding)

def charger_tous_les_csv(dossier_data: str = "data/raw") -> dict:
    """
    Charge les trois fichiers CSV du projet depuis data/raw 
    et leur ajoute une colonne de traçabilité 'source'.
    """
    print("--- Chargement des fichiers CSV ---")
    
    # 1. Fichier notaires.csv (souvent en UTF-8 avec un séparateur virgule)
    chemin_notaires = os.path.join(dossier_data, "notaires.csv")
    df_notaires = charger_csv(chemin_notaires, sep=',', encoding='utf-8')
    df_notaires['source'] = 'notaires'
    print(f"✓ Notaires chargés : {len(df_notaires)} lignes")

    # 2. Fichier import_historique.csv
    chemin_historique = os.path.join(dossier_data, "import_historique.csv")
    df_historique = charger_csv(chemin_historique, sep=';', encoding='latin1')
    df_historique['source'] = 'historique'
    print(f"✓ Historique chargé : {len(df_historique)} lignes")

    # 3. Fichier plateforme_immo_sn.csv
    chemin_plateforme = os.path.join(dossier_data, "plateforme_immo_sn.csv")
    df_plateforme = charger_csv(chemin_plateforme, sep=';', encoding='latin1')
    df_plateforme['source'] = 'plateforme_immo'
    print(f"✓ Plateforme Immo chargée : {len(df_plateforme)} lignes")

    print("-----------------------------------")
    
    return {
        "notaires": df_notaires,
        "historique": df_historique,
        "plateforme_immo": df_plateforme
    }

if __name__ == "__main__":
    # Test direct du module
    charger_tous_les_csv()