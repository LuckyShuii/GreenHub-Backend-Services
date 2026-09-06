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

## Hors périmètre de ce squelette

- Aucune logique métier dans services/ et utils/ pour le moment
- Pas de schéma applicatif ni de seed joués automatiquement
- Pas de service IA dans ce compose (dev backend isolé ; stack complète dans le repo infra)