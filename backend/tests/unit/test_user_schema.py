"""Tests unitaires de validation des schemas Pydantic utilisateur."""

from datetime import UTC, datetime
from uuid import UUID

import pytest
from pydantic import ValidationError

from schemas.user_schema import UserCreate, UserRead

pytestmark = pytest.mark.unit


class TestUserCreate:
    def test_accepte_un_payload_valide(self, payload_inscription: dict):
        utilisateur = UserCreate(**payload_inscription)

        assert utilisateur.first_name == "Ada"
        assert utilisateur.email == "ada@example.com"
        assert utilisateur.mot_de_passe == "MotDePasse1!"

    def test_localisation_est_optionnelle(self, payload_inscription: dict):
        del payload_inscription["localisation"]

        assert UserCreate(**payload_inscription).localisation is None

    def test_normalise_l_email_en_minuscules(
        self, payload_inscription: dict
    ):
        payload_inscription["email"] = "  ADA@Example.COM  "

        assert UserCreate(**payload_inscription).email == "ada@example.com"

    def test_supprime_les_espaces_autour_des_noms(
        self, payload_inscription: dict
    ):
        payload_inscription["prenom"] = "  Ada  "
        payload_inscription["nom"] = "  Lovelace "
        payload_inscription["pseudonyme"] = " ada "

        utilisateur = UserCreate(**payload_inscription)

        assert utilisateur.first_name == "Ada"
        assert utilisateur.last_name == "Lovelace"
        assert utilisateur.username == "ada"

    @pytest.mark.parametrize(
        "champ",
        ["prenom", "nom", "email", "pseudonyme", "mot_de_passe"],
    )
    def test_refuse_un_champ_obligatoire_absent(
        self, payload_inscription: dict, champ: str
    ):
        del payload_inscription[champ]

        with pytest.raises(ValidationError) as erreur:
            UserCreate(**payload_inscription)

        nom_canonique = {
            "prenom": "first_name",
            "nom": "last_name",
            "pseudonyme": "username",
        }.get(champ, champ)
        assert nom_canonique in str(erreur.value)

    @pytest.mark.parametrize(
        "email",
        [
            pytest.param("pas-un-email", id="sans-arobase"),
            pytest.param("ada@", id="sans-domaine"),
            pytest.param("@example.com", id="sans-partie-locale"),
            pytest.param("", id="vide"),
        ],
    )
    def test_refuse_un_email_invalide(
        self, payload_inscription: dict, email: str
    ):
        payload_inscription["email"] = email

        with pytest.raises(ValidationError):
            UserCreate(**payload_inscription)

    @pytest.mark.parametrize(
        ("mot_de_passe", "attendu"),
        [
            pytest.param("Court1!", "at least 12", id="trop-court"),
            pytest.param("motdepasse1!", "majuscule", id="sans-majuscule"),
            pytest.param("MOTDEPASSE1!", "minuscule", id="sans-minuscule"),
            pytest.param("MotDePasse!!", "chiffre", id="sans-chiffre"),
            pytest.param(
                "MotDePasse12", "spécial", id="sans-caractere-special"
            ),
        ],
    )
    def test_refuse_un_mot_de_passe_trop_faible(
        self, payload_inscription: dict, mot_de_passe: str, attendu: str
    ):
        payload_inscription["mot_de_passe"] = mot_de_passe

        with pytest.raises(ValidationError) as erreur:
            UserCreate(**payload_inscription)

        assert attendu in str(erreur.value)

    def test_refuse_un_mot_de_passe_trop_long(
        self, payload_inscription: dict
    ):
        payload_inscription["mot_de_passe"] = "A1!" + "a" * 126

        with pytest.raises(ValidationError):
            UserCreate(**payload_inscription)

    @pytest.mark.parametrize(
        ("champ", "longueur_max"),
        [("prenom", 100), ("nom", 100), ("pseudonyme", 50)],
    )
    def test_refuse_un_champ_trop_long(
        self, payload_inscription: dict, champ: str, longueur_max: int
    ):
        payload_inscription[champ] = "a" * (longueur_max + 1)

        with pytest.raises(ValidationError):
            UserCreate(**payload_inscription)


class TestUserRead:
    def test_se_construit_depuis_un_objet_orm(self):
        """`from_attributes` permet de renvoyer directement le modele."""

        class UtilisateurFactice:
            id = UUID("00000000-0000-0000-0000-000000000001")
            first_name = "Ada"
            last_name = "Lovelace"
            email = "ada@example.com"
            username = "ada"
            date_of_birth = None
            postal_code = None
            password_hash = "pbkdf2_sha256$200000$aa$bb"
            created_at = datetime(2026, 1, 1, tzinfo=UTC)

        lecture = UserRead.model_validate(UtilisateurFactice())

        assert lecture.id == UUID("00000000-0000-0000-0000-000000000001")
        assert lecture.email == "ada@example.com"

    def test_n_expose_jamais_le_mot_de_passe(self):
        """Garde-fou : aucun champ de hash ne doit fuiter par l'API."""
        champs = UserRead.model_fields

        assert "mot_de_passe" not in champs
        assert "password_hash" not in champs
