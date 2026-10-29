from processing.harmonizer import charger_et_mapper_tous_les_fichiers
from processing.Cleanning import nettoyer_tous_les_datasets
from validation.validation import valider_tous_les_datasets
from validation.export import exporter_resultats

if __name__ == "__main__":
    print("🚀 Démarrage du pipeline ETL Immobilier...")
    
    # 1. Étape d'ingestion et d'harmonisation (chargement via les loaders et application du mapping)
    datasets_mappes = charger_et_mapper_tous_les_fichiers()
    
    # 2. Étape de nettoyage (normalisation textuelle, types numériques et référentiels)
    datasets_nettoyes = nettoyer_tous_les_datasets(datasets_mappes)
    
    # 3. Étape de validation (règles métier bloquantes et séparation propre)
    datasets_valides, datasets_quarantaine = valider_tous_les_datasets(datasets_nettoyes)
    
    # 4. Étape d'exportation (sauvegarde des CSV dans data/processed/ et data/quarantine/)
    exporter_resultats(datasets_valides, datasets_quarantaine)
    
    print("\n✨ Pipeline ETL exécuté et exporté avec succès !")