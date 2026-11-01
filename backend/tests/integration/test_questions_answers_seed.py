"""Chargement initial du catalogue de quiz parisien."""

from pathlib import Path

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

pytestmark = pytest.mark.integration

SCRIPT = Path(__file__).resolve().parents[3] / "database" / "init" / "02-questions-answers.sql"


def test_catalogue_questions_initial(db_session: Session) -> None:
    connexion = db_session.connection()
    script = SCRIPT.read_text(encoding="utf-8")
    connexion.execute(text(script))

    questions = connexion.execute(
        text("SELECT id, question, departments FROM questions ORDER BY id")
    ).all()
    reponses = connexion.execute(
        text("SELECT id, question_id, body, is_correct, points, comment FROM answers ORDER BY id")
    ).all()
    assert len(questions) == 20
    assert len(reponses) == 60
    bonnes_reponses = [1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 3, 2, 2, 2, 2, 2, 2, 1, 2, 2]
    questions_bonus = {11, 14, 15, 16, 17, 18, 19}
    for numero, question in enumerate(questions, start=1):
        assert question.departments == [75]
        choix = [r for r in reponses if r.question_id == question.id]
        assert len(choix) == 3
        assert [r.is_correct for r in choix] == [
            position == bonnes_reponses[numero - 1] for position in range(1, 4)
        ]
        assert len({r.comment for r in choix}) == 1
        assert choix[0].comment
        assert all(r.body for r in choix)
        for reponse in choix:
            assert reponse.points == (
                (15 if numero in questions_bonus else 10) if reponse.is_correct else 0
            )
