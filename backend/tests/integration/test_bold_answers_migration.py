"""Migration du gras Markdown sur les reponses du catalogue, sur PostgreSQL."""

import re
from importlib import import_module
from pathlib import Path

import pytest
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import text
from sqlalchemy.orm import Session

migration = import_module("migrations.versions.20261101_bold_answers")

pytestmark = pytest.mark.integration

SCRIPT = Path(__file__).resolve().parents[3] / "database" / "init" / "02-questions-answers.sql"


def _inserer_reponses(connexion, corps_par_id: dict[str, str]) -> None:
    question_id = connexion.execute(
        text("INSERT INTO questions (question) VALUES ('Question test') RETURNING id")
    ).scalar_one()
    connexion.execute(
        text("INSERT INTO answers (id, question_id, body) VALUES (:id, :question_id, :body)"),
        [
            {"id": reponse_id, "question_id": question_id, "body": corps}
            for reponse_id, corps in corps_par_id.items()
        ],
    )


def _corps(connexion) -> dict[str, str]:
    return {
        str(r.id): r.body for r in connexion.execute(text("SELECT id, body FROM answers")).all()
    }


def test_chaque_reponse_a_du_gras_coherent() -> None:
    assert len(migration.ANSWER_BODIES) == 60
    for _, plain, bold in migration.ANSWER_BODIES:
        assert "**" not in plain
        assert re.search(r"\*\*[^*]+\*\*", bold)
        assert bold.count("**") % 2 == 0
        assert bold.replace("**", "") == plain


def test_seed_aligne_sur_la_migration() -> None:
    script = SCRIPT.read_text(encoding="utf-8")
    for _, _, bold in migration.ANSWER_BODIES:
        assert "'" + bold.replace("'", "''") + "'" in script


def test_migration_met_les_reponses_en_gras(db_session: Session) -> None:
    connexion = db_session.connection()
    _inserer_reponses(connexion, {a: plain for a, plain, _ in migration.ANSWER_BODIES})

    with Operations.context(MigrationContext.configure(connexion)):
        migration.upgrade()
        attendu_gras = {a: bold for a, _, bold in migration.ANSWER_BODIES}
        assert _corps(connexion) == attendu_gras

        migration.upgrade()
        assert _corps(connexion) == attendu_gras

        migration.downgrade()
        assert _corps(connexion) == {a: plain for a, plain, _ in migration.ANSWER_BODIES}


def test_migration_ne_touche_pas_un_texte_modifie(db_session: Session) -> None:
    connexion = db_session.connection()
    reponse_id = migration.ANSWER_BODIES[0][0]
    _inserer_reponses(connexion, {reponse_id: "Texte edite a la main"})

    with Operations.context(MigrationContext.configure(connexion)):
        migration.upgrade()

    assert _corps(connexion) == {reponse_id: "Texte edite a la main"}
