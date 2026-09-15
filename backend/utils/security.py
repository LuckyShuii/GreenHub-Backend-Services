import hashlib
import hmac
import secrets

# PBKDF2-HMAC (stdlib) : hachage salé du mot de passe, sans dependance externe.
_ALGORITHME = "sha256"
_ITERATIONS = 200_000
_SEL_OCTETS = 16


def hash_password(mot_de_passe: str) -> str:
    sel = secrets.token_bytes(_SEL_OCTETS)
    derive = hashlib.pbkdf2_hmac(
        _ALGORITHME, mot_de_passe.encode("utf-8"), sel, _ITERATIONS
    )
    return f"pbkdf2_{_ALGORITHME}${_ITERATIONS}${sel.hex()}${derive.hex()}"


def verify_password(mot_de_passe: str, stocke: str) -> bool:
    try:
        algo_tag, iterations_brut, sel_hex, hash_hex = stocke.split("$")
        algorithme = algo_tag.split("_", 1)[1]
        iterations = int(iterations_brut)
        sel = bytes.fromhex(sel_hex)
        attendu = bytes.fromhex(hash_hex)
    except (ValueError, IndexError):
        return False

    derive = hashlib.pbkdf2_hmac(
        algorithme, mot_de_passe.encode("utf-8"), sel, iterations
    )
    return hmac.compare_digest(derive, attendu)
