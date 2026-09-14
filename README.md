# GreenHub-Backend-Services

Base applicative FastAPI minimale, avec une route de santé et la
documentation Swagger générée automatiquement.

## Préfixe /api — mêmes URLs en local et en prod

**Le backend porte lui-même le préfixe `/api`** : toutes les routes métier sont
montées sous `/api` par l'application (`api_router` dans `main.py`), pas par un
proxy. La gateway nginx de prod ne fait que router `/api/` vers le backend,
**sans réécrire l'URL**.

Conséquence : le chemin appelé par le front est identique partout, seul l'hôte
change.

| | base URL | exemple |
|---|---|---|
| dev (ce repo, `docker compose up`) | `http://localhost:8000` | `http://localhost:8000/api/...` |
| dev stack complète (repo infra) | `http://localhost:8080` | `http://localhost:8080/api/...` |
| production | `https://api.<domaine>` | `https://api.<domaine>/api/...` |

`/health` est délibérément **hors** `/api` : c'est une sonde infra (healthcheck
du conteneur et de la gateway), pas une route d'API.

Ajouter une route métier = la monter sur `api_router`, jamais sur `app`
directement, sinon elle sera injoignable derrière la gateway (qui ne route que
`/api/`, `/ai/` et `/health`).

## Structure

backend/
├── main.py           # point d'entrée FastAPI, monte les routers sous /api
├── routers/
│   └── health.py      # route GET /health (sonde infra, hors /api)
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

Générée automatiquement par FastAPI, servie sous `/api` comme le reste de l'API
(donc joignable à l'identique derrière la gateway) :

- http://localhost:8000/api/docs — Swagger UI interactif (tester les routes depuis le navigateur)
- http://localhost:8000/api/redoc — documentation alternative (ReDoc)
- http://localhost:8000/api/openapi.json — schéma OpenAPI brut

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
> infrastructure ; ce compose-ci ne sert qu'au dev backend. Pas de gateway ici :
> elle serait inutile puisque le backend sert déjà `/api` lui-même (voir plus
> haut) — les chemins sont donc les mêmes que sur la stack complète et en prod.

Démarrage :

    cp .env.example .env      # renseigner DB_USER / DB_PASSWORD
    docker compose up -d

Vérifier que la base est prête :

    docker compose ps         # postgres "healthy" (pg_isready), backend démarré
    docker compose exec postgres psql -U "$DB_USER" -d greener -c "SELECT postgis_version();"
    curl http://localhost:8000/health   # {"status": "ok"}
    open http://localhost:8000/api/docs  # les routes métier, telles que le front les appellera

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