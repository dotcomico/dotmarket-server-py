"""In-memory helpers for deriving the category tree and ancestry.

Every function here takes an *already loaded* collection of category rows and
derives the answer in memory, so a caller issues one query instead of one
query per node (the N+1 pattern these replace).

Rows only need `.id` and `.parentId`, so both full `Category` models and
lightweight `db.session.query(Category.id, Category.parentId)` tuples work.
Callers that need `to_dict()` (i.e. `build_forest`) must pass full models.

Deliberately free of Flask/SQLAlchemy imports: this is service-shaped logic
that moves into `services/category_service.py` unchanged at Step 9.
"""


def _group_children(rows):
    """Map parentId -> [row, ...]. Root rows live under the key `None`."""
    children = {}
    for row in rows:
        children.setdefault(row.parentId, []).append(row)
    return children


def build_forest(rows, max_depth=None):
    """Build the full category tree as nested `to_dict()` payloads.

    `max_depth=None` means unlimited depth; pass an int to stop expanding
    below that level (children of a capped node come back as `[]`).

    A cycle cannot hang this traversal: `parentId` is single-valued, so any
    cycle forms a component in which no row has `parentId IS NULL`, and the
    walk only ever starts from roots.
    """
    children = _group_children(rows)

    def build(node, depth):
        data = node.to_dict()
        if max_depth is not None and depth >= max_depth:
            data['children'] = []
        else:
            data['children'] = [build(child, depth + 1)
                                for child in children.get(node.id, [])]
        return data

    return [build(root, 0) for root in children.get(None, [])]


def collect_subtree_ids(rows, root_id):
    """Ids of `root_id` and every category beneath it, `root_id` first."""
    children = _group_children(rows)

    ids = []
    seen = set()
    stack = [root_id]
    while stack:
        current = stack.pop()
        # Descending from an arbitrary node *can* meet a cycle in corrupt
        # data, unlike build_forest above, so guard the walk.
        if current in seen:
            continue
        seen.add(current)
        ids.append(current)
        stack.extend(child.id for child in children.get(current, []))
    return ids


def ancestry_chain(rows, category_id):
    """Rows from the root down to `category_id`, i.e. breadcrumb order.

    Returns `[]` if `category_id` isn't present in `rows`. Stops on a repeat
    so a corrupt parent cycle can't loop forever.
    """
    by_id = {row.id: row for row in rows}

    chain = []
    seen = set()
    current = category_id
    while current is not None and current not in seen:
        seen.add(current)
        row = by_id.get(current)
        if row is None:
            break
        chain.insert(0, row)
        current = row.parentId
    return chain


def is_descendant(rows, ancestor_id, category_id):
    """True if `category_id` sits somewhere beneath `ancestor_id`.

    Walks up from `category_id` (depth steps) rather than down through
    `ancestor_id`'s whole subtree.
    """
    if ancestor_id == category_id:
        return False
    return any(row.id == ancestor_id
               for row in ancestry_chain(rows, category_id))
