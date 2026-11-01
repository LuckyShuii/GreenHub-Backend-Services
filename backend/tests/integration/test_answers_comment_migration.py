"""Migration du commentaire optionnel des reponses, sur PostgreSQL."""

from importlib import import_module

import pytest
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

migration = import_module("migrations.versions.20261030_add_answers_comment")

pytestmark = pytest.mark.integration


def test_migration_depuis_schema_existant(db_session: Session) -> None:
    connexion = db_session.connection()
    connexion.execute(text("ALTER TABLE answers DROP COLUMN comment"))
    question_id = connexion.execute(
        text("INSERT INTO questions (question) VALUES ('Question test') RETURNING id")
    ).scalar_one()
    reponse_id = connexion.execute(
        text(
            "INSERT INTO answers (question_id, body) "
            "VALUES (:question_id, 'Reponse test') RETURNING id"
        ),
        {"question_id": question_id},
    ).scalar_one()

    with Operations.context(MigrationContext.configure(connexion)):
        migration.upgrade()
        colonne = next(
            c for c in inspect(connexion).get_columns("answers") if c["name"] == "comment"
        )
        assert str(colonne["type"]) == "TEXT"
        assert colonne["nullable"] is True
        assert colonne["default"] is None
        assert connexion.execute(
            text("SELECT body, comment FROM answers WHERE id = :id"),
            {"id": reponse_id},
        ).one() == ("Reponse test", None)

        commentaire = "Explication de la reponse\n" + "x" * 10000
        connexion.execute(
            text("UPDATE answers SET comment = :comment WHERE id = :id"),
            {"comment": commentaire, "id": reponse_id},
        )
        assert (
            connexion.execute(
                text("SELECT comment FROM answers WHERE id = :id"), {"id": reponse_id}
            ).scalar_one()
            == commentaire
        )

        migration.downgrade()
        assert "comment" not in {c["name"] for c in inspect(connexion).get_columns("answers")}
        assert (
            connexion.execute(
                text("SELECT body FROM answers WHERE id = :id"), {"id": reponse_id}
            ).scalar_one()
            == "Reponse test"
        )

        migration.upgrade()
        assert (
            connexion.execute(
                text("SELECT comment FROM answers WHERE id = :id"), {"id": reponse_id}
            ).scalar_one()
            is None
        )


def test_migration_depuis_schema_initialise(db_session: Session) -> None:
    connexion = db_session.connection()
    question_id = connexion.execute(
        text("INSERT INTO questions (question) VALUES ('Question test') RETURNING id")
    ).scalar_one()
    reponse_id = connexion.execute(
        text(
            "INSERT INTO answers (question_id, body, comment) "
            "VALUES (:question_id, 'Reponse test', 'Commentaire existant') RETURNING id"
        ),
        {"question_id": question_id},
    ).scalar_one()

    with Operations.context(MigrationContext.configure(connexion)):
        migration.upgrade()

    assert (
        connexion.execute(
            text("SELECT comment FROM answers WHERE id = :id"), {"id": reponse_id}
        ).scalar_one()
        == "Commentaire existant"
    )
