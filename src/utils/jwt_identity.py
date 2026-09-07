"""Shared parsing for the JWT identity, which is stored as a JSON-serialized
dict (see `user_identity_loader` in src/main.py) rather than a plain user id.

This logic used to be copy-pasted in three places (src/main.py,
src/middleware/auth.py, src/controllers/auth_controller.py::getMe) — see
ARCHITECTURE_IMPROVEMENTS.md Step 4.
"""
import json


def parse_identity(identity):
    """Parse a JWT identity that may be a JSON-encoded dict, or return it
    unchanged if it's already a dict or isn't valid JSON (e.g. a plain id).
    """
    if isinstance(identity, str):
        try:
            return json.loads(identity)
        except (json.JSONDecodeError, TypeError):
            return identity
    return identity


def resolve_user_id(identity):
    """Extract the user id from a raw JWT identity (JSON string, dict, or
    plain id), as returned by `flask_jwt_extended.get_jwt_identity()`.
    """
    parsed = parse_identity(identity)
    if isinstance(parsed, dict):
        return parsed.get('id')
    return parsed
