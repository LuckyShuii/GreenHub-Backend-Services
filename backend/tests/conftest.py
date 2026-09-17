"""Fixtures partagees par toute la suite de tests.

Les fixtures qui touchent une vraie base vivent dans
`tests/integration/conftest.py` : ce fichier-ci ne doit contenir que des
outils utilisables sans aucune I/O.
"""

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from main import app
from schemas.user_schema import UserCreate


@pytest.fixture
def client() -> Iterator[TestClient]:
    """Client HTTP sur l'app complete, sans base de donnees.

    Les tests unitaires de routers remplacent la dependance `get_db` ou
    la couche service ; la fixture se contente de garantir que les
    surcharges posees par un test ne fuient pas vers le suivant.
    """
    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def payload_inscription() -> dict:
    """Corps JSON valide pour POST /api/auth/register.

    Les tests qui ciblent un cas d'erreur partent de ce dictionnaire et
    n'ecrasent que le champ qu'ils veulent invalider : la raison de
    l'echec attendu reste lisible dans le test.
    """
    return {
        "prenom": "Ada",
        "nom": "Lovelace",
        "email": "ada@example.com",
        "pseudonyme": "ada",
        "localisation": "Paris",
        "mot_de_passe": "MotDePasse1!",
    }


@pytest.fixture
def user_create(payload_inscription: dict) -> UserCreate:
    """Le meme utilisateur valide, deja valide par Pydantic."""
    return UserCreate(**payload_inscription)
