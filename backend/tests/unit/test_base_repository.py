"""Tests unitaires du contrat d'ecriture de BaseRepository.

Seules les methodes qui orchestrent la session (ordre add/commit/refresh)
sont testables sans base. Les lectures (`get`, `get_all`, `get_by_email`)
produisent du SQL : elles sont couvertes par les tests d'integration, ou
une vraie requete PostgreSQL a du sens.
"""

import pytest

from models.user_model import User
from repositories.base import BaseRepository

pytestmark = pytest.mark.unit


class SessionEspion:
    """Enregistre les appels de session dans l'ordre ou ils surviennent."""

    def __init__(self):
        self.appels: list[tuple[str, object]] = []

    def add(self, obj):
        self.appels.append(("add", obj))

    def commit(self):
        self.appels.append(("commit", None))

    def refresh(self, obj):
        self.appels.append(("refresh", obj))

    def delete(self, obj):
        self.appels.append(("delete", obj))


@pytest.fixture
def session() -> SessionEspion:
    return SessionEspion()


@pytest.fixture
def depot(session: SessionEspion) -> BaseRepository[User]:
    return BaseRepository(User, session)


@pytest.fixture
def utilisateur() -> User:
    return User(
        first_name="Ada",
        last_name="Lovelace",
        email="ada@example.com",
        username="ada",
        password_hash="pbkdf2_sha256$200000$aa$bb",
    )


def test_create_ajoute_commite_puis_rafraichit(
    depot: BaseRepository[User],
    session: SessionEspion,
    utilisateur: User,
):
    depot.create(utilisateur)

    assert [nom for nom, _ in session.appels] == [
        "add",
        "commit",
        "refresh",
    ]


def test_create_renvoie_l_objet_rafraichi(
    depot: BaseRepository[User], utilisateur: User
):
    assert depot.create(utilisateur) is utilisateur


def test_update_commite_sans_re_ajouter_l_objet(
    depot: BaseRepository[User],
    session: SessionEspion,
    utilisateur: User,
):
    """L'objet est deja suivi par la session : pas de `add`."""
    depot.update(utilisateur)

    assert [nom for nom, _ in session.appels] == ["commit", "refresh"]


def test_delete_supprime_puis_commite(
    depot: BaseRepository[User],
    session: SessionEspion,
    utilisateur: User,
):
    depot.delete(utilisateur)

    assert session.appels == [
        ("delete", utilisateur),
        ("commit", None),
    ]


def test_delete_ne_renvoie_rien(
    depot: BaseRepository[User], utilisateur: User
):
    assert depot.delete(utilisateur) is None
