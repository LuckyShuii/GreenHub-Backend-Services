# Tests backend

**Où :** toutes les commandes se lancent depuis `backend/`, jamais depuis
la racine du dépôt (pytest a besoin de `backend/` dans `sys.path` pour
résoudre `from routers import ...`).

**Résultat attendu :** `90 passed`. Si vous voyez `63 passed, 27 skipped`,
les tests d'intégration ont été ignorés faute de base — voir
[Résoudre les problèmes](#résoudre-les-problèmes).

## Premier lancement

Deux façons de faire, au choix. La plus simple est la seconde.

### Option A — depuis votre machine

Il vous faut [uv](https://docs.astral.sh/uv/) et Docker.

```bash
# 1. Depuis la racine du dépôt : credentials + base de données
cp .env.example .env          # renseigner DB_USER et DB_PASSWORD
docker compose up -d postgres

# 2. Depuis backend/ : dépendances puis tests
cd backend
uv sync                       # installe aussi pytest & co (groupe dev)
uv run pytest
```

### Option B — depuis le conteneur backend

Rien à installer localement : ni Python, ni uv. Le conteneur contient
déjà pytest et joint la base par le réseau interne du compose.

```bash
# Depuis la racine du dépôt
cp .env.example .env          # renseigner DB_USER et DB_PASSWORD
docker compose up -d
docker compose exec backend pytest
```

## Commandes courantes

Depuis `backend/` (ou préfixées de `docker compose exec backend` en
option B, sans le `uv run`) :

| Commande | Ce qu'elle fait |
|---|---|
| `uv run pytest` | suite complète + couverture — **c'est celle à lancer avant une PR** |
| `uv run pytest -m unit --no-cov` | unitaires seuls, ~3 s, aucune base requise |
| `uv run pytest -m integration --no-cov` | intégration seule, PostgreSQL requis |
| `uv run pytest tests/unit/test_security.py --no-cov` | un seul fichier |
| `uv run pytest -k register --no-cov` | tous les tests dont le nom contient `register` |
| `uv run pytest -x -q --no-cov` | s'arrête au premier échec |
| `uv run pytest -vv --no-cov` | nom de chaque test, utile pour lire un échec |
| `uv run pytest --cov-report=html` | rapport HTML dans `htmlcov/index.html` |

`--no-cov` sur les lancements partiels : le seuil de couverture suppose la
suite complète et échouerait à tort sur un sous-ensemble.

## Résoudre les problèmes

**`27 skipped` — les tests d'intégration sont ignorés.** C'est volontaire
en local quand aucune base n'est joignable, et le message de skip dit
quoi faire. Deux causes :

- `aucun DB_USER trouve` → il manque le `.env` **à la racine du dépôt**
  (pas dans `backend/`) : `cp .env.example .env` puis renseignez
  `DB_USER` / `DB_PASSWORD` ;
- sinon la base n'est pas démarrée → `docker compose up -d postgres`.

En CI (`CI=true`), ces tests **échouent** au lieu d'être ignorés : un
service indisponible sur la CI est un bug d'infrastructure, pas une
excuse pour une PR verte.

**`ModuleNotFoundError: No module named 'main'`** — vous lancez pytest
depuis la racine du dépôt. Placez-vous dans `backend/`.

**`La base de test doit avoir un nom suffixe par '_test'`** — votre
`TEST_DATABASE_URL` pointe sur une base qui n'est pas une base de test.
Le garde-fou vous a évité d'écrire dans la base de dev.

**La couverture échoue sous 90 %** — voir [Couverture de code](#couverture-de-code).

## Base de test

Les tests ne touchent **jamais** la base de développement `greener`. Ils
tournent sur `greener_test`, **créée automatiquement** au premier
lancement. La cible est résolue dans cet ordre :

1. `TEST_DATABASE_URL` — utilisée par la CI ;
2. les variables `DB_*` de l'environnement — cas du conteneur backend,
   qui reçoit `DB_HOST=postgres` par le compose ;
3. le `.env` **à la racine du dépôt**, sur la base `greener_test`.

Le point 3 est lu directement par `tests/integration/conftest.py`, et non
via `config/settings.py` : celui-ci charge `.env` relativement au
répertoire courant, donc lancé depuis `backend/` il ne verrait pas le
`.env` de la racine — et les tests d'intégration seraient ignorés en
silence alors qu'une base tourne.

Un garde-fou refuse de démarrer si le nom de la base ne se termine pas par
`_test` : un `TEST_DATABASE_URL` mal copié ne peut pas altérer la base de
dev.

Le schéma est créé en jouant les **migrations Alembic**, pas un
`create_all()` : une migration oubliée fait échouer la suite.

Chaque test tourne dans une transaction annulée à la fin (les `commit()`
des repositories deviennent des `SAVEPOINT`). La base est donc vide au
début de chaque test, sans recréation ni ordre d'exécution imposé.

## Arborescence

```
backend/tests/
├── conftest.py            # fixtures partagées, sans aucune I/O
├── unit/                  # aucun accès réseau ni base de données
│   ├── test_security.py
│   ├── test_user_schema.py
│   ├── test_deps.py
│   ├── test_base_repository.py
│   ├── test_auth_service.py
│   ├── test_auth_router.py
│   └── test_health_router.py
└── integration/
    ├── conftest.py        # moteur, session transactionnelle, client API
    ├── test_database.py
    ├── test_user_repository.py
    └── test_auth_register.py
```

Le fichier de test **reflète le module testé** :
`services/auth_service.py` → `tests/unit/test_auth_service.py`.

## Conventions de nommage

| Élément | Convention | Exemple |
|---|---|---|
| Fichier | `test_<module_teste>.py` | `test_auth_service.py` |
| Classe (optionnelle, pour regrouper) | `Test<Sujet>` | `class TestUserCreate:` |
| Fonction | `test_<sujet>_<comportement_attendu>` | `test_register_refuse_un_email_deja_utilise` |
| Fixture | nom du rôle, sans préfixe `test_` | `db_session`, `client_api`, `payload_inscription` |
| Double de test | `Faux<Classe>` / `<Classe>Espion` | `FauxUserRepository`, `SessionEspion` |
| Cas paramétré | `id=` explicite en kebab-case | `pytest.param("ada@", id="sans-domaine")` |

Règles :

- **En français**, comme le reste du code métier du dépôt.
- Le nom décrit le **comportement attendu**, pas la mécanique : on lit
  `test_le_doublon_ne_cree_pas_de_second_utilisateur`, pas `test_register_2`.
- **Un comportement par test.** Un `assert` sur plusieurs champs d'un même
  résultat est acceptable ; deux scénarios dans un test ne le sont pas.
- Corps en trois temps séparés par une ligne vide : préparation, action,
  vérification.
- Un test non évident porte une **docstring** qui explique *pourquoi* le
  comportement est attendu, pas ce que fait le code.
- PEP8 comme le reste du backend : 4 espaces, 79 caractères maximum.

## Marqueurs

Déclarés dans `pyproject.toml`, `--strict-markers` rejette tout marqueur
inconnu (une faute de frappe échoue au lieu de passer inaperçue).

| Marqueur | Signification |
|---|---|
| `unit` | aucune I/O : ni base, ni réseau, ni système de fichiers |
| `integration` | nécessite un vrai PostgreSQL/PostGIS |

Le marqueur se pose une fois par fichier :

```python
pytestmark = pytest.mark.unit
```

Un test `async` doit porter `@pytest.mark.asyncio` (`asyncio_mode = "strict"`) :
le mode automatique masque les tests async qu'on a oublié de faire tourner.

## Que teste-t-on à quel niveau ?

| Couche | Niveau | Pourquoi |
|---|---|---|
| `utils/`, `schemas/` | unitaire | fonctions pures, aucun contexte à monter |
| `services/` | unitaire (repository simulé) | c'est la logique métier qu'on isole |
| `routers/` | unitaire (service simulé) | on ne teste que le contrat HTTP : codes, corps, validation |
| `repositories/` | intégration | ce sont des adaptateurs SQL : les simuler ne prouverait rien |
| migrations, contraintes, PostGIS | intégration | seul PostgreSQL peut les valider |
| parcours complet HTTP → base | intégration | le seul niveau qui prouve que la chaîne tient |

Les lectures de `BaseRepository` (`get`, `get_all`) ne sont **pas**
testées avec une fausse session : simuler `query().filter().first()`
reviendrait à tester la simulation. Seule l'orchestration
`add`/`commit`/`refresh` l'est.

## Couverture de code

Mesurée par `pytest-cov`, configurée dans `pyproject.toml`.

| | Valeur |
|---|---|
| **Seuil bloquant** (`--cov-fail-under`) | **90 %** — sous ce seuil, la CI échoue |
| **Cible sur `services/`, `schemas/`, `utils/`, `repositories/`** | **100 %** — c'est la logique métier |
| Mesuré à ce jour, suite complète | **100 %** (187 instructions) |

Le seuil est volontairement proche du réel : un plancher très bas laisse
la couverture s'éroder pendant des mois sans que rien n'échoue.

Exclus du calcul (`[tool.coverage.run] omit`) : `tests/` et `migrations/`
(jouées par Alembic, pas par la suite).

Le seuil suppose la **suite complète**. Pour ne lancer qu'une partie,
désactivez la couverture : `uv run pytest -m unit --no-cov`.

Rapport détaillé en local :

```bash
uv run pytest --cov-report=html
# puis ouvrir htmlcov/index.html
```

La couverture est un **garde-fou, pas un objectif** : 100 % de lignes
exécutées ne dit rien des cas limites. Un `if` couvert par un seul de ses
deux chemins compte comme couvert. Les cas d'erreur (409, 422, base
injoignable, empreinte corrompue) valent plus que quelques lignes de
plus.

## Ajouter un test — checklist

- [ ] Le fichier porte le nom du module testé, dans `unit/` ou `integration/`
- [ ] `pytestmark = pytest.mark.unit` (ou `integration`) en tête de fichier
- [ ] Le nom du test décrit le comportement attendu, en français
- [ ] Le cas d'erreur est couvert, pas seulement le cas nominal
- [ ] Aucune donnée n'est laissée en base (c'est automatique via `db_session`)
- [ ] `uv run pytest` passe en local avant d'ouvrir la PR

## CI

`.github/workflows/backend-tests.yml` — sur chaque PR et chaque push vers
`main` et `staging`.

Le job démarre un service `postgis/postgis:16-3.4-alpine` (même image que
`docker-compose.yml`), installe les dépendances avec `uv sync --frozen`
sur Python 3.12 (même version que les Dockerfiles), lance la suite
complète et publie `coverage.xml` en artefact.

Le job échoue si un test échoue, si la couverture passe sous 90 %, ou si
`uv.lock` n'est plus cohérent avec `pyproject.toml` (`--frozen`).
