"""Tests unitaires des schemas de session (schemas/auth_schema.py)."""

import pytest
from pydantic import ValidationError

from schemas.auth_schema import (
    LoginRequest,
    RefreshSessionRequest,
    TokenResponse,
)

pytestmark = pytest.mark.unit


def test_login_normalise_l_email():
    connexion = LoginRequest(
        email="  ADA@Example.COM ", mot_de_passe="x", device_info="device-1"
    )

    assert connexion.email == "ada@example.com"


def test_login_accepte_un_email_mal_forme():
    """Il finira en 401 comme un e-mail inconnu, pas en 422 revelateur."""
    connexion = LoginRequest(
        email="pas-un-email", mot_de_passe="x", device_info="device-1"
    )

    assert connexion.email == "pas-un-email"


def test_login_n_applique_pas_la_politique_de_mot_de_passe():
    connexion = LoginRequest(
        email="ada@example.com", mot_de_passe="court", device_info="device-1"
    )

    assert connexion.mot_de_passe == "court"


@pytest.mark.parametrize("champ", ["email", "mot_de_passe"])
def test_login_refuse_un_champ_vide(champ: str):
    corps = {
        "email": "ada@example.com",
        "mot_de_passe": "MotDePasse1!",
        "device_info": "device-1",
    }
    corps[champ] = ""

    with pytest.raises(ValidationError):
        LoginRequest(**corps)


def test_login_refuse_un_mot_de_passe_trop_long():
    with pytest.raises(ValidationError):
        LoginRequest(
            email="ada@example.com",
            mot_de_passe="a" * 129,
            device_info="device-1",
        )


def test_refresh_refuse_un_jeton_vide():
    with pytest.raises(ValidationError):
        RefreshSessionRequest(refresh_token="", device_info="device-1")


def test_refresh_exige_un_appareil():
    with pytest.raises(ValidationError):
        RefreshSessionRequest(refresh_token="refresh")


def test_la_reponse_de_jetons_est_de_type_bearer():
    jetons = TokenResponse(access_token="a", refresh_token="r", expires_in=900)

    assert jetons.token_type == "bearer"
