"""Parcours complet de session : HTTP -> service -> PostgreSQL.

Seul endroit qui prouve que la session par appareil tient reellement en base,
au-dela des doubles des tests unitaires.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from models.session_model import UserSession
from utils.security import hash_refresh_token

pytestmark = pytest.mark.integration

URL_REGISTER = "/api/auth/register"
URL_LOGIN = "/api/auth/login"
URL_REFRESH = "/api/auth/refresh"
URL_LOGOUT = "/api/auth/logout"
URL_ME = "/api/auth/me"


@pytest.fixture
def identifiants(client_api: TestClient, payload_inscription: dict) -> dict:
    client_api.post(URL_REGISTER, json=payload_inscription)
    return {
        "email": payload_inscription["email"],
        "mot_de_passe": payload_inscription["mot_de_passe"],
        "device_info": "device-1",
    }


def _connecter(client_api: TestClient, identifiants: dict) -> dict:
    reponse = client_api.post(URL_LOGIN, json=identifiants)
    assert reponse.status_code == 200
    return reponse.json()


def _rafraichir(
    client_api: TestClient,
    refresh_token: str,
    device_info: str = "device-1",
):
    return client_api.post(
        URL_REFRESH,
        json={"refresh_token": refresh_token, "device_info": device_info},
    )


def test_le_jeton_d_acces_ouvre_la_route_me(
    client_api: TestClient, identifiants: dict
):
    jetons = _connecter(client_api, identifiants)

    reponse = client_api.get(
        URL_ME, headers={"Authorization": f"Bearer {jetons['access_token']}"}
    )

    assert reponse.status_code == 200
    assert reponse.json()["email"] == "ada@example.com"


def test_seule_l_empreinte_du_refresh_token_est_stockee(
    client_api: TestClient, db_session: Session, identifiants: dict
):
    jetons = _connecter(client_api, identifiants)

    sessions = db_session.query(UserSession).all()

    assert len(sessions) == 1
    assert sessions[0].refresh_token_hash == hash_refresh_token(
        jetons["refresh_token"]
    )
    assert sessions[0].refresh_token_hash != jetons["refresh_token"]


def test_email_inconnu_et_mauvais_mot_de_passe_sont_indistincts(
    client_api: TestClient, identifiants: dict
):
    mauvais_mot_de_passe = client_api.post(
        URL_LOGIN, json={**identifiants, "mot_de_passe": "MauvaisMdp1!"}
    )
    email_inconnu = client_api.post(
        URL_LOGIN, json={**identifiants, "email": "inconnu@example.com"}
    )

    assert mauvais_mot_de_passe.status_code == 401
    assert email_inconnu.status_code == 401
    assert mauvais_mot_de_passe.json() == email_inconnu.json()


def test_le_refresh_conserve_le_jeton_et_la_ligne(
    client_api: TestClient, db_session: Session, identifiants: dict
):
    jetons = _connecter(client_api, identifiants)

    reponse = _rafraichir(client_api, jetons["refresh_token"])

    assert reponse.status_code == 200
    assert reponse.json()["refresh_token"] == jetons["refresh_token"]
    sessions = db_session.query(UserSession).all()
    assert len(sessions) == 1
    assert sessions[0].revoked is False


def test_un_second_appareil_obtient_une_ligne_distincte(
    client_api: TestClient, db_session: Session, identifiants: dict
):
    premier = _connecter(client_api, identifiants)
    second = _connecter(
        client_api,
        {**identifiants, "device_info": "device-2"},
    )

    assert premier["refresh_token"] != second["refresh_token"]
    assert len(db_session.query(UserSession).all()) == 2


def test_logout_empeche_tout_nouveau_refresh(
    client_api: TestClient, identifiants: dict
):
    jetons = _connecter(client_api, identifiants)

    deconnexion = client_api.post(
        URL_LOGOUT, json={"refresh_token": jetons["refresh_token"]}
    )

    assert deconnexion.status_code == 204
    assert _rafraichir(client_api, jetons["refresh_token"]).status_code == 401
