# GreenHub-Backend-Services

Base applicative FastAPI minimale, avec une route de santé et la
documentation Swagger générée automatiquement.

## Structure

backend/
├── main.py           # point d'entrée FastAPI, monte les routers
├── routers/
│   └── health.py      # route GET /health
├── services/          # logique métier (à venir)
├── utils/             # fonctions utilitaires partagées (à venir)
├── tests/             # suite pytest (unit/ et integration/)
├── pyproject.toml     # dépendances du projet
├── uv.lock             # lockfile figé (généré par uv sync)
└── .gitignore

## Installation locale

    cd backend
    uv sync

## Lancer le serveur

    uv run uvicorn main:app --reload
Le serveur écoute par défaut sur http://localhost:8000

## Vérifier la sonde de liveness

    curl http://localhost:8000/health
    # {"status": "ok"}

## Documentation Swagger

Générée automatiquement par FastAPI, sans configuration supplémentaire :

- http://localhost:8000/docs — Swagger UI interactif (tester les routes depuis le navigateur)
- http://localhost:8000/redoc — documentation alternative (ReDoc)
- http://localhost:8000/openapi.json — schéma OpenAPI brut

## Tests

Depuis votre machine (nécessite `.env` renseigné et la base lancée) :

    docker compose up -d postgres
    cd backend
    uv run pytest                    # 90 tests, suite complète + couverture
    uv run pytest -m unit --no-cov   # unitaires seuls, ~3 s, sans base

Ou directement depuis le conteneur, sans rien installer localement :

    docker compose up -d
    docker compose exec backend pytest

Les tests d'intégration tournent sur une base dédiée `greener_test`,
créée automatiquement, **jamais** sur `greener`. Sans base joignable ils
sont ignorés en local (avec un message expliquant quoi faire) et en échec
en CI.

Comment lancer les tests, conventions de nommage, découpage
unitaire/intégration et cible de couverture :
[backend/tests/README.md](backend/tests/README.md).

La CI (`.github/workflows/backend-tests.yml`) rejoue la suite complète
sur chaque PR vers `main` et `staging`, PostGIS compris.

## Ajouter une dépendance

    uv add nom-du-package

pyproject.toml et uv.lock sont mis à jour automatiquement — les deux
doivent être committés.

## Stack de dev isolée (PostgreSQL + backend)

Le `docker-compose.yml` à la racine démarre une stack **db + backend uniquement**
(sans le service IA) pour développer le backend en isolation : PostgreSQL persistant
avec PostGIS (stratégie V1 : pas de service managé) et l'API FastAPI en hot-reload
(image `backend/Dockerfile.dev`, source montée en volume).

> La stack applicative complète (backend + IA + gateway) vit dans le repo
> infrastructure ; ce compose-ci ne sert qu'au dev backend.

Démarrage :

    cp .env.example .env      # renseigner DB_USER / DB_PASSWORD
    docker compose up -d

Vérifier que la base est prête :

    docker compose ps         # postgres "healthy" (pg_isready), backend démarré
    docker compose exec postgres psql -U "$DB_USER" -d greener -c "SELECT postgis_version();"
    curl http://localhost:8000/health   # {"status": "ok"}
    curl http://localhost:8000/health/db # {"status": "ok", "database": "reachable"}

La route `GET /health/db` ouvre une session SQLAlchemy depuis le backend et
exécute `SELECT 1`. Elle retourne `503` si PostgreSQL n'est pas joignable ou si
les identifiants de connexion sont invalides.

- Image officielle versionnée `postgis/postgis:16-3.4-alpine`.
- Données persistées dans le volume nommé `pg_data` (survivent au redémarrage
  et au `docker compose down` ; `down -v` les supprime).
- Port exposé sur `127.0.0.1:5432` uniquement (injoignable depuis l'extérieur).
  En production (repo infrastructure) aucun port n'est publié : les services
  communiquent via le réseau `greener_internal` et le debug distant passe par
  le VPN.
- Credentials lus depuis `.env` ; en prod ils sont injectés via ansible-vault.

Arrêter :

    docker compose down       # conserve les données
    docker compose down -v    # supprime aussi le volume pg_data

## Migrations de base de données

Le schéma initial est créé par `database/init/01-postgis.sql` uniquement
lorsque le volume PostgreSQL est vide. Sur une base existante, les évolutions
sont appliquées par Alembic : le backend exécute `alembic upgrade head` au
démarrage.

Pour appliquer les migrations sans redémarrer un backend déjà lancé :

    docker compose exec backend alembic upgrade head

La révision `20261030_add_answers_comment` ajoute `answers.comment` en
`TEXT`, nullable et sans valeur par défaut. Les réponses existantes sont
conservées avec `NULL` pour ce champ. Sur une nouvelle base, le SQL initial
crée déjà la colonne et la migration accepte sa présence.

Ne supprimez pas le volume `pg_data` pour appliquer une migration.
Le retour à `20261009_base` (`alembic downgrade 20261009_base`) supprime
la colonne `comment` et tous les commentaires enregistrés.

## Questions et réponses initiales

`database/init/02-questions-answers.sql` charge 20 questions et 60 réponses
pour Paris (`departments = [75]`). Chaque réponse porte le conseil de sa
question ; la bonne réponse vaut 10 ou 15 points, les autres 0.
Les textes et les barèmes sont repris du document fourni, sans validation métier.

Le fichier est chargé uniquement à l'initialisation d'un volume PostgreSQL
vide, après la création du schéma. Il n'est pas rejoué au redémarrage des
conteneurs ni par les migrations Alembic. Une base existante reste inchangée.

Chaque bloc contient un `INSERT` pour la question puis un `INSERT` pour ses
trois réponses, avec des UUID explicites pour les relier. Il n'y a pas de
mise à jour automatique ni de gestion des doublons : ne pas rejouer ce fichier
sur une base déjà alimentée. Ne pas supprimer un volume existant pour charger
ce catalogue, car cela effacerait ses données.

Les annotations de liens et de navigation du document ne sont pas incluses.

## Hors périmètre de ce squelette

- Aucune logique métier dans services/ et utils/ pour le moment
- Pas de chargement automatique de données en dehors des scripts d'initialisation
- Pas de service IA dans ce compose (dev backend isolé ; stack complète dans le repo infra)