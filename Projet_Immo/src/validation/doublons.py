"""
Détection des doublons — stratégie documentée.

1. DOUBLON EXACT : même source ET tous les champs normalisés identiques.
   -> la copie est mise en quarantaine (motif 'doublon_exact'), l'original est conservé.
2. CONFLIT D'IDENTIFIANT : même (source, id_local) mais contenus différents.
   -> les deux lignes sont conservées et signalées ('conflit_id'). Pas de résolution arbitraire.
3. DOUBLON PROBABLE (rapprochement approximatif, entre lignes retenues) :
   même ville + même type de bien + même transaction, ET
   écart de surface <= 2 %, écart de prix <= 5 %, écart de date <= 30 jours.
   -> signalé ('doublon_probable') avec un `groupe_doublon` commun. JAMAIS fusionné :
   la décision de fusion appartient à l'analyste (seuils dans config.py).
"""
import pandas as pd

import config

CHAMPS_CONTENU = ["source", "id_local", "date", "region", "ville", "type_bien",
                  "type_transaction", "prix", "surface", "chambres", "sdb", "statut"]


def marquer_doublons_exacts(df):
    """Booléen : True pour les copies (la première occurrence n'est pas marquée)."""
    return df.duplicated(subset=CHAMPS_CONTENU, keep="first")


def marquer_conflits_id(df, masque_copies):
    """True pour les lignes dont (source, id_local) apparaît avec des contenus différents."""
    base = df[~masque_copies]
    cle = base["source"].astype(str) + "|" + base["id_local"].astype(str)
    multiples = cle[cle.duplicated(keep=False)]
    conflit = pd.Series(False, index=df.index)
    conflit.loc[multiples.index] = True
    return conflit


def _ecart_relatif(a, b):
    return abs(a - b) / max(abs(a), abs(b))


def trouver_doublons_probables(df):
    """
    Renvoie une Series `groupe_doublon` (NaN si aucun) sur les lignes fournies.
    Blocage par (ville, type_bien, type_transaction) puis comparaison deux à deux.
    """
    groupes = pd.Series(pd.NA, index=df.index, dtype="object")
    parent = {i: i for i in df.index}

    def trouver(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    candidats = df.dropna(subset=["ville", "type_bien", "type_transaction", "surface", "prix", "date"])
    for _, bloc in candidats.groupby(["ville", "type_bien", "type_transaction"]):
        idx = list(bloc.index)
        for a in range(len(idx)):
            for b in range(a + 1, len(idx)):
                i, j = idx[a], idx[b]
                ra, rb = df.loc[i], df.loc[j]
                if ra["source"] == rb["source"] and ra["id_local"] == rb["id_local"]:
                    continue  # même enregistrement (cas des conflits d'identifiant)
                if _ecart_relatif(ra["surface"], rb["surface"]) > config.DOUBLON_TOLERANCE_SURFACE:
                    continue
                if _ecart_relatif(ra["prix"], rb["prix"]) > config.DOUBLON_TOLERANCE_PRIX:
                    continue
                if abs((ra["date"] - rb["date"]).days) > config.DOUBLON_TOLERANCE_JOURS:
                    continue
                parent[trouver(j)] = trouver(i)

    racines = {}
    for i in candidats.index:
        r = trouver(i)
        racines.setdefault(r, []).append(i)
    numero = 0
    for membres in racines.values():
        if len(membres) > 1:
            numero += 1
            for i in membres:
                groupes.loc[i] = f"DUP-{numero:04d}"
    return groupes
