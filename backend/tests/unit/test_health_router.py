"""Tests unitaires des sondes de sante.

`/health` est une sonde de liveness pure (aucune dependance) ; `/health/db`
est testee ici avec une session factice, la vraie connexion etant couverte
par `tests/integration/test_health_db.py`.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from database.deps import get_db
from main import app
from routers.health import health_check

pytestmark = pytest.mark.unit


class FausseSession:
    """Session SQLAlchemy factice : execute() reussit ou leve."""

    def __init__(self, erreur: Exception | None = None):
        self.erreur = erreur
        self.requetes: list[str] = []

    def execute(self, statement):
        self.requetes.append(str(statement))
        if self.erreur is not None:
            raise self.erreur
        return None


def _brancher_session(session: FausseSession) -> None:
    app.dependency_overrides[get_db] = lambda: session


class TestLiveness:
    def test_health_renvoie_ok(self, client: TestClient):
        reponse = client.get("/health")

        assert reponse.status_code == 200
        assert reponse.json() == {"status": "ok"}

    @pytest.mark.asyncio
    async def test_health_check_est_une_coroutine(self):
        """Appel direct du handler async, hors pile HTTP."""
        assert await health_check() == {"status": "ok"}

    def test_health_n_est_pas_sous_le_prefixe_api(self, client: TestClient):
        """La sonde infra reste a la racine : /api/health n'existe pas."""
        assert client.get("/api/health").status_code == 404


class TestReadiness:
    def test_health_db_renvoie_ok_quand_la_base_repond(
        self, client: TestClient
    ):
        session = FausseSession()
        _brancher_session(session)

        reponse = client.get("/health/db")

        assert reponse.status_code == 200
        assert reponse.json() == {"status": "ok", "database": "reachable"}

    def test_health_db_execute_bien_une_requete(self, client: TestClient):
        session = FausseSession()
        _brancher_session(session)

        client.get("/health/db")

        assert session.requetes == ["SELECT 1"]

    def test_health_db_renvoie_503_si_la_base_est_injoignable(
        self, client: TestClient
    ):
        _brancher_session(
            FausseSession(
                erreur=OperationalError("SELECT 1", {}, Exception("down"))
            )
        )

        reponse = client.get("/health/db")

        assert reponse.status_code == 503
        assert reponse.json()["detail"] == "Database is unreachable."
