"""Tests unitaires de AuthService, sans base de donnees.

Le service instancie lui-meme son UserRepository ; on substitue donc le
nom `UserRepository` dans le module `services.auth_service` par un double
en memoire. Ce qui est teste ici est la logique metier (detection du
doublon, hachage, mapping des champs), pas le SQL.
"""

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest

from models.session_model import UserSession
from models.user_model import User
from schemas.auth_schema import LoginRequest
from schemas.user_schema import UserCreate
from services import auth_service as auth_service_module
from services.auth_service import (
    AuthService,
    EmailAlreadyUsedError,
    InvalidCredentialsError,
    InvalidRefreshTokenError,
    UsernameAlreadyUsedError,
)
from utils.security import (
    decode_access_token,
    hash_refresh_token,
    verify_password,
)

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


class FauxSessionRepository:
    """Double en memoire de SessionRepository (meme surface utilisee)."""

    def __init__(self, db=None):
        self.db = db
        self.sessions: list[UserSession] = []

    def get_by_refresh_token_hash(self, token_hash: str) -> UserSession | None:
        return next(
            (s for s in self.sessions if s.refresh_token_hash == token_hash),
            None,
        )

    def get_by_user_and_device(
        self, user_id: UUID, device_info: str
    ) -> UserSession | None:
        return next(
            (
                s
                for s in self.sessions
                if s.user_id == user_id and s.device_info == device_info
            ),
            None,
        )

    def revoke_all_for_user(self, user_id: UUID) -> None:
        for session_utilisateur in self.sessions:
            if session_utilisateur.user_id == user_id:
                session_utilisateur.revoked = True

    def create(self, obj: UserSession) -> UserSession:
        # Imite les valeurs par defaut que PostgreSQL poserait a l'insertion.
        obj.id = uuid4()
        obj.revoked = False
        self.sessions.append(obj)
        return obj

    def update(self, obj: UserSession) -> UserSession:
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
def depot_sessions(monkeypatch: pytest.MonkeyPatch) -> FauxSessionRepository:
    instance = FauxSessionRepository()
    monkeypatch.setattr(
        auth_service_module, "SessionRepository", lambda db: instance
    )
    return instance


@pytest.fixture
def service(
    depot: FauxUserRepository, depot_sessions: FauxSessionRepository
) -> AuthService:
    # La session est inutilisee : les faux depots ignorent leur argument.
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


def _connexion(
    email: str = "ada@example.com",
    mot_de_passe: str = "MotDePasse1!",
    device_info: str = "device-1",
) -> LoginRequest:
    return LoginRequest(
        email=email,
        mot_de_passe=mot_de_passe,
        device_info=device_info,
    )


def _dans_six_mois() -> datetime:
    return datetime.now(UTC) + timedelta(days=180)


@pytest.fixture
def inscrit(service: AuthService, user_create: UserCreate) -> User:
    return service.register(user_create)


def test_login_renvoie_une_paire_de_jetons(service: AuthService, inscrit: User):
    jetons = service.login(_connexion())

    assert decode_access_token(jetons.access_token) == inscrit.id
    assert jetons.refresh_token
    assert jetons.token_type == "bearer"
    assert jetons.expires_in == 15 * 60


def test_login_ne_persiste_que_l_empreinte_du_refresh_token(
    service: AuthService,
    depot_sessions: FauxSessionRepository,
    inscrit: User,
):
    jetons = service.login(_connexion())

    assert len(depot_sessions.sessions) == 1
    ouverte = depot_sessions.sessions[0]
    assert ouverte.user_id == inscrit.id
    assert ouverte.refresh_token_hash == hash_refresh_token(jetons.refresh_token)
    assert ouverte.refresh_token_hash != jetons.refresh_token


def test_login_ouvre_une_session_de_six_mois(
    service: AuthService,
    depot_sessions: FauxSessionRepository,
    inscrit: User,
):
    service.login(_connexion())

    ecart = depot_sessions.sessions[0].expires_at - _dans_six_mois()
    assert abs(ecart) < timedelta(minutes=1)


def test_login_stocke_l_information_de_l_appareil(
    service: AuthService,
    depot_sessions: FauxSessionRepository,
    inscrit: User,
):
    service.login(_connexion(device_info="android"))

    assert depot_sessions.sessions[0].device_info == "android"


def test_login_refuse_un_mauvais_mot_de_passe(
    service: AuthService,
    depot_sessions: FauxSessionRepository,
    inscrit: User,
):
    with pytest.raises(InvalidCredentialsError):
        service.login(_connexion(mot_de_passe="MauvaisMdp1!"))

    assert depot_sessions.sessions == []


def test_login_refuse_un_email_inconnu(
    service: AuthService,
    depot_sessions: FauxSessionRepository,
    inscrit: User,
):
    with pytest.raises(InvalidCredentialsError):
        service.login(_connexion(email="inconnu@example.com"))

    assert depot_sessions.sessions == []


def test_login_verifie_un_hash_meme_pour_un_email_inconnu(
    service: AuthService, monkeypatch: pytest.MonkeyPatch
):
    """Sans ce calcul, un e-mail inconnu repondrait plus vite qu'un vrai compte."""
    verifications = []

    def verify_password_espion(mot_de_passe: str, stocke: str) -> bool:
        verifications.append(stocke)
        return verify_password(mot_de_passe, stocke)

    monkeypatch.setattr(
        auth_service_module, "verify_password", verify_password_espion
    )

    with pytest.raises(InvalidCredentialsError):
        service.login(_connexion(email="inconnu@example.com"))

    assert len(verifications) == 1
    assert verifications[0].startswith("pbkdf2_sha256$")


def test_refresh_reutilise_la_meme_session_et_le_meme_token(
    service: AuthService,
    depot_sessions: FauxSessionRepository,
    inscrit: User,
):
    premiers = service.login(_connexion())

    seconds = service.refresh(premiers.refresh_token, "device-1")

    assert len(depot_sessions.sessions) == 1
    assert depot_sessions.sessions[0].revoked is False
    assert seconds.refresh_token == premiers.refresh_token
    assert depot_sessions.sessions[0].refresh_token_hash == hash_refresh_token(
        seconds.refresh_token
    )
    assert decode_access_token(seconds.access_token) == inscrit.id


def test_refresh_conserve_l_appareil_si_le_client_ne_le_repete_pas(
    service: AuthService,
    depot_sessions: FauxSessionRepository,
    inscrit: User,
):
    premiers = service.login(_connexion(device_info="ios"))

    service.refresh(premiers.refresh_token, "ios")

    assert len(depot_sessions.sessions) == 1
    assert depot_sessions.sessions[0].device_info == "ios"


def test_refresh_refuse_un_autre_appareil(
    service: AuthService,
    depot_sessions: FauxSessionRepository,
    inscrit: User,
):
    premiers = service.login(_connexion(device_info="android"))

    with pytest.raises(InvalidRefreshTokenError):
        service.refresh(premiers.refresh_token, "ios")

    assert len(depot_sessions.sessions) == 1
    assert depot_sessions.sessions[0].device_info == "android"


def test_refresh_repousse_l_expiration_a_six_mois(
    service: AuthService,
    depot_sessions: FauxSessionRepository,
    inscrit: User,
):
    """Chaque refresh valide repousse la limite de six mois."""
    jetons = service.login(_connexion())
    depot_sessions.sessions[0].expires_at = datetime.now(UTC) + timedelta(days=1)

    avant_refresh = datetime.now(UTC)
    service.refresh(jetons.refresh_token, "device-1")
    apres_refresh = datetime.now(UTC)

    expiration = depot_sessions.sessions[0].expires_at
    assert avant_refresh + timedelta(days=180) <= expiration
    assert expiration <= apres_refresh + timedelta(days=180)


def test_refresh_refuse_un_jeton_inconnu(service: AuthService):
    with pytest.raises(InvalidRefreshTokenError):
        service.refresh("jeton-inconnu", "device-1")


def test_refresh_refuse_un_jeton_expire(
    service: AuthService,
    depot_sessions: FauxSessionRepository,
    inscrit: User,
):
    jetons = service.login(_connexion())
    depot_sessions.sessions[0].expires_at = datetime.now(UTC) - timedelta(seconds=1)

    with pytest.raises(InvalidRefreshTokenError):
        service.refresh(jetons.refresh_token, "device-1")

    assert len(depot_sessions.sessions) == 1
    assert depot_sessions.sessions[0].revoked is True


def test_un_second_appareil_ouvre_une_session_distincte(
    service: AuthService,
    depot_sessions: FauxSessionRepository,
    inscrit: User,
):
    telephone = service.login(_connexion(device_info="device-1"))
    tablette = service.login(_connexion(device_info="device-2"))

    assert telephone.refresh_token != tablette.refresh_token
    assert len(depot_sessions.sessions) == 2
    assert {s.device_info for s in depot_sessions.sessions} == {
        "device-1",
        "device-2",
    }


def test_logout_revoque_la_session(
    service: AuthService,
    depot_sessions: FauxSessionRepository,
    inscrit: User,
):
    jetons = service.login(_connexion())

    service.logout(jetons.refresh_token)

    assert depot_sessions.sessions[0].revoked is True


def test_logout_est_idempotent(
    service: AuthService,
    depot_sessions: FauxSessionRepository,
    inscrit: User,
):
    jetons = service.login(_connexion())

    service.logout(jetons.refresh_token)
    service.logout(jetons.refresh_token)

    assert len(depot_sessions.sessions) == 1
    assert depot_sessions.sessions[0].revoked is True


def test_logout_ignore_un_jeton_inconnu(
    service: AuthService, depot_sessions: FauxSessionRepository
):
    service.logout("jeton-inconnu")

    assert depot_sessions.sessions == []


def test_un_jeton_deconnecte_ne_permet_plus_de_rafraichir(
    service: AuthService, inscrit: User
):
    jetons = service.login(_connexion())
    service.logout(jetons.refresh_token)

    with pytest.raises(InvalidRefreshTokenError):
        service.refresh(jetons.refresh_token, "device-1")
