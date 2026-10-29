# Pipeline ETL Immobilier Modulaire

Bienvenue dans le dépôt du **Pipeline ETL Immobilier**. Ce projet en Python propose une solution modulaire, robuste et maintenable pour l'ingestion, l'harmonisation, le nettoyage, la validation métier et l'exportation de données immobilières issues de sources très hétérogènes (CSV, Excel et JSON).

---

## VUE D'ENSEMBLE DU SYSTEME

Le pipeline a pour objectif d'absorber des flux de données divers provenant de 5 sources (agences, plateformes web, notaires et particuliers) et de les convertir en un jeu de données unifié, nettoyé et contrôlé.

```
┌────────────────────────────────────────────────────────────────────────┐
│                        DATA RAW (Fichiers Bruts)                      │
│   CSV (notaires, historique, plateforme) | XLSX (teranga) | JSON (part)│
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ 1. INGESTION (src/loaders/)                                            │
│    Lectures spécialisées par format (CSV, JSON, Excel)                 │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ 2. HARMONISATION (src/processing/harmonizer.py)                       │
│    Mapping global des colonnes via mapping_schema.json                 │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ 3. NETTOYAGE (src/processing/Cleanning.py)                             │
│    Normalisation du texte, conversions numériques & typologie           │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ 4. VALIDATION MÉTIER (src/validation/validation.py)                    │
│    Contrôle de conformité + Référentiels Géo & Catégories             │
└─────────────────┬──────────────────────────────────────┬───────────────┘
                  │                                      │
         [Lignes Valides]                        [Lignes Invalides]
                  │                                      │
                  ▼                                      ▼
┌───────────────────────────────────┐  ┌─────────────────────────────────┐
│ 5. EXPORT PROCESSED               │  │ 5. EXPORT QUARANTINE            │
│    data/processed/*_valide.csv    │  │    data/quarantine/*_quar.csv   │
└───────────────────────────────────┘  └─────────────────────────────────┘
```

---

## STRUCTURE DU PROJET

Le projet suit les principes de la **Séparation des Responsabilités (Separation of Concerns)**.

```text
Projet_Immo/
│
├── config/
│   └── mapping_schema.json         # Correspondances des entêtes de chaque source
│
├── data/
│   ├── raw/                        # Fichiers bruts & Référentiels
│   │   ├── agence_teranga.xlsx
│   │   ├── import_historique.csv
│   │   ├── notaires.csv
│   │   ├── particuliers.json
│   │   ├── plateforme_immo_sn.csv
│   │   ├── referentiel_categories.csv
│   │   └── referentiel_geographique.csv
│   │
│   ├── processed/                  # Résultats des données valides (.csv)
│   └── quarantine/                 # Résultats des données invalides (.csv)
│
├── src/
│   ├── loaders/                    # Modules d'ingestion technique
│   │   ├── __init__.py
│   │   ├── loader_csv.py           # Lecture personnalisée des fichiers CSV
│   │   ├── loader_json.py          # Lecture & aplatissement des structures JSON
│   │   ├── loader_xlsx.py          # Lecture des feuilles de calcul Excel
│   │   └── main_loader.py          # Centralisation du chargement des sources
│   │
│   ├── processing/                 # Traitement & transformation des données
│   │   ├── __init__.py
│   │   ├── harmonizer.py           # Standardisation des schémas de colonnes
│   │   └── Cleanning.py            # Nettoyage, types & référentiels typologiques
│   │
│   ├── validation/                 # Validation & Exportation
│   │   ├── __init__.py
│   │   ├── validation.py           # Contrôles métier & quarantaine
│   │   └── export.py               # Enregistrement sur le disque
│   │
│   └── main.py                     # Orchestrateur principal du pipeline ETL
│
├── requirements.txt                # Liste des dépendances Python
└── README.md                       # Documentation officielle
```

---

## DESCRIPTION DES MODULES

### 1. Ingestion (`src/loaders/`)
* **`loader_csv.py`** : Lit les fichiers CSV en gérant dynamiquement les encodages (`latin1`, `utf-8`) et les séparateurs (`;`, `,`).
* **`loader_json.py`** : Extrait et aplatit les données hiérarchiques (clés imbriquées telles que `localisation` ou `details`) en tables plates à l'aide de `pandas.json_normalize`.
* **`loader_xlsx.py`** : Lit la feuille appropriée (ex: `Annonces`) du fichier Excel `agence_teranga.xlsx`.
* **`main_loader.py`** : Appelle l'ensemble des loaders et retourne un dictionnaire global `dict[str, DataFrame]` contenant toutes les sources chargées.

### 2. Harmonisation & Nettoyage (`src/processing/`)
* **`harmonizer.py`** : Applique les règles définies dans `config/mapping_schema.json` pour renommer les colonnes d'origine vers des entêtes uniformes (`id_bien`, `date`, `region`, `ville`, `type_bien`, `prix`, `surface`, `chambres`, `sdb`, `statut`).
* **`Cleanning.py`** : 
  - Nettoie les espaces inutiles et normalise le texte en majuscules/minuscules.
  - Convertit les types numériques (`prix`, `surface`, `chambres`, `sdb`).
  - Mappe les termes invalides ou synonymes (via `referentiel_categories.csv`).

### 3. Validation & Isolation (`src/validation/`)
* **`validation.py`** : Évalue chaque ligne par rapport à des règles métier bloquantes :
  - Identifiant unique présent et non vide.
  - Prix strict positif ($Prix > 0$).
  - Surface stricte positive ($Surface > 0$).
  - Format de date valide.
  - Contrôle géographique indicatif via `referentiel_geographique.csv`.
  - Sépare les enregistrements en deux catégories : **Valides** et **Quarantaine**.
* **`export.py`** : Exporte les DataFrames résultants au format CSV encodé en UTF-8 dans les dossiers `data/processed/` et `data/quarantine/`.

---

## INSTALLATION ET EXÉCUTION

### Préréquis
- Python 3.9 ou version supérieure.
- Un environnement virtuel configuré.

### 1. Installation des dépendances
Activez votre environnement virtuel puis installez les bibliothèques requises :

```bash
# Activation de l'environnement virtuel (Linux / macOS)
source mon_env/bin/activate

# Installation des dépendances
pip install -r requirements.txt
```

### 2. Lancement du Pipeline ETL
Pour exécuter l'ensemble de la chaîne de traitement (Ingestion ➔ Harmonisation ➔ Nettoyage ➔ Validation ➔ Exportation) :

```bash
python src/main.py
```

### 3. Fichiers de sortie générés
Une fois le script exécuté, vous retrouverez :
- **Données conformes** : dans `data/processed/` (ex: `notaires_valide.csv`, `particuliers_valide.csv`, etc.).
- **Anomalies métier** : dans `data/quarantine/` (ex: `notaires_quarantaine.csv`, `plateforme_immo_quarantaine.csv`, etc.).

---

## BOÎTE À OUTILS & COMMANDES D'ASSISTANCE

Si vous souhaitez exécuter un module individuellement pour effectuer des tests ou du débogage :

```bash
# Test du loader de fichiers CSV
python -m src.loaders.loader_csv

# Test du loader centralisé
python -m src.loaders.main_loader

# Test de l'harmoniseur
python -m src.processing.harmonizer