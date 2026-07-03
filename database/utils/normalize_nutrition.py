"""
Greener -- Etape 1 : Normalisation
Lit les donnees brutes et produit nutrition.json

Usage :
    python normalize_nutrition.py
    python normalize_nutrition.py --output mon_fichier.json
"""

import json
import re
import argparse

# ------------------------------------------------------------------ #
# Saisonnalite                                                        #
# ------------------------------------------------------------------ #

MOIS_FR = [
    "janvier", "fevrier", "mars", "avril", "mai", "juin",
    "juillet", "aout", "septembre", "octobre", "novembre", "decembre"
]

MOIS_ALIASES = {
    "janvier": "janvier", "fevrier": "fevrier", "février": "fevrier",
    "mars": "mars", "avril": "avril", "mai": "mai", "juin": "juin",
    "juillet": "juillet", "aout": "aout", "août": "aout",
    "septembre": "septembre", "octobre": "octobre",
    "novembre": "novembre", "decembre": "decembre", "décembre": "decembre",
}

def normaliser_mois(raw: str) -> str | None:
    raw = raw.strip().lower()
    raw = raw.replace("é", "e").replace("û", "u").replace("è", "e")
    return MOIS_ALIASES.get(raw)

def expandre_intervalle(debut: str, fin: str) -> list[str]:
    i_debut = MOIS_FR.index(debut)
    i_fin   = MOIS_FR.index(fin)
    if i_debut <= i_fin:
        return MOIS_FR[i_debut:i_fin + 1]
    return MOIS_FR[i_debut:] + MOIS_FR[:i_fin + 1]

def parser_saisonnalite(raw: str) -> list[str]:
    if not raw or raw.strip() == "":
        return []
    raw_lower = raw.lower().replace("toute l'année", "toute_annee").replace("toute l'annee", "toute_annee")
    if "toute_annee" in raw_lower:
        return MOIS_FR[:]

    mois_result = []
    segments = [s.strip() for s in raw.split(",")]
    for segment in segments:
        if "–" in segment or (segment.count("-") == 1 and not segment.startswith("-")):
            sep = "–" if "–" in segment else "-"
            parties = [p.strip() for p in segment.split(sep)]
            if len(parties) == 2:
                debut = normaliser_mois(parties[0])
                fin   = normaliser_mois(parties[1])
                if debut and fin:
                    mois_result.extend(expandre_intervalle(debut, fin))
        else:
            m = normaliser_mois(segment)
            if m:
                mois_result.append(m)

    seen = set()
    return [m for m in mois_result if not (m in seen or seen.add(m))]

# ------------------------------------------------------------------ #
# Valeurs nutritionnelles                                             #
# ------------------------------------------------------------------ #

def extraire_nombre(texte: str, pattern: str) -> float | None:
    match = re.search(pattern, texte, re.IGNORECASE)
    if match:
        raw = match.group(1).replace(",", ".").replace("≈", "").strip()
        try:
            return float(raw)
        except ValueError:
            return None
    return None

def parser_valeurs_nutritionnelles(raw: str) -> dict:
    result = {
        "calories_kcal": None,
        "proteines_g":   None,
        "lipides_g":     None,
        "glucides_g":    None,
        "fibres_g":      None,
        "vitamines":     [],
        "mineraux":      [],
    }
    if not raw:
        return result

    result["calories_kcal"] = extraire_nombre(raw, r"([\d.,≈]+)\s*kcal")
    result["proteines_g"]   = extraire_nombre(raw, r"([\d.,]+)\s*g\s*prot[eé]ines?")
    if result["proteines_g"] is None:
        result["proteines_g"] = extraire_nombre(raw, r"prot[eé]ines?\s*\(([\d.,]+)\s*g\)")
    result["lipides_g"]  = extraire_nombre(raw, r"([\d.,]+)\s*g\s*lipides?")
    result["glucides_g"] = extraire_nombre(raw, r"([\d.,]+)\s*g\s*glucides?")
    if result["glucides_g"] is None:
        result["glucides_g"] = extraire_nombre(raw, r"sucres?\s*\(([\d.,]+)\s*g\)")
    result["fibres_g"] = extraire_nombre(raw, r"fibres?\s*\(([\d.,]+)\s*g\)")
    if result["fibres_g"] is None:
        result["fibres_g"] = extraire_nombre(raw, r"([\d.,]+)\s*g\s*fibres?")

    vit_matches = re.findall(r"vit(?:amine)?s?\.?\s*([A-Z][0-9]?(?:[,/]\s*[A-Z][0-9]?)*)", raw)
    vitamines = []
    for match in vit_matches:
        for v in re.split(r"[,/]", match):
            v = v.strip()
            if v:
                vitamines.append(v)
    result["vitamines"] = list(dict.fromkeys(vitamines))

    MINERAUX_CONNUS = [
        "potassium", "magnésium", "magnesium", "calcium", "fer", "zinc",
        "sélénium", "selenium", "manganèse", "manganese", "phosphore",
        "sodium", "cuivre", "iode", "folates"
    ]
    mineraux = []
    raw_lower = raw.lower()
    for m in MINERAUX_CONNUS:
        if m in raw_lower:
            mineraux.append(m.replace("é", "e").replace("è", "e"))
    result["mineraux"] = list(dict.fromkeys(mineraux))

    return result

# ------------------------------------------------------------------ #
# Conservation                                                        #
# ------------------------------------------------------------------ #

def parser_conservation(duree_raw: str) -> dict:
    result = {
        "duree_ambiante": None,
        "duree_frigo":    None,
        "duree_congele":  None,
    }
    if not duree_raw:
        return result

    raw = duree_raw.lower()

    match = re.search(r"(\d+[^;,]*(?:mois|sem\.|semaines?|j(?:ours?)?))\s*(?:congel[eé](?:e)?s?)", raw)
    if match:
        result["duree_congele"] = match.group(1).strip()
    if not result["duree_congele"]:
        match = re.search(r"congel[eé](?:e)?s?\s*:?\s*([^;,]+)", raw)
        if match:
            result["duree_congele"] = match.group(1).strip()

    match = re.search(r"(\d+[^;,]*(?:mois|sem\.|semaines?|j(?:ours?)?))\s*frigo", raw)
    if match:
        result["duree_frigo"] = match.group(1).strip()
    if not result["duree_frigo"]:
        match = re.search(r"frigo\s*:?\s*([^;,]+)", raw)
        if match:
            result["duree_frigo"] = match.group(1).strip()

    match = re.search(r"(\d+[^;,]*(?:mois|sem\.|semaines?|j(?:ours?)?|an))\s*(?:ambiante?|t°?\s*ambiante?|fermée?)", raw)
    if match:
        result["duree_ambiante"] = match.group(1).strip()
    if not result["duree_ambiante"]:
        premier = re.split(r"[;]|frigo|congel", raw)[0].strip().rstrip(",").strip()
        if premier and any(u in premier for u in ["mois", "sem", "jour", "j ", "an"]):
            result["duree_ambiante"] = premier

    return result

# ------------------------------------------------------------------ #
# Allergenes                                                          #
# ------------------------------------------------------------------ #

def parser_allergenes(raw: str) -> list[str] | None:
    if not raw or raw.strip().lower() in ("rares", "rare", ""):
        return None
    return [a.strip() for a in raw.split(";") if a.strip()]

# ------------------------------------------------------------------ #
# Donnees brutes                                                      #
# ------------------------------------------------------------------ #

PRODUITS_BRUTS = [
    # (nom, categorie, saisonnalite, pays, valeurs, duree_conservation, bienfaits, allergenes)
    ("amande", "fruit", "Septembre", "USA (Californie), Espagne, Australie, Iran, Maroc",
     "579 kcal/100g — 21 g proteines, lipides mono-insatures, vit. E, magnesium",
     "12 mois fermee ; 24 mois congelee",
     "Cholesterol, satiete, sante cardiaque", "Fruits a coque (allergene majeur UE)"),

    ("avocat", "fruit", "Janvier–Mars, Mai–Août, Octobre–Décembre",
     "Mexique, Perou, Rep. dominicaine, Colombie, Indonesie",
     "160 kcal/100g — lipides mono-insatures, fibres, K, folates, vit. E",
     "2-3 j muri ; 7 j frigo",
     "Cardiovasculaire, anti-inflammatoire, satiete", "Latex-fruit syndrome (rare)"),

    ("cerise", "fruit", "Mai, Juin", "Turquie, USA, Iran, Italie, Espagne, France",
     "63 kcal/100g — vit. C, polyphenols, potassium, fibres",
     "4-7 j frigo ; 6-12 mois congelees",
     "Antioxydant, anti-inflammatoire, sommeil", "Syndrome oral (Rosacees, LTP)"),

    ("citron", "fruit", "Janvier–Mars, Mai, Juillet–Décembre",
     "Inde, Mexique, Chine, Argentine, Espagne",
     "29 kcal/100g — vit. C (53 mg), acide citrique, potassium",
     "1 mois frigo",
     "Immunite, digestion, antioxydant", "LTP rare"),

    ("coing", "fruit", "Septembre, Octobre, Novembre",
     "Turquie, Chine, Iran, Maroc, Argentine",
     "57 kcal/100g — vit. C, pectines, potassium",
     "2 mois frigo",
     "Transit, antioxydant", None),

    ("figue", "fruit", "Juin–Octobre", "Turquie, Egypte, Maroc, Algerie, Iran",
     "74 kcal/100g — fibres, potassium, calcium, vit. K",
     "2-3 j frigo",
     "Transit, os, antioxydant", "LTP ; latex"),

    ("framboise", "fruit", "Mai–Septembre", "Russie, Mexique, Pologne, Serbie, USA",
     "52 kcal/100g — fibres (6,5 g), vit. C, manganese, antioxydants",
     "2-3 j ; 12 mois congelees",
     "Transit, antioxydant", "Histamino-liberateur"),

    ("fruits-a-coque", "fruit", "Octobre", "USA, Chine, Iran, Turquie, Inde",
     "600 kcal/100g — lipides bons, proteines, fibres, vit. E, magnesium",
     "6-12 mois",
     "Cardiovasculaire, satiete", "Fruits a coque (allergene majeur UE)"),

    ("kaki", "fruit", "Octobre, Novembre, Décembre", "Chine, Coree, Japon, Bresil, Espagne",
     "70 kcal/100g — vit. A, C, fibres, potassium",
     "1 sem. muri",
     "Vue, immunite, antioxydant", "LTP rare"),

    ("kumquat", "fruit", "Mars", "Chine, Japon, USA, Israel, Bresil",
     "71 kcal/100g — vit. C, fibres, calcium",
     "2 sem. frigo",
     "Immunite, antioxydant", "LTP rare"),

    ("mangue", "fruit", "Mai, Septembre, Octobre, Novembre",
     "Inde, Chine, Thailande, Indonesie, Mexique",
     "60 kcal/100g — vit. A, C, fibres, polyphenols",
     "5-7 j mure ; 2 j frigo",
     "Vue, immunite, transit", "Reaction croisee latex"),

    ("myrtille", "fruit", "Avril–Septembre", "USA, Canada, Pologne, Perou, Mexique",
     "57 kcal/100g — anthocyanes, vit. C, K, fibres",
     "1-2 sem. frigo ; 12 mois congelees",
     "Antioxydant, vue, memoire", None),

    ("nectarine", "fruit", "Juin, Juillet, Août", "Chine, Italie, Espagne, USA, France",
     "44 kcal/100g — vit. C, A, fibres, potassium",
     "3-5 j mure",
     "Antioxydant, vue", "Syndrome oral (Rosacees, LTP)"),

    ("orange", "fruit", "Janvier–Mai, Octobre–Décembre",
     "Bresil, Inde, Chine, Mexique, Espagne, USA",
     "47 kcal/100g — vit. C (53 mg), folates, fibres",
     "2-3 sem. frigo",
     "Immunite, antioxydant", "LTP rare"),

    ("peche", "fruit", "Juin, Juillet, Août", "Chine, Italie, Espagne, USA, Grece",
     "39 kcal/100g — vit. C, A, fibres, potassium",
     "3-5 j mure",
     "Antioxydant, transit, peau", "Syndrome oral / LTP majeur (Rosacees)"),

    ("pomelo", "fruit", "Janvier–Mai, Octobre, Novembre",
     "Chine, Vietnam, Thailande, Inde, Israel",
     "38 kcal/100g — vit. C, fibres, potassium",
     "2-3 sem. frigo",
     "Immunite, antioxydant", "Interactions medicamenteuses (CYP3A4)"),

    ("prune", "fruit", "Juin–Septembre", "Chine, Roumanie, Serbie, USA, Iran",
     "46 kcal/100g — vit. C, K, fibres, polyphenols",
     "3-5 j",
     "Transit, antioxydant", "Syndrome oral"),

    ("raisin-noir", "fruit", "Juillet–Octobre", "Italie, France, Espagne, Turquie, Chine",
     "69 kcal/100g — anthocyanes, resveratrol, vit. C, K",
     "5-7 j frigo",
     "Cardiovasculaire, antioxydant", "LTP rare"),

    ("abricot", "fruit", "Juin, Juillet, Août", "Turquie, Iran, Ouzbekistan, Italie, France",
     "48 kcal/100g — beta-carotene, vit. C, potassium, fibres",
     "3-5 j frigo ; 6 mois congele",
     "Antioxydant, sante oculaire, transit", "Syndrome oral (Rosacees, LTP)"),

    ("anone", "fruit", "Octobre, Novembre", "Perou, Espagne, Chili, Mexique",
     "75 kcal/100g — vit. C, B6, fibres, potassium",
     "2-3 j mure ; 5 j frigo",
     "Antioxydant, immunite, digestion", None),

    ("banane", "fruit", "Mai–Décembre",
     "Inde, Chine, Indonesie, Bresil, Equateur, Philippines",
     "89 kcal/100g — glucides, potassium (358 mg), vit. B6, fibres",
     "5-7 j",
     "Energie, transit, recuperation musculaire", "Latex-fruit syndrome (rare)"),

    ("chataigne", "fruit", "Septembre, Novembre", "Chine, Turquie, Italie, Espagne, France",
     "196 kcal/100g — glucides complexes, fibres, vit. C, manganese",
     "1 sem. ambiante ; 1 mois frigo ; 6 mois congelee",
     "Energie sans gluten, transit, mineraux", "Fruit a coque (etiquetage UE)"),

    ("clementine", "fruit", "Octobre, Novembre, Décembre",
     "Espagne, Maroc, Chine, Italie, Algerie",
     "47 kcal/100g — vit. C, fibres, folates, potassium",
     "1 sem. ambiante ; 2 sem. frigo",
     "Immunite, antioxydant", "LTP possible"),

    ("datte", "fruit", "Mai", "Egypte, Iran, Arabie saoudite, Algerie, Tunisie",
     "282 kcal/100g — sucres (66 g), fibres, potassium, magnesium",
     "6 mois ambiante ; 1 an frigo",
     "Energie rapide, transit, mineraux", None),

    ("fraise", "fruit", "Avril–Août", "Chine, USA, Mexique, Egypte, Espagne",
     "32 kcal/100g — vit. C (59 mg), manganese, polyphenols, fibres",
     "2-3 j",
     "Antioxydant, immunite, peau", "Histamino-liberateur frequent"),

    ("fruit-de-la-passion", "fruit", "Mai",
     "Bresil, Colombie, Perou, Equateur, Vietnam",
     "97 kcal/100g — fibres (10 g), vit. C, A, fer",
     "1 sem. frigo",
     "Transit, immunite, antioxydant", "Latex-fruit syndrome possible"),

    ("grenade", "fruit", "Septembre, Octobre, Novembre",
     "Inde, Iran, Chine, Turquie, Espagne",
     "83 kcal/100g — vit. C, K, polyphenols, fibres",
     "1 mois frigo",
     "Antioxydant, cardiovasculaire", "LTP rare"),

    ("kiwi", "fruit", "Janvier–Mai, Octobre–Décembre",
     "Nouvelle-Zelande, Italie, Chine, Iran, Grece, Chili",
     "61 kcal/100g — vit. C (93 mg), K, fibres, folates",
     "1-2 sem. frigo",
     "Immunite, transit, peau", "Allergene frequent (latex-fruit)"),

    ("mandarine", "fruit", "Janvier, Février, Mars, Octobre",
     "Chine, Espagne, Turquie, Bresil, Maroc",
     "53 kcal/100g — vit. C, A, fibres",
     "2 sem. frigo",
     "Immunite, antioxydant", "LTP rare"),

    ("melon", "fruit", "Mai–Septembre", "Chine, Turquie, Iran, Inde, Espagne, Maroc",
     "34 kcal/100g — eau (90%), vit. A, C, potassium",
     "5 j entier ; 2-3 j coupe",
     "Hydratation, vue", "Syndrome oral (pollen ambroisie)"),

    ("nashi", "fruit", "Septembre, Octobre, Novembre",
     "Chine, Coree, Japon, Australie, USA",
     "42 kcal/100g — eau, fibres, vit. C, potassium",
     "1-2 sem. frigo",
     "Hydratation, transit", "Syndrome oral (Rosacees)"),

    ("noix", "fruit", "Novembre", "Chine, USA, Iran, Turquie, Mexique",
     "654 kcal/100g — omega-3 (ALA), proteines, fibres, magnesium",
     "6-12 mois en coque ; 6 mois decorticuees",
     "Cerveau, cardiovasculaire", "Fruits a coque (allergene majeur UE)"),

    ("pasteque", "fruit", "Mai–Septembre", "Chine, Iran, Turquie, Inde, Bresil",
     "30 kcal/100g — eau (92%), lycopene, vit. A, C",
     "7-10 j entiere ; 3-4 j coupee",
     "Hydratation, antioxydant", "Syndrome oral"),

    ("poire", "fruit", "Août–Décembre", "Chine, USA, Argentine, Italie, Espagne",
     "57 kcal/100g — fibres (3,1 g), vit. C, K, potassium",
     "3-5 j mure ; 1-2 sem. frigo",
     "Transit, satiete, antioxydant", "Syndrome oral (Rosacees)"),

    ("pomme", "fruit", "Toute l'année", "Chine, USA, Turquie, Pologne, Italie",
     "52 kcal/100g — fibres (2,4 g), vit. C, K, polyphenols",
     "1-2 mois frigo",
     "Transit, cardiovasculaire, antioxydant", "Syndrome oral (Rosacees, LTP)"),

    ("raisin-blanc", "fruit", "Août–Octobre", "Italie, France, Espagne, Turquie, Chine",
     "69 kcal/100g — sucres, vit. C, K, polyphenols",
     "5-7 j frigo",
     "Antioxydant, cardiovasculaire", "LTP rare"),

    ("litchi", "fruit", "Juin, Juillet",
     "Chine, Inde, Thailande, Vietnam, Afrique du Sud",
     "66 kcal/100g — vit. C (72 mg), potassium, fibres, polyphenols",
     "1-2 sem. frigo ; 3 mois congele",
     "Immunite, antioxydant", "LTP rare"),

    # Legumes
    ("artichaut", "legume", "Avril–Octobre",
     "Italie, Egypte, Espagne, Perou, France",
     "47 kcal/100g — fibres (5 g), folates, vit. K, magnesium",
     "1 sem. cru",
     "Foie, digestion, prebiotique", "Syndrome oral (Asteracees)"),

    ("aubergine", "legume", "Avril–Septembre",
     "Chine, Inde, Egypte, Turquie, Iran",
     "25 kcal/100g — fibres, antioxydants, potassium",
     "5-7 j",
     "Antioxydant, satiete", "Solanacees (rare)"),

    ("blette", "legume", "Janvier, Mars, Mai–Novembre",
     "France, Italie, Espagne",
     "19 kcal/100g — vit. K, A, C, magnesium",
     "3-5 j",
     "Os, antioxydant", "Riche en oxalates"),

    ("carotte", "legume", "Toute l'année",
     "Chine, Ouzbekistan, USA, Russie, Pologne",
     "41 kcal/100g — beta-carotene (vit. A), fibres, potassium",
     "2-4 sem. frigo",
     "Vue, peau, antioxydant", "Syndrome oral (Apiacees)"),

    ("champignon", "legume", "Janvier–Mars, Mai–Décembre",
     "Chine, Italie, USA, Pays-Bas, Pologne",
     "22 kcal/100g — proteines, vit. B, D, selenium, potassium",
     "3-7 j",
     "Immunite, vit. D", "Spores ; rares"),

    ("choux-chinois", "legume", "Janvier–Mars, Juin–Décembre",
     "Chine, Coree, Japon",
     "13 kcal/100g — vit. C, K, A, folates",
     "1 sem.",
     "Antioxydant, os", None),

    ("choux-fleur", "legume", "Toute l'année",
     "Chine, Inde, USA, Espagne, France",
     "25 kcal/100g — vit. C, K, fibres, choline",
     "1 sem.",
     "Antioxydant, satiete, cerveau", None),

    ("choux-kale", "legume", "Janvier",
     "USA, Chine, Italie, France",
     "49 kcal/100g — vit. K, A, C, calcium, fibres",
     "5-7 j",
     "Os, vue, antioxydant", None),

    ("choux-rave", "legume", "Mai–Septembre, Novembre",
     "Allemagne, Inde, Chine, France",
     "27 kcal/100g — vit. C, fibres, potassium",
     "2-3 sem.",
     "Immunite, transit", None),

    ("choux-de-bruxelle", "legume", "Octobre, Novembre",
     "Pays-Bas, Royaume-Uni, France, USA, Mexique",
     "43 kcal/100g — vit. C, K, fibres, sulforaphane",
     "1-2 sem.",
     "Antioxydant, transit", None),

    ("choux-frise", "legume", "Janvier, Mars, Septembre–Décembre",
     "USA, Chine, Italie, France",
     "49 kcal/100g — vit. K, C, A, calcium",
     "5-7 j",
     "Os, antioxydant, vue", None),

    ("choux-lisse", "legume", "Janvier, Février, Avril–Décembre",
     "Chine, Inde, Russie, Coree, Pologne",
     "25 kcal/100g — vit. C, K, fibres",
     "2-3 sem.",
     "Antioxydant, digestion", None),

    ("choux-romanesco", "legume", "Février, Septembre–Novembre",
     "Italie, France, Espagne",
     "25 kcal/100g — vit. C, K, fibres",
     "1 sem.",
     "Antioxydant, transit", None),

    ("concombre", "legume", "Mars–Octobre",
     "Chine, Turquie, Iran, Russie, Mexique",
     "16 kcal/100g — eau (96%), vit. K, potassium",
     "1 sem.",
     "Hydratation, faible cal", "LTP rare"),

    ("courge-butternut", "legume", "Janvier–Mars, Juillet–Décembre",
     "USA, Chine, Inde, Mexique, Italie",
     "45 kcal/100g — beta-carotene, vit. C, fibres, potassium",
     "2-3 mois entiere ; 5 j coupee frigo",
     "Vue, antioxydant", None),

    ("courgette", "legume", "Avril–Novembre",
     "Chine, Inde, Russie, Mexique, Egypte",
     "17 kcal/100g — vit. C, K, B6, eau",
     "1 sem.",
     "Hydratation, faible cal", None),

    ("endive", "legume", "Janvier–Mars, Mai, Juin, Septembre–Décembre",
     "France, Belgique, Pays-Bas",
     "17 kcal/100g — vit. K, A, B9, fibres",
     "1 sem.",
     "Digestion, foie", "Asteracees (rare)"),

    ("epinard", "legume", "Février, Avril–Novembre",
     "Chine, USA, Japon, Turquie, Indonesie",
     "23 kcal/100g — fer, folates, vit. K, A, magnesium",
     "3-5 j ; congelable",
     "Anemie, os, vue", "Riche en oxalates"),

    ("fenouil", "legume", "Toute l'année",
     "Inde, Chine, Egypte, Italie, France",
     "31 kcal/100g — vit. C, K, fibres",
     "1 sem.",
     "Digestion, anti-ballonnement", "Apiacees (rare)"),

    ("feves", "legume", "Avril, Mai",
     "Chine, Ethiopie, Royaume-Uni, France, Egypte",
     "88 kcal/100g — proteines (8 g), folates, fibres, fer",
     "2-3 j ; congelables",
     "Proteines vegetales, folates", "Favisme (G6PD) ; legumineuses"),

    ("haricot", "legume", "Avril–Septembre",
     "Chine, Indonesie, Inde, Turquie, Egypte",
     "31 kcal/100g — fibres, vit. C, K, folates",
     "5-7 j ; congelables",
     "Transit, antioxydant", "Legumineuses"),

    ("mache", "legume", "Décembre",
     "France, Italie, Pays-Bas",
     "21 kcal/100g — omega-3 (ALA), vit. C, B9, fer",
     "3-4 j",
     "Antioxydant, fer", None),

    ("mais", "legume", "Juillet, Août, Septembre",
     "USA, Chine, Bresil, Argentine, Ukraine",
     "86 kcal/100g — glucides, fibres, vit. B, magnesium",
     "3 j frais ; 6 mois congele",
     "Energie, antioxydants", "Possible (graminees) ; rare"),

    ("navet", "legume", "Toute l'année",
     "Chine, Russie, France, USA, Pologne",
     "28 kcal/100g — vit. C, fibres, potassium",
     "2-3 sem.",
     "Faible cal, antioxydant", None),

    ("oignons", "legume", "Janvier–Août",
     "Chine, Inde, Egypte, USA, Iran",
     "40 kcal/100g — quercetine, vit. C, fibres",
     "1-2 mois entier",
     "Cardiovasculaire, antioxydant", "Rares ; FODMAP"),

    ("panais", "legume", "Octobre, Novembre",
     "Royaume-Uni, USA, France, Allemagne",
     "75 kcal/100g — fibres, vit. C, K, folates, potassium",
     "2-3 sem.",
     "Transit, energie douce", "Apiacees (rare)"),

    ("patate-douce", "legume", "Janvier–Juin, Septembre–Décembre",
     "Chine, Malawi, Tanzanie, Nigeria, Indonesie",
     "86 kcal/100g — beta-carotene, vit. C, fibres, potassium",
     "3-4 sem.",
     "Vue, antioxydant, energie", None),

    ("poireau", "legume", "Toute l'année",
     "Indonesie, Turquie, Coree, France, Belgique",
     "61 kcal/100g — vit. K, A, C, fibres, manganese",
     "1-2 sem.",
     "Diuretique, transit", "Liliacees (rare)"),

    ("pois", "legume", "Mai–Août",
     "Canada, Russie, Chine, Inde, USA",
     "81 kcal/100g — proteines (5 g), fibres, vit. C, K, folates",
     "2-3 j ; congelables",
     "Proteines vegetales, transit", "Legumineuses"),

    ("poivrons", "legume", "Avril–Septembre",
     "Chine, Mexique, Turquie, Indonesie, Espagne",
     "31 kcal/100g — vit. C, A, fibres",
     "1-2 sem.",
     "Immunite, antioxydant", "Solanacees (rare)"),

    ("pomme-de-terre", "legume", "Toute l'année",
     "Chine, Inde, Russie, Ukraine, USA",
     "77 kcal/100g — glucides, vit. C, B6, potassium, fibres",
     "1-2 mois",
     "Energie, satiete", "Solanine (germes verts) ; rares"),

    ("radis", "legume", "Toute l'année",
     "Chine, Japon, Coree, USA, France",
     "16 kcal/100g — vit. C, fibres",
     "1 sem.",
     "Antioxydant, digestion", None),

    ("salade", "legume", "Toute l'année",
     "Chine, USA, Inde, Espagne, Italie",
     "15 kcal/100g — eau, vit. K, A, folates",
     "5-7 j",
     "Hydratation, faible cal", "Asteracees / LTP (rare)"),

    ("tomate", "legume", "Mai–Octobre",
     "Chine, Inde, Turquie, USA, Egypte",
     "18 kcal/100g — lycopene, vit. C, K, potassium",
     "1 sem.",
     "Antioxydant, cardiovasculaire", "Solanacees ; histamino-liberateur"),
]

# ------------------------------------------------------------------ #
# Normalisation                                                       #
# ------------------------------------------------------------------ #

def normaliser(produit: tuple) -> dict:
    nom, categorie, sais_raw, pays_raw, valeurs_raw, duree_raw, bienfaits_raw, allergenes_raw = produit

    return {
        "nom":                      nom,
        "categorie":                categorie,
        "saisonnalite":             parser_saisonnalite(sais_raw),
        "pays_production":          [p.strip() for p in pays_raw.split(",") if p.strip()],
        "valeurs_nutritionnelles":  parser_valeurs_nutritionnelles(valeurs_raw),
        "duree_conservation":       parser_conservation(duree_raw),
        "bienfaits_sante":          [b.strip() for b in bienfaits_raw.split(",") if b.strip()],
        "allergenes":               parser_allergenes(allergenes_raw),
    }

# ------------------------------------------------------------------ #
# Main                                                                #
# ------------------------------------------------------------------ #

def main():
    parser = argparse.ArgumentParser(description="Normalise les donnees nutrition vers JSON")
    parser.add_argument("--output", default="nutrition.json", help="Fichier de sortie (defaut: nutrition.json)")
    args = parser.parse_args()

    produits = [normaliser(p) for p in PRODUITS_BRUTS]

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(produits, f, ensure_ascii=False, indent=2)

    print(f"{len(produits)} produits normalises → {args.output}")

if __name__ == "__main__":
    main()
