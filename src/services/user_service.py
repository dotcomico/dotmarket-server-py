from sqlalchemy import case, func

from src.config.constants import REVENUE_STATUSES, ROLES
from src.config.database import db
from src.models.Order import Order
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
    """Every user (password excluded) plus their order aggregates.

    Local (users-specific). Each dict is `User.to_dict(exclude_password=True)`
    extended with two columns the admin user list needs:

    - `ordersCount` — how many orders the user *placed*, **including
      cancelled** ones. Cancelling an order doesn't un-place it, so it still
      counts here.
    - `totalSpent` — realized revenue only: the sum of `totalAmount` over the
      user's `REVENUE_STATUSES` orders (paid/shipped). Pending and cancelled
      are excluded on purpose, because this is the same status set the admin
      dashboard's "Total Revenue" tile sums over — so per-user spend and total
      revenue can never disagree.

    One query: a LEFT OUTER JOIN + GROUP BY, so a user with no orders still
    appears (`ordersCount: 0`, `totalSpent: 0.0`) and there is no per-user
    query in a loop. `totalSpent` uses conditional aggregation and is coalesced
    so it is `0.0` rather than `None` for a user with no revenue orders.
    """
    rows = (
        db.session.query(
            User,
            func.count(Order.id).label('ordersCount'),
            func.coalesce(
                func.sum(
                    case((Order.status.in_(REVENUE_STATUSES), Order.totalAmount),
                         else_=0.0)
                ),
                0.0,
            ).label('totalSpent'),
        )
        .outerjoin(Order, Order.UserId == User.id)
        .group_by(User.id)
        .order_by(User.id)
        .all()
    )

    users = []
    for user, orders_count, total_spent in rows:
        data = user.to_dict(exclude_password=True)
        data['ordersCount'] = int(orders_count or 0)
        data['totalSpent'] = round(float(total_spent or 0.0), 2)
        users.append(data)

    return users


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
