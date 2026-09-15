"""Tests unitaires du hachage de mot de passe (utils/security.py)."""

import pytest

from utils.security import hash_password, verify_password

pytestmark = pytest.mark.unit

MOT_DE_PASSE = "MotDePasse1!"


def test_hash_password_ne_contient_pas_le_mot_de_passe_en_clair():
    empreinte = hash_password(MOT_DE_PASSE)

    assert MOT_DE_PASSE not in empreinte


def test_hash_password_produit_le_format_attendu():
    empreinte = hash_password(MOT_DE_PASSE)

    algo_tag, iterations, sel, derive = empreinte.split("$")
    assert algo_tag == "pbkdf2_sha256"
    assert int(iterations) >= 200_000
    # Sel de 16 octets et empreinte SHA-256, tous deux en hexadecimal.
    assert len(sel) == 32
    assert len(derive) == 64


def test_hash_password_sale_chaque_empreinte():
    """Deux utilisateurs avec le meme mot de passe n'ont pas le meme hash."""
    premiere = hash_password(MOT_DE_PASSE)
    seconde = hash_password(MOT_DE_PASSE)

    assert premiere != seconde


def test_verify_password_accepte_le_bon_mot_de_passe():
    assert verify_password(MOT_DE_PASSE, hash_password(MOT_DE_PASSE))


def test_verify_password_refuse_un_mauvais_mot_de_passe():
    assert not verify_password("MauvaisMdp1!", hash_password(MOT_DE_PASSE))


def test_verify_password_est_sensible_a_la_casse():
    assert not verify_password("motdepasse1!", hash_password(MOT_DE_PASSE))


@pytest.mark.parametrize(
    "stocke",
    [
        pytest.param("", id="chaine-vide"),
        pytest.param("pas-un-hash", id="sans-separateur"),
        pytest.param("pbkdf2_sha256$200000$abc", id="champ-manquant"),
        pytest.param(
            "pbkdf2_sha256$pas-un-entier$aa$bb", id="iterations-non-numeriques"
        ),
        pytest.param("pbkdf2_sha256$200000$zz$bb", id="sel-non-hexadecimal"),
        pytest.param("sha256$200000$aa$bb", id="tag-algo-sans-underscore"),
    ],
)
def test_verify_password_refuse_une_empreinte_malformee(stocke: str):
    """Une valeur corrompue en base renvoie False, sans lever d'exception."""
    assert not verify_password(MOT_DE_PASSE, stocke)
