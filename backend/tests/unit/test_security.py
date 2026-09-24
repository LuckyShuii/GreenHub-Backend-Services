"""Tests unitaires de utils/security.py : mots de passe et jetons."""

import base64
import json
from datetime import UTC, datetime, timedelta
from uuid import UUID

import jwt
import pytest

from config.settings import settings
from utils.security import (
    ACCESS_TOKEN_TTL,
    InvalidAccessTokenError,
    create_access_token,
    decode_access_token,
    generate_refresh_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)

pytestmark = pytest.mark.unit

MOT_DE_PASSE = "MotDePasse1!"
IDENTIFIANT = UUID("00000000-0000-0000-0000-000000000001")


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


def _revendications_valides(**surcharges) -> dict:
    maintenant = datetime.now(UTC)
    revendications = {
        "sub": str(IDENTIFIANT),
        "type": "access",
        "iat": maintenant,
        "exp": maintenant + ACCESS_TOKEN_TTL,
    }
    revendications.update(surcharges)
    return revendications


def _signer(revendications: dict, cle: str | None = None) -> str:
    return jwt.encode(
        revendications, cle or settings.JWT_SECRET_KEY, algorithm="HS256"
    )


def _segment(donnees: dict) -> str:
    brut = json.dumps(donnees).encode("utf-8")
    return base64.urlsafe_b64encode(brut).rstrip(b"=").decode("ascii")


def test_le_jeton_d_acces_restitue_l_identifiant():
    assert decode_access_token(create_access_token(IDENTIFIANT)) == IDENTIFIANT


def test_le_jeton_d_acces_vit_quinze_minutes():
    revendications = jwt.decode(
        create_access_token(IDENTIFIANT), options={"verify_signature": False}
    )

    assert revendications["exp"] - revendications["iat"] == 15 * 60
    assert revendications["type"] == "access"


def test_un_jeton_d_acces_expire_est_refuse():
    emis_il_y_a_16_minutes = datetime.now(UTC) - timedelta(minutes=16)
    jeton = create_access_token(IDENTIFIANT, now=emis_il_y_a_16_minutes)

    with pytest.raises(InvalidAccessTokenError):
        decode_access_token(jeton)


def test_un_jeton_signe_avec_une_autre_cle_est_refuse():
    jeton = _signer(_revendications_valides(), cle="autre-cle-" + "y" * 48)

    with pytest.raises(InvalidAccessTokenError):
        decode_access_token(jeton)


def test_un_jeton_d_un_autre_type_est_refuse():
    jeton = _signer(_revendications_valides(type="refresh"))

    with pytest.raises(InvalidAccessTokenError):
        decode_access_token(jeton)


def test_un_jeton_non_signe_est_refuse():
    """alg=none : contournement de signature classique, jamais accepte."""
    maintenant = int(datetime.now(UTC).timestamp())
    jeton = ".".join(
        [
            _segment({"alg": "none", "typ": "JWT"}),
            _segment(
                {
                    "sub": str(IDENTIFIANT),
                    "type": "access",
                    "iat": maintenant,
                    "exp": maintenant + 900,
                }
            ),
            "",
        ]
    )

    with pytest.raises(InvalidAccessTokenError):
        decode_access_token(jeton)


def test_un_jeton_sans_expiration_est_refuse():
    revendications = _revendications_valides()
    del revendications["exp"]

    with pytest.raises(InvalidAccessTokenError):
        decode_access_token(_signer(revendications))


def test_un_sujet_qui_n_est_pas_un_uuid_est_refuse():
    jeton = _signer(_revendications_valides(sub="42"))

    with pytest.raises(InvalidAccessTokenError):
        decode_access_token(jeton)


@pytest.mark.parametrize(
    "jeton",
    [
        pytest.param("pas-un-jwt", id="malforme"),
        pytest.param("", id="vide"),
    ],
)
def test_un_jeton_malforme_est_refuse(jeton: str):
    with pytest.raises(InvalidAccessTokenError):
        decode_access_token(jeton)


def test_emettre_un_jeton_sans_cle_configuree_echoue(
    monkeypatch: pytest.MonkeyPatch,
):
    """Erreur de configuration : elle doit remonter, pas passer pour un 401."""
    monkeypatch.setattr(settings, "JWT_SECRET_KEY", None)

    with pytest.raises(RuntimeError):
        create_access_token(IDENTIFIANT)


def test_les_refresh_tokens_sont_uniques_et_longs():
    jetons = {generate_refresh_token() for _ in range(100)}

    assert len(jetons) == 100
    assert all(len(jeton) >= 64 for jeton in jetons)


def test_l_empreinte_d_un_refresh_token_est_un_sha256_deterministe():
    jeton = generate_refresh_token()

    empreinte = hash_refresh_token(jeton)

    assert empreinte == hash_refresh_token(jeton)
    assert len(empreinte) == 64
    assert empreinte != jeton
