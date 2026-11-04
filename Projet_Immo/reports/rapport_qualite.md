# Rapport de qualité — ImmoAnalyse

Traitement réalisé sur le dataset **consolidé** (concaténation des 5 sources avant nettoyage, validation et export). Les données sources n'ont pas été modifiées.

## 1. Synthèse

| Indicateur | Valeur |
|---|---|
| Enregistrements reçus (toutes sources) | 3184 |
| Retenus, entièrement conformes (ni correction, ni avertissement) | 836 (26.3 %) |
| Retenus après correction de format, sans avertissement | 1621 |
| Retenus avec avertissement | 522 |
| Mis en quarantaine | 205 |
| Dont doublons exacts | 15 (0.47 %) |
| Doublons probables signalés (non fusionnés) | 0 lignes en 0 groupes |

*Définition du taux global : enregistrements entièrement conformes / enregistrements reçus (3184). Les 4 catégories (quarantaine, avertissement, corrigé, conforme) sont exclusives : un enregistrement n'est compté qu'une fois, selon la priorité quarantaine > avertissement > corrigé > conforme. Au total, 2124 enregistrements ont subi au moins une correction de format (y compris ceux qui ont aussi un avertissement).*

## 2. Volumes par source

| Source | Reçus | Quarantaine | Retenus | % retenus |
|---|---|---|---|---|
| notaires | 410 | 20 | 390 | 95.1 |
| historique | 528 | 10 | 518 | 98.1 |
| plateforme_immo | 875 | 30 | 845 | 96.6 |
| particuliers | 731 | 136 | 595 | 81.4 |
| agence_teranga | 640 | 9 | 631 | 98.6 |

## 3. Conformité par règle

Taux = conformes / évaluables. Les lignes non évaluables sont comptées à part et ne sont pas considérées comme conformes.

| Règle | Évaluables (dénominateur) | Conformes | Non conformes | Non évaluables | Taux |
|---|---|---|---|---|---|
| identifiant local présent | 3184 | 3184 | 0 | 0 | 100.0 % |
| prix numérique | 3184 | 3091 | 93 | 0 | 97.1 % |
| prix > 0 | 3091 | 3086 | 5 | 93 | 99.8 % |
| surface numérique | 3184 | 3100 | 84 | 0 | 97.4 % |
| surface > 0 | 3100 | 3096 | 4 | 84 | 99.9 % |
| date interprétable | 3184 | 3178 | 6 | 0 | 99.8 % |
| date non future | 3178 | 3173 | 5 | 6 | 99.8 % |
| type_transaction renseigné ou déductible | 3184 | 3184 | 0 | 0 | 100.0 % |
| type_bien dans le référentiel | 3184 | 3184 | 0 | 0 | 100.0 % |
| pas de doublon exact | 3184 | 3169 | 15 | 0 | 99.5 % |
| surface plausible | 3096 | 3096 | 0 | 88 | 100.0 % |
| prix de vente plausible | 2608 | 2608 | 0 | 576 | 100.0 % |
| loyer plausible | 478 | 478 | 0 | 2706 | 100.0 % |
| région cohérente avec la ville | 3176 | 3172 | 4 | 8 | 99.9 % |
| prix dans la fourchette de la catégorie | 2608 | 2528 | 80 | 576 | 96.9 % |
| surface dans la fourchette de la catégorie | 3096 | 3093 | 3 | 88 | 99.9 % |
| chambres/sdb cohérentes | 2774 | 2612 | 162 | 410 | 94.2 % |

## 4. Quarantaine : motifs

Chaque ligne en quarantaine porte ses motifs dans `data/quarantine/quarantaine.csv` (colonne `motifs_quarantaine`). Une ligne peut cumuler plusieurs motifs.

| Motif | Lignes |
|---|---|
| prix_absent | 85 |
| surface_absent | 80 |
| doublon_exact | 15 |
| prix_illisible | 8 |
| date_impossible | 6 |
| date_future | 5 |
| prix_non_positif | 5 |
| surface_illisible | 4 |
| surface_non_positif | 4 |

## 5. Avertissements (lignes conservées)

| Avertissement | Lignes |
|---|---|
| periodicite_inconnue | 278 |
| sdb_superieur_chambres_plus_2 | 153 |
| prix_hors_fourchette_categorie | 80 |
| transaction_incoherente_statut | 13 |
| ville_absente | 8 |
| region_ville_incoherente | 4 |
| surface_hors_fourchette_categorie | 3 |

## 6. Valeurs manquantes par colonne (avant nettoyage, dataset consolidé)

| Colonne | Manquants | Taux |
|---|---|---|
| id_local | 0 | 0.0 % |
| date | 0 | 0.0 % |
| region | 0 | 0.0 % |
| ville | 8 | 0.3 % |
| type_bien | 0 | 0.0 % |
| type_transaction | 1578 | 49.6 % |
| prix | 85 | 2.7 % |
| devise | 2309 | 72.5 % |
| surface | 80 | 2.5 % |
| chambres | 0 | 0.0 % |
| sdb | 410 | 12.9 % |
| statut | 528 | 16.6 % |
| quartier | 2309 | 72.5 % |
| date_expiration | 2309 | 72.5 % |

## 7. Erreurs de conversion par champ

Valeurs présentes mais non convertibles de façon fiable (illisible, ambigu, date impossible ou relative).

| Champ | Erreurs |
|---|---|
| prix | 8 |
| surface | 4 |
| date | 6 |
| date_expiration | 0 |
| chambres | 0 |
| sdb | 0 |
| type_transaction | 0 |

## 8. Décisions de traitement

- **Concaténation avant validation** : les 5 sources sont harmonisées puis réunies en un seul tableau, ce qui permet d'appliquer des règles identiques et de détecter les doublons entre sources. Chaque ligne garde `source`, `id_local` et `ligne_source`.
- **Identifiants** : `id_local` n'est jamais utilisé comme clé. Un `id_bien` technique unique est généré ; un même identifiant local portant des contenus différents est signalé (`conflit_id`).
- **Dates `JJ/MM/AAAA`** : lues jour en premier, conformément au dictionnaire de données ; `32/13/2024` est impossible, `hier` est relative donc refusée (quarantaine).
- **Dates futures** : mises en quarantaine pour toutes les transactions (le dictionnaire de données l'exige pour les annonces ; `regles_metier.md` ne cite que les ventes — nous appliquons la règle la plus stricte).
- **Prix** : `58.29 millions` → 58 290 000 (unité explicite) ; `37 965 000` et `1,250,000` → séparateurs de milliers ; `à négocier` et `quatre-vingt` → illisibles, donc quarantaine (pas de conversion de texte en lettres).
- **Surfaces** : `53,0` → 53.0 ; `1,250` serait ambigu (1 250 m² ou 1,25 m²) → quarantaine, jamais deviné.
- **Transaction** : valeur d'origine conservée si présente. Sinon `notaires` et `historique` = vente (par nature de la source) ; autres sources déduites du statut (`Loué`, `Disponible` → location). Ces lignes sont marquées `transaction_deduite = True`.
- **Périodicité** : lue depuis la devise (`FCFA/mois` → mensuel). Absente ⇒ signalée, jamais devinée. Ventes et locations ne doivent pas être agrégées ensemble (un loyer n'est pas un prix de vente).
- **Type de bien hors référentiel** : quarantaine (cahier des charges §6.1), alors que `regles_metier.md` ne prévoit qu'un avertissement. Aucun cas dans ces données.
- **Doublons** : copies exactes mises en quarantaine (traçables, rien n'est supprimé) ; doublons probables signalés sans fusion (surface ±2 %, prix ±5 %, date ±30 jours, même ville, type et transaction). Seuils dans `src/config.py`.
- **Fourchettes du référentiel** : prix et surface hors fourchette indicative → avertissement uniquement.

## 9. Limites

- Données synthétiques : ces indicateurs n'ont pas de valeur de marché.
- Les prix de vente sont des prix demandés (annonces), pas nécessairement des prix de transaction.
- Les seuils de plausibilité et de rapprochement sont des hypothèses pédagogiques, à valider avec le formateur sur les cas ambigus.
- La déduction de la transaction à partir du statut repose sur la cohérence observée dans `plateforme_immo` et `particuliers`.
