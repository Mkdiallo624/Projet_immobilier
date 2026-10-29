import os
# Utilisation d'imports relatifs pour cibler les fichiers dans le même dossier
from .loader_csv import charger_tous_les_csv
from .loader_json import charger_source_json
from .loader_xlsx import charger_source_excel

def charger_tous_les_fichiers_bruts(dossier_data: str = "data/raw") -> dict:
    """
    Orchestre le chargement de toutes les sources hétérogènes (CSV, JSON, Excel)
    depuis le dossier data/raw et retourne un dictionnaire de DataFrames bruts.
    """
    print("\n🚀 Démarrage du chargement global des fichiers bruts...")
    
    datasets_bruts = {}

    try:
        # 1. Chargement des sources CSV (notaires, historique, plateforme_immo)
        csv_data = charger_tous_les_csv(dossier_data)
        datasets_bruts.update(csv_data)

        # 2. Chargement de la source JSON (particuliers)
        df_json = charger_source_json(nom_fichier="particuliers.json", nom_source="particuliers", dossier_data=dossier_data)
        datasets_bruts["particuliers"] = df_json

        # 3. Chargement de la source Excel (agence_teranga)
        # Note : On précise la feuille "Annonces" si c'est celle utilisée dans votre projet
        df_excel = charger_source_excel(nom_fichier="agence_teranga.xlsx", nom_source="agence_teranga", dossier_data=dossier_data, sheet_name="Annonces")
        datasets_bruts["agence_teranga"] = df_excel

        print(f"✨ Chargement terminé avec succès ! {len(datasets_bruts)} sources chargées.\n")

    except Exception as e:
        print(f"❌ Erreur critique lors du chargement des sources : {e}")
        raise

    return datasets_bruts

if __name__ == "__main__":
    # Test direct du module de chargement global
    charger_tous_les_fichiers_bruts()