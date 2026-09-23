"""Tests d'integration de UserRepository contre PostgreSQL.

Les lectures produisent du vrai SQL : c'est ici, et pas en unitaire, que
la contrainte d'unicite et le comportement de l'index sont verifiables.
"""

from uuid import UUID

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from models.user_model import User
from repositories.user_repository import UserRepository

pytestmark = pytest.mark.integration


def _utilisateur(email: str = "ada@example.com", **surcharges) -> User:
    champs = {
        "first_name": "Ada",
        "last_name": "Lovelace",
        "email": email,
        "username": "ada",
        "password_hash": "pbkdf2_sha256$200000$aa$bb",
    }
    champs.update(surcharges)
    return User(**champs)


@pytest.fixture
def depot(db_session: Session) -> UserRepository:
    return UserRepository(db_session)


def test_create_attribue_un_identifiant(depot: UserRepository):
    utilisateur = depot.create(_utilisateur())

    assert utilisateur.id is not None


def test_create_remplit_la_date_de_creation(depot: UserRepository):
    """`server_default=now()` : la valeur vient de PostgreSQL."""
    utilisateur = depot.create(_utilisateur())

    assert utilisateur.created_at is not None
    assert utilisateur.created_at.tzinfo is not None


def test_get_retrouve_l_utilisateur_par_identifiant(
    depot: UserRepository,
):
    cree = depot.create(_utilisateur())

    assert depot.get(cree.id) is cree


def test_get_renvoie_none_pour_un_identifiant_inconnu(
    depot: UserRepository,
):
    assert depot.get(UUID("00000000-0000-0000-0000-000000000099")) is None


def test_get_by_email_retrouve_l_utilisateur(depot: UserRepository):
    depot.create(_utilisateur())

    trouve = depot.get_by_email("ada@example.com")

    assert trouve is not None
    assert trouve.username == "ada"


def test_get_by_email_renvoie_none_si_absent(depot: UserRepository):
    assert depot.get_by_email("inconnu@example.com") is None


def test_get_by_email_est_sensible_a_la_casse(depot: UserRepository):
    """La colonne n'est pas citext : c'est le schema qui normalise.

    Ce test fige le comportement reel de la requete ; si un jour la
    normalisation doit vivre en base, il echouera et devra etre revu.
    """
    depot.create(_utilisateur())

    assert depot.get_by_email("ADA@example.com") is None


def test_get_all_renvoie_les_utilisateurs_crees(depot: UserRepository):
    depot.create(_utilisateur("ada@example.com"))
    depot.create(_utilisateur("grace@example.com", pseudonyme="grace"))

    emails = {u.email for u in depot.get_all()}

    assert emails == {"ada@example.com", "grace@example.com"}


def test_la_base_est_vide_au_debut_de_chaque_test(depot: UserRepository):
    """Garde-fou d'isolation : le test precedent a bien ete annule."""
    assert depot.get_all() == []


def test_l_email_est_unique_en_base(
    depot: UserRepository, db_session: Session
):
    """L'unicite ne repose pas que sur la verification applicative."""
    depot.create(_utilisateur())

    with pytest.raises(IntegrityError):
        depot.create(_utilisateur(pseudonyme="autre"))

    db_session.rollback()


def test_update_persiste_la_modification(
    depot: UserRepository, db_session: Session
):
    utilisateur = depot.create(_utilisateur())

    utilisateur.username = "ada_l"
    depot.update(utilisateur)
    db_session.expire_all()

    assert depot.get(utilisateur.id).username == "ada_l"


def test_delete_supprime_l_utilisateur(depot: UserRepository):
    utilisateur = depot.create(_utilisateur())
    identifiant = utilisateur.id

    depot.delete(utilisateur)

    assert depot.get(identifiant) is None
