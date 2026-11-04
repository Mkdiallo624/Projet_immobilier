# ImmoAnalyse — Pipeline ETL immobilier

Transforme 5 sources hétérogènes (CSV, Excel, JSON) en **un seul dataset propre**, avec quarantaine justifiée et rapport de qualité chiffré.

## Chaîne de traitement

```
Ingestion ─► Harmonisation ─► CONCATÉNATION ─► Nettoyage ─► Validation ─► Export
(loaders)    (mapping JSON)   (1 dataset)      (cleaning)   (règles,      (propres, quarantaine,
                                                             doublons)     rapport)
```

La concaténation intervient **avant** nettoyage, validation et export : les mêmes règles s'appliquent à toutes les sources et les doublons entre sources deviennent détectables. Chaque ligne conserve `source`, `id_local` et `ligne_source` ; un `id_bien` technique unique est généré.

## Exécution

```bash
python -m venv mon_env && source mon_env/bin/activate
pip install -r requirements.txt
python src/main.py          # depuis la racine du projet
python -m pytest            # tests unitaires et d'intégration
```

## Sorties

| Fichier | Contenu |
|---|---|
| `data/processed/donnees_propres.csv` / `.json` | lignes retenues (colonnes `statut_final`, `corrections`, `avertissements`, `groupe_doublon`) |
| `data/quarantine/quarantaine.csv` | lignes écartées + `motifs_quarantaine` + valeurs brutes d'origine |
| `reports/rapport_qualite.md` | indicateurs, conformité par règle (avec dénominateur), décisions, limites |
| `reports/quality_report.json`, `quality_summary.csv` | mêmes indicateurs, lisibles par programme |

## Organisation

```
config/mapping_schema.json   colonnes de chaque source -> schéma commun
src/config.py                chemins, seuils de plausibilité, conventions métier (modifiables ici)
src/loaders/                 lecture CSV / JSON / Excel (feuille « Annonces »)
src/processing/harmonizer.py mapping + concaténation
src/processing/cleaning.py   normalisation (fonctions pures : prix, surface, date, catégories…)
src/validation/validation.py règles bloquantes / avertissements / statut final
src/validation/doublons.py   doublons exacts, conflits d'identifiant, doublons probables
src/validation/export.py     exports et rapport
src/analysis/qualite.py      indicateurs de qualité
tests/                       32 tests
```

## Règles (résumé — détail dans `reports/rapport_qualite.md`)

- **Quarantaine** : prix / surface absents, illisibles, ambigus ou ≤ 0 ; date absente, impossible, relative ou future ; transaction non interprétable ; type de bien hors référentiel ; identifiant absent ; doublon exact.
- **Corrigé** : séparateurs de milliers, virgule décimale, suffixes FCFA, « millions » explicites, dates `JJ/MM/AAAA`, casse/accents, synonymes, transaction déduite.
- **Avertissement** (ligne conservée) : valeurs atypiques, géographie incohérente, hors fourchette du référentiel, périodicité inconnue, conflit d'identifiant, doublon probable.
- **Jamais fait** : fusion de doublons, imputation de ville/région, devinette de périodicité ou d'unité.

## Limites

Données synthétiques ; prix = prix demandés ; seuils = hypothèses pédagogiques (voir `src/config.py`). Les ventes et locations coexistent dans le dataset : ne jamais agréger leurs prix ensemble.
