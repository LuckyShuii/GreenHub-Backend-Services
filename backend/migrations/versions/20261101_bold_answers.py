"""Highlight the key part of every seeded answer with Markdown bold.

Revision ID: 20261101_bold_answers
Revises: 20261030_add_answers_comment
"""

from alembic import op
from sqlalchemy import text

revision = "20261101_bold_answers"
down_revision = "20261030_add_answers_comment"
branch_labels = None
depends_on = None

# (answer id, plain body, bold body), mirrored in database/init/02-questions-answers.sql.
ANSWER_BODIES = [
    ("47524841-0000-4000-8000-000000000011", "Bac jaune", "**Bac jaune**"),
    ("47524841-0000-4000-8000-000000000012", "Poubelle noire", "**Poubelle noire**"),
    ("47524841-0000-4000-8000-000000000013", "Colonne à verre", "**Colonne à verre**"),
    (
        "47524841-0000-4000-8000-000000000021",
        "Bac jaune, comme tout carton",
        "**Bac jaune**, comme tout carton",
    ),
    ("47524841-0000-4000-8000-000000000022", "Poubelle noire", "**Poubelle noire**"),
    ("47524841-0000-4000-8000-000000000023", "Compost", "**Compost**"),
    (
        "47524841-0000-4000-8000-000000000031",
        "Dans un bac bleu séparé pour le papier",
        "Dans un **bac bleu** séparé pour le papier",
    ),
    (
        "47524841-0000-4000-8000-000000000032",
        "Dans le même bac jaune que les emballages",
        "Dans le même **bac jaune** que les emballages",
    ),
    ("47524841-0000-4000-8000-000000000033", "À la déchetterie", "À la **déchetterie**"),
    (
        "47524841-0000-4000-8000-000000000041",
        "La déchetterie, car c'est dangereux",
        "**La déchetterie**, car c'est dangereux",
    ),
    ("47524841-0000-4000-8000-000000000042", "Le bac jaune", "**Le bac jaune**"),
    ("47524841-0000-4000-8000-000000000043", "La poubelle noire", "**La poubelle noire**"),
    (
        "47524841-0000-4000-8000-000000000051",
        "Le laisser à côté du bac",
        "Le laisser **à côté du bac**",
    ),
    (
        "47524841-0000-4000-8000-000000000052",
        "L'apporter en déchetterie ou via Trimobile Paris",
        "L'apporter **en déchetterie** ou via **Trimobile Paris**",
    ),
    (
        "47524841-0000-4000-8000-000000000053",
        "Le découper en confettis et le jeter en plusieurs fois",
        "Le **découper en confettis** et le jeter en plusieurs fois",
    ),
    ("47524841-0000-4000-8000-000000000061", "Le bac jaune", "**Le bac jaune**"),
    (
        "47524841-0000-4000-8000-000000000062",
        "La colonne à verre ou le bac blanc (Paris)",
        "**La colonne à verre** ou **le bac blanc** (Paris)",
    ),
    ("47524841-0000-4000-8000-000000000063", "La poubelle noire", "**La poubelle noire**"),
    (
        "47524841-0000-4000-8000-000000000071",
        "La colonne à verre, comme tout le verre",
        "**La colonne à verre**, comme tout le verre",
    ),
    ("47524841-0000-4000-8000-000000000072", "La déchetterie", "**La déchetterie**"),
    ("47524841-0000-4000-8000-000000000073", "Le bac jaune", "**Le bac jaune**"),
    (
        "47524841-0000-4000-8000-000000000081",
        "Le jeter directement dans la colonne à verre",
        "Le jeter directement dans **la colonne à verre**",
    ),
    (
        "47524841-0000-4000-8000-000000000082",
        "L'emballer dans du papier journal puis le mettre en poubelle noire",
        "L'emballer dans du papier journal puis le mettre en **poubelle noire**",
    ),
    (
        "47524841-0000-4000-8000-000000000083",
        "Le mettre dans le bac jaune avec les autres déchets cassants",
        "Le mettre dans **le bac jaune** avec les autres déchets cassants",
    ),
    ("47524841-0000-4000-8000-000000000091", "Le bac jaune", "**Le bac jaune**"),
    (
        "47524841-0000-4000-8000-000000000092",
        "Une borne biodéchets, un Trilib' ou un composteur",
        "Une **borne biodéchets**, un **Trilib'** ou un **composteur**",
    ),
    ("47524841-0000-4000-8000-000000000093", "La poubelle noire", "**La poubelle noire**"),
    (
        "47524841-0000-4000-8000-000000000101",
        "La borne biodéchets, comme tout reste alimentaire",
        "**La borne biodéchets**, comme tout reste alimentaire",
    ),
    ("47524841-0000-4000-8000-000000000102", "La poubelle noire", "**La poubelle noire**"),
    (
        "47524841-0000-4000-8000-000000000103",
        "Le compost à la maison uniquement",
        "**Le compost à la maison** uniquement",
    ),
    ("47524841-0000-4000-8000-000000000111", "Bac jaune", "**Bac jaune**"),
    ("47524841-0000-4000-8000-000000000112", "Poubelle noire", "**Poubelle noire**"),
    (
        "47524841-0000-4000-8000-000000000113",
        "Point de collecte dédié (supermarché, pharmacie, Trilib')",
        "**Point de collecte dédié** (supermarché, pharmacie, Trilib')",
    ),
    (
        "47524841-0000-4000-8000-000000000121",
        "À la poubelle noire, dans un sac fermé",
        "À **la poubelle noire**, dans un sac fermé",
    ),
    ("47524841-0000-4000-8000-000000000122", "En pharmacie", "En **pharmacie**"),
    (
        "47524841-0000-4000-8000-000000000123",
        "Dans les toilettes pour les formes liquides",
        "Dans **les toilettes** pour les formes liquides",
    ),
    (
        "47524841-0000-4000-8000-000000000131",
        "La poubelle noire, ils sont trop abîmés",
        "**La poubelle noire**, ils sont trop abîmés",
    ),
    (
        "47524841-0000-4000-8000-000000000132",
        "Un conteneur textile dédié sur la voie publique",
        "Un **conteneur textile** dédié sur la voie publique",
    ),
    (
        "47524841-0000-4000-8000-000000000133",
        "Le bac jaune avec les autres matières recyclables",
        "**Le bac jaune** avec les autres matières recyclables",
    ),
    (
        "47524841-0000-4000-8000-000000000141",
        "Dans l'évier, en petite quantité",
        "Dans **l'évier**, en petite quantité",
    ),
    (
        "47524841-0000-4000-8000-000000000142",
        "Dans une borne dédiée (Trilib') ou en déchetterie",
        "Dans une **borne dédiée (Trilib')** ou en **déchetterie**",
    ),
    (
        "47524841-0000-4000-8000-000000000143",
        "Dans le bac jaune, dans une bouteille fermée",
        "Dans **le bac jaune**, dans une bouteille fermée",
    ),
    (
        "47524841-0000-4000-8000-000000000151",
        "Dans la poubelle noire, bien refermée",
        "Dans **la poubelle noire**, bien refermée",
    ),
    (
        "47524841-0000-4000-8000-000000000152",
        "En pharmacie ou en déchetterie",
        "En **pharmacie** ou en **déchetterie**",
    ),
    (
        "47524841-0000-4000-8000-000000000153",
        "Dans le bac jaune avec les autres déchets médicaux",
        "Dans **le bac jaune** avec les autres déchets médicaux",
    ),
    (
        "47524841-0000-4000-8000-000000000161",
        "Le bac jaune, comme tout papier",
        "**Le bac jaune**, comme tout papier",
    ),
    ("47524841-0000-4000-8000-000000000162", "La poubelle noire", "**La poubelle noire**"),
    ("47524841-0000-4000-8000-000000000163", "La déchetterie", "**La déchetterie**"),
    ("47524841-0000-4000-8000-000000000171", "Le bac jaune", "**Le bac jaune**"),
    ("47524841-0000-4000-8000-000000000172", "La poubelle noire", "**La poubelle noire**"),
    ("47524841-0000-4000-8000-000000000173", "Le compost", "**Le compost**"),
    (
        "47524841-0000-4000-8000-000000000181",
        "Le bac jaune, comme une enveloppe normale",
        "**Le bac jaune**, comme une enveloppe normale",
    ),
    (
        "47524841-0000-4000-8000-000000000182",
        "La poubelle noire, à cause du plastique",
        "**La poubelle noire**, à cause du plastique",
    ),
    (
        "47524841-0000-4000-8000-000000000183",
        "Il faut retirer la fenêtre avant de jeter",
        "Il faut **retirer la fenêtre** avant de jeter",
    ),
    (
        "47524841-0000-4000-8000-000000000191",
        "Le bac jaune, c'est du métal",
        "**Le bac jaune**, c'est du métal",
    ),
    (
        "47524841-0000-4000-8000-000000000192",
        "Une filière de collecte dédiée (boutique ou point de collecte spécifique)",
        "Une **filière de collecte dédiée** (boutique ou point de collecte spécifique)",
    ),
    ("47524841-0000-4000-8000-000000000193", "La poubelle noire", "**La poubelle noire**"),
    (
        "47524841-0000-4000-8000-000000000201",
        "Le bac jaune avec les papiers",
        "**Le bac jaune** avec les papiers",
    ),
    ("47524841-0000-4000-8000-000000000202", "La poubelle noire", "**La poubelle noire**"),
    (
        "47524841-0000-4000-8000-000000000203",
        "Le compost, comme tout papier",
        "**Le compost**, comme tout papier",
    ),
]


def _replace_bodies(from_index: int, to_index: int) -> None:
    # Only touches seeded rows that still have the expected text.
    op.get_bind().execute(
        text("UPDATE answers SET body = :new_body WHERE id = :id AND body = :old_body"),
        [
            {"id": row[0], "old_body": row[from_index], "new_body": row[to_index]}
            for row in ANSWER_BODIES
        ],
    )


def upgrade() -> None:
    _replace_bodies(1, 2)


def downgrade() -> None:
    _replace_bodies(2, 1)
