"""
Orchestrateur du pipeline ETL ImmoAnalyse.   Usage : python src/main.py   (depuis la racine du projet)

Ingestion -> Harmonisation -> CONCATÉNATION -> Nettoyage -> Validation -> Export
"""
from processing.harmonizer import charger_et_mapper_tous_les_fichiers, concatener_sources
from processing.cleaning import nettoyer_dataframe
from validation.validation import valider_dataframe
from validation.export import exporter_resultats
from analysis.qualite import calculer_metriques

if __name__ == "__main__":
    print("Démarrage du pipeline ETL Immobilier...")

    # 1. Ingestion + harmonisation des colonnes, source par source
    datasets_mappes = charger_et_mapper_tous_les_fichiers()

    # 2. Concaténation : UN SEUL dataset, avant tout nettoyage / validation / export
    df_consolide = concatener_sources(datasets_mappes)
    print(f"\n Dataset consolidé : {len(df_consolide)} lignes issues de {len(datasets_mappes)} sources")

    # 3. Normalisation (formats, synonymes, référentiels) sur le dataset consolidé
    df_normalise = nettoyer_dataframe(df_consolide)

    # 4. Validation métier + détection des doublons
    df_valide, regles = valider_dataframe(df_normalise)

    # 5. Indicateurs de qualité + exports (données propres, quarantaine, rapport)
    metriques = calculer_metriques(df_consolide, df_valide, regles)
    exporter_resultats(df_valide, metriques)

    print("\n Pipeline exécuté de bout en bout.")
