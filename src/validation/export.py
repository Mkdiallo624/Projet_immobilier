import os
import pandas as pd

# ==========================================
# CONFIGURATION DES CHEMINS DE SORTIE
# ==========================================
PROCESSED_DIR = "data/processed"
QUARANTINE_DIR = "data/quarantine"


def exporter_resultats(datasets_valides, datasets_quarantaine):
    """
    Exporte les DataFrames valides vers data/processed/ 
    et les DataFrames en quarantaine vers data/quarantine/ sous format CSV.
    """
    # S'assurer que les dossiers de destination existent
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    os.makedirs(QUARANTINE_DIR, exist_ok=True)

    # 1. Export des données valides
    print("\n--- 📁 Exportation des données valides (processed) ---")
    for nom_source, df in datasets_valides.items():
        if df is not None and not df.empty:
            out_path = os.path.join(PROCESSED_DIR, f"{nom_source}_valide.csv")
            df.to_csv(out_path, index=False, encoding="utf-8")
            print(f"✅ Sauvegardé : {out_path} ({len(df)} lignes)")
        else:
            print(f"ℹ️ Aucun enregistrement valide pour : {nom_source}")

    # 2. Export des données en quarantaine
    print("\n--- ⚠️ Exportation des données en quarantaine (quarantine) ---")
    for nom_source, df in datasets_quarantaine.items():
        if df is not None and not df.empty:
            out_path = os.path.join(QUARANTINE_DIR, f"{nom_source}_quarantaine.csv")
            df.to_csv(out_path, index=False, encoding="utf-8")
            print(f"⚠️ Quarantaine : {out_path} ({len(df)} lignes)")
        else:
            print(f"✨ Aucune anomalie pour : {nom_source} (Quarantaine vide)")