"""Tests unitaires de la dependance FastAPI `get_db`.

Cette fonction est surchargee partout ailleurs dans la suite : c'est le
seul endroit qui verifie son vrai comportement, notamment la fermeture
de la session (une session non fermee fuit une connexion du pool).
"""

import pytest

from database import deps

pytestmark = pytest.mark.unit


class SessionFactice:
    def __init__(self):
        self.fermee = False

    def close(self):
        self.fermee = True


@pytest.fixture
def session(monkeypatch: pytest.MonkeyPatch) -> SessionFactice:
    instance = SessionFactice()
    monkeypatch.setattr(deps, "SessionLocal", lambda: instance)
    return instance


def test_get_db_fournit_une_session(session: SessionFactice):
    generateur = deps.get_db()

    assert next(generateur) is session


def test_get_db_ferme_la_session_a_la_fin(session: SessionFactice):
    generateur = deps.get_db()
    next(generateur)

    assert not session.fermee

    with pytest.raises(StopIteration):
        next(generateur)

    assert session.fermee


def test_get_db_ferme_la_session_meme_en_cas_d_erreur(
    session: SessionFactice,
):
    """Une exception dans la route ne doit pas fuiter la connexion."""
    generateur = deps.get_db()
    next(generateur)

    with pytest.raises(RuntimeError):
        generateur.throw(RuntimeError("echec dans la route"))

    assert session.fermee
