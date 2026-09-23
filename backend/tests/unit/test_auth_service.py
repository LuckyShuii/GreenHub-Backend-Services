"""Tests unitaires de AuthService, sans base de donnees.

Le service instancie lui-meme son UserRepository ; on substitue donc le
nom `UserRepository` dans le module `services.auth_service` par un double
en memoire. Ce qui est teste ici est la logique metier (detection du
doublon, hachage, mapping des champs), pas le SQL.
"""

from uuid import UUID

import pytest

from models.user_model import User
from schemas.user_schema import UserCreate
from services import auth_service as auth_service_module
from services.auth_service import (
    AuthService,
    EmailAlreadyUsedError,
    UsernameAlreadyUsedError,
)
from utils.security import verify_password

pytestmark = pytest.mark.unit


class FauxUserRepository:
    """Double en memoire de UserRepository (meme surface utilisee)."""

    def __init__(self, db=None):
        self.db = db
        self.utilisateurs: list[User] = []

    def get_by_email(self, email: str) -> User | None:
        return next(
            (u for u in self.utilisateurs if u.email == email), None
        )

    def get_by_username(self, username: str) -> User | None:
        return next(
            (u for u in self.utilisateurs if u.username == username),
            None,
        )

    def create(self, obj: User) -> User:
        obj.id = UUID("00000000-0000-0000-0000-000000000001")
        self.utilisateurs.append(obj)
        return obj


@pytest.fixture
def depot(monkeypatch: pytest.MonkeyPatch) -> FauxUserRepository:
    """Injecte le faux depot et renvoie l'instance utilisee par le service."""
    instance = FauxUserRepository()
    monkeypatch.setattr(
        auth_service_module, "UserRepository", lambda db: instance
    )
    return instance


@pytest.fixture
def service(depot: FauxUserRepository) -> AuthService:
    # La session est inutilisee : le faux depot ignore son argument.
    return AuthService(db=None)


def test_register_renvoie_l_utilisateur_cree(
    service: AuthService, user_create: UserCreate
):
    utilisateur = service.register(user_create)

    assert utilisateur.id is not None
    assert utilisateur.first_name == "Ada"
    assert utilisateur.last_name == "Lovelace"
    assert utilisateur.email == "ada@example.com"
    assert utilisateur.username == "ada"


def test_register_persiste_l_utilisateur(
    service: AuthService,
    depot: FauxUserRepository,
    user_create: UserCreate,
):
    service.register(user_create)

    assert len(depot.utilisateurs) == 1


def test_register_hache_le_mot_de_passe(
    service: AuthService, user_create: UserCreate
):
    utilisateur = service.register(user_create)

    assert utilisateur.password_hash != user_create.mot_de_passe
    assert verify_password(
        user_create.mot_de_passe, utilisateur.password_hash
    )


def test_register_refuse_un_email_deja_utilise(
    service: AuthService, user_create: UserCreate
):
    service.register(user_create)

    with pytest.raises(EmailAlreadyUsedError):
        service.register(user_create)


def test_register_n_ecrit_rien_si_l_email_est_deja_pris(
    service: AuthService,
    depot: FauxUserRepository,
    user_create: UserCreate,
):
    """Le doublon est detecte avant toute ecriture."""
    service.register(user_create)

    with pytest.raises(EmailAlreadyUsedError):
        service.register(user_create)

    assert len(depot.utilisateurs) == 1


def test_register_refuse_un_pseudonyme_deja_utilise(
    service: AuthService, payload_inscription: dict
):
    """Le pseudonyme est unique en base : le service le refuse avant.

    Sans ce garde-fou, l'insertion partirait jusqu'a PostgreSQL et
    remonterait une IntegrityError au lieu d'un 409 lisible.
    """
    service.register(UserCreate(**payload_inscription))

    with pytest.raises(UsernameAlreadyUsedError):
        service.register(
            UserCreate(
                **{**payload_inscription, "email": "grace@example.com"}
            )
        )


def test_register_n_ecrit_rien_si_le_pseudonyme_est_deja_pris(
    service: AuthService,
    depot: FauxUserRepository,
    payload_inscription: dict,
):
    service.register(UserCreate(**payload_inscription))

    with pytest.raises(UsernameAlreadyUsedError):
        service.register(
            UserCreate(
                **{**payload_inscription, "email": "grace@example.com"}
            )
        )

    assert len(depot.utilisateurs) == 1


def test_register_accepte_deux_utilisateurs_distincts(
    service: AuthService,
    depot: FauxUserRepository,
    payload_inscription: dict,
):
    """E-mail *et* pseudonyme differents : les deux doivent passer."""
    service.register(UserCreate(**payload_inscription))
    service.register(
        UserCreate(
            **{
                **payload_inscription,
                "email": "grace@example.com",
                "pseudonyme": "grace",
            }
        )
    )

    assert len(depot.utilisateurs) == 2
