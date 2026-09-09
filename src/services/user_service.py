from src.config.constants import ROLES
from src.config.database import db
from src.models.User import User


def get_profile(user_id):
    """Return the given user's dict (password excluded).

    Local (users-specific) — mirrors the old inline behavior: if `user_id`
    doesn't exist, `.to_dict()` raises AttributeError, same as the original
    route code. `g.user['id']` always comes from an already-validated JWT
    (see `auth` middleware), so this shouldn't happen in practice.
    """
    user = User.query.filter_by(id=user_id).first()
    return user.to_dict(exclude_password=True)


def get_all_users():
    """Return every user as a dict (password excluded). Local (users-specific)."""
    users = User.query.all()
    return [u.to_dict(exclude_password=True) for u in users]


def update_user_role(user_id, role):
    """Update a user's role.

    Local (users-specific). Returns (result, error): `error` is
    {'status': int, 'message': str} on failure (None on success), so the
    route can turn it into the right HTTP status without this function
    touching flask.request/jsonify directly.
    """
    if role not in ROLES.values():
        return None, {'status': 400, 'message': 'Invalid role'}

    user = User.query.filter_by(id=user_id).first()
    if not user:
        return None, {'status': 404, 'message': 'User not found'}

    user.role = role
    db.session.commit()

    return {'message': 'User role updated successfully'}, None
