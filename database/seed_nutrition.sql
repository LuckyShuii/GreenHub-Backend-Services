-- ============================================================
-- Greener -- Etape 2 : Seed nutrition
-- Prerequis : avoir lance normalize_nutrition.py pour generer
--             nutrition.json dans le meme dossier que ce fichier.
--
-- Usage depuis psql :
--   \cd /chemin/vers/le/dossier
--   \i seed_nutrition.sql
--
-- Ou en une ligne depuis le terminal :
--   psql -U postgres -d greener -f seed_nutrition.sql
-- ============================================================

-- Colonnes ajoutees progressivement -- sans risque si elles existent deja
ALTER TABLE nutrition ADD COLUMN IF NOT EXISTS categorie    text;
ALTER TABLE nutrition ADD COLUMN IF NOT EXISTS saisonnalite jsonb;

-- Table temporaire pour recevoir le JSON brut
CREATE TEMP TABLE nutrition_import (data jsonb) ON COMMIT DROP;

-- Chargement du fichier JSON
-- \copy attend un chemin absolu ou relatif au repertoire courant (\cd)
\copy nutrition_import (data) FROM 'nutrition.json' (FORMAT text)

-- Insertion depuis la table temporaire
-- ON CONFLICT DO NOTHING : rejouer le script ne cree pas de doublons
INSERT INTO nutrition (
    nom,
    categorie,
    saisonnalite,
    pays_production,
    valeurs_nutritionnelles,
    duree_conservation,
    bienfaits_sante,
    allergenes
)
SELECT
    elem->>'nom',
    elem->>'categorie',
    elem->'saisonnalite',
    elem->'pays_production',
    elem->'valeurs_nutritionnelles',
    elem->'duree_conservation',
    elem->'bienfaits_sante',
    elem->'allergenes'
FROM nutrition_import,
     jsonb_array_elements(data) AS elem
ON CONFLICT DO NOTHING;

-- Confirmation
SELECT
    categorie,
    COUNT(*) AS nb_produits
FROM nutrition
GROUP BY categorie
ORDER BY categorie;
