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

## Hors périmètre de ce squelette

- Aucune logique métier dans services/ et utils/ pour le moment
- Pas de configuration externe (variables d'environnement, PostgreSQL)
- Pas de Dockerfile