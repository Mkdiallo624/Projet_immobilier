"""
Paramètres du pipeline : chemins, seuils de plausibilité, conventions métier.

Tous les seuils sont ici (et nulle part ailleurs) : on les modifie sans toucher
aux fonctions de traitement. Les seuils de plausibilité sont des hypothèses
pédagogiques (cf. cahier des charges, §6), pas des normes du marché.
"""
import os

# ---------- Chemins ----------
RAW_DIR = "data/raw"
PROCESSED_DIR = "data/processed"
QUARANTINE_DIR = "data/quarantine"
REPORTS_DIR = "reports"
MAPPING_PATH = "config/mapping_schema.json"
REF_GEO_PATH = os.path.join(RAW_DIR, "referentiel_geographique.csv")
REF_CATEGORIES_PATH = os.path.join(RAW_DIR, "referentiel_categories.csv")

# ---------- Schéma commun (après harmonisation) ----------
COLONNES_STANDARD = [
    "id_local", "date", "region", "ville", "type_bien", "type_transaction",
    "prix", "devise", "surface", "chambres", "sdb", "statut",
    "quartier", "date_expiration",
]

# ---------- Seuils de plausibilité (avertissements, jamais de suppression) ----------
SURFACE_ATYPIQUE_MIN = 5            # m²
SURFACE_ATYPIQUE_MAX = 2_000        # m²
PRIX_VENTE_ATYPIQUE_MIN = 100_000          # FCFA
PRIX_VENTE_ATYPIQUE_MAX = 2_000_000_000    # FCFA
LOYER_ATYPIQUE_MIN = 25_000         # FCFA / mois
LOYER_ATYPIQUE_MAX = 5_000_000      # FCFA / mois
CHAMBRES_MAX_APPART_STUDIO = 10
SDB_MARGE_SUR_CHAMBRES = 2          # sdb > chambres + 2 -> atypique

# ---------- Rapprochement des doublons probables ----------
DOUBLON_TOLERANCE_SURFACE = 0.02    # écart relatif max
DOUBLON_TOLERANCE_PRIX = 0.05       # écart relatif max
DOUBLON_TOLERANCE_JOURS = 30        # écart max entre les dates

# ---------- Conventions métier documentées ----------
# Sources qui, par nature, ne contiennent que des ventes (dictionnaire de données).
SOURCES_VENTE_UNIQUEMENT = {"notaires", "historique"}
# Déduction de la transaction à partir du statut quand elle est absente.
# Vérifié sur plateforme_immo et particuliers : ces statuts n'y apparaissent
# qu'avec la transaction indiquée.
STATUTS_LOCATION = {"Loué", "Disponible"}
STATUTS_VENTE = {"En vente", "Vendu", "Vente conclue", "Acte signé",
                 "Sous offre", "Retiré", "À confirmer"}
STATUTS_CANONIQUES = sorted(STATUTS_LOCATION | STATUTS_VENTE)

# Alias de lieux non couverts par la simple normalisation casse/accents.
ALIAS_LIEUX = {"dkr": "Dakar"}

MOIS_FR = {
    "janvier": 1, "fevrier": 2, "mars": 3, "avril": 4, "mai": 5, "juin": 6,
    "juillet": 7, "aout": 8, "septembre": 9, "octobre": 10, "novembre": 11,
    "decembre": 12,
}
