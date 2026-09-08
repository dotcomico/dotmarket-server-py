# Backend Architecture Improvements — Roadmap

This document tracks the architecture review findings for `backend-py` and lays out
the fixes in **execution order: smallest/safest first, biggest/riskiest last.**
Each step is meant to be done, tested, and committed on its own before moving to
the next one — don't batch multiple steps into one commit.

Check off items as they're done (`[x]`) so this file also works as a running log.

---

## Step 1 — Cap pagination `limit`
**Size: trivial (~5 min) | Risk: none**

`getAllProducts` and `getProductsByCategory` accept an unbounded `limit` query
param — a client can request an arbitrarily large page.

- [x] In `controllers/product_controller.py` (`getAllProducts`) and
      `controllers/category_controller.py` (`getProductsByCategory`), clamp:
      `limit = min(int(request.args.get('limit', 10)), 100)`

**Commit:** `fix: clamp pagination limit to a sane maximum`

---

## Step 2 — Fix the SQLite path ambiguity
**Size: trivial (~10 min) | Risk: low (verify which file is actually live first)**

`config/database.py` resolves `DB_STORAGE` relative to the current working
directory (`./database.sqlite`), but a second file exists at
`src/instance/database.sqlite`. Depending on how the app is launched, it's
not obvious which one is used.

- [x] Confirm which file the running app currently writes to. — `src/instance/database.sqlite`
      is the real data (3 users, 60 categories, 84 products, 5 orders, 12 order items);
      `.env`'s `DB_STORAGE` was wrongly pointing at `./database.sqlite` (empty). Fixed by
      correcting `DB_STORAGE=./src/instance/database.sqlite` in the local `.env` — this was
      the entire bug (see the "two DB/env setup" note below).
- [x] ~~Resolve the path with `Path(__file__)`-relative logic instead of CWD-relative~~ —
      considered and reverted. The app is always launched from the repo root
      (`python -m src.main`), so CWD-relative resolution already behaves deterministically
      in practice; the `Path(__file__)` version was extra complexity solving a problem that
      wasn't actually being hit. Not applied.
- [x] Delete/ignore the stale `.sqlite` file once confirmed unused. — N/A: there is no stale
      file. `.env.example` intentionally points `DB_STORAGE` at `./database.sqlite`, a
      **blank starting DB for new installs** (populated via `seed_database.py`), while `.env`
      (gitignored, real local config) points at `src/instance/database.sqlite`, the real data.
      Both are needed; do not unify or delete either.

**Commit:** `fix: resolve SQLite database path deterministically`

---

## Step 3 — Delete the dead `asyncHandler`
**Size: trivial (~5 min) | Risk: none (it's unused)**

`middleware/errorHandler.py` defines `asyncHandler`, a leftover Express idiom
that is never imported anywhere in the codebase (confirmed via grep).

- [x] Delete `middleware/errorHandler.py`, **or** keep the file and repurpose it
      in Step 5 below (pick one — don't do both). — Deleted (confirmed via grep
      it was never imported anywhere). Step 5 will write a fresh log-and-reraise
      decorator rather than reusing this one.

**Commit:** `chore: remove unused asyncHandler leftover from Express port`

---

## Step 4 — Deduplicate JWT identity parsing
**Size: small (~30 min) | Risk: low**

The same "unwrap the JWT identity (string→JSON→dict, or plain id)" logic is
copy-pasted in three places:
- `main.py` (`user_lookup_callback`)
- `middleware/auth.py` (`auth()`)
- `controllers/auth_controller.py` (`getMe()`)

- [x] Add one helper, e.g. `utils/jwt_identity.py::resolve_user_id(identity)`. —
      Added `parse_identity()` (JSON-string → dict, else unchanged) and
      `resolve_user_id()` (parse then pull `.get('id')` if a dict) in
      `src/utils/jwt_identity.py`.
- [x] Replace all three call sites with it. — `main.py::user_lookup_callback`
      now calls `parse_identity`; `middleware/auth.py::auth` and
      `auth_controller.py::getMe` now call `resolve_user_id`.
- [x] Manually re-test login → `/api/auth/me` → any protected route, to confirm
      identity resolution still works identically. — Couldn't boot the live
      server in this sandbox (pre-existing sqlite3 "unable to open database
      file" error, reproduced identically on unmodified `master`, unrelated
      to this change). Verified equivalence instead by exercising the new
      helper against every identity shape the old duplicated code branched
      on (JSON-encoded dict, plain dict, non-JSON string, plain int,
      malformed JSON) — all five matched the old logic. **Recommend the user
      manually re-test login → `/api/auth/me` on their machine before
      merging**, since that's the one check this environment couldn't run.

**Commit:** `refactor: extract shared JWT identity parsing helper`

---

## Step 5 — Add a shared error-logging decorator, remove per-function try/except
**Size: medium (~1-2 hrs) | Risk: low (behavior-preserving)**

Nearly every controller function repeats:
```python
except Exception as error:
    logger.error('Operation failed', {'error': str(error)})
    print(f'... error: {error}')
    return jsonify({'message': 'Server error', 'error': str(error)}), 500
```
`main.py` already has a global `@app.errorhandler(Exception)` — this
boilerplate exists mainly to add the `logger.error` call.

- [x] Add one decorator (this is where `asyncHandler` from Step 3 gets reborn,
      if you chose to keep the file) that logs the exception and re-raises,
      letting the global handler build the response. — `src/utils/error_handler.py::handle_errors`
      (written fresh, not a revival of the deleted `asyncHandler`).
- [x] Apply it to every controller function, removing the local `try/except`. —
      Applied to all 26 controller functions. The only `except Exception` blocks
      left in the controllers are three narrow guards around
      `delete_uploaded_file` in `category_controller.py`, which are deliberate
      (a failed image cleanup must not fail the request) — not leftovers.
- [x] Confirm error responses (shape/status code) are unchanged by hitting a
      few endpoints with bad input. — Follow-up fix in `507eb5b` corrected two
      cases that were returning 500 instead of 400.

**Commit:** `refactor: replace per-function try/except with shared error-logging decorator`

---

## Step 6 — Add a shared validation helper module
**Size: medium (~1-2 hrs) | Risk: low**

`auth_controller.py` and `product_controller.py` each hand-roll their own
`validate*()` functions (duplicating the email regex, required-string checks,
etc.); `category_controller.py` and `order_controller.py` validate inline
with scattered `if not X: return jsonify(...), 400`.

- [x] Create `utils/validators.py` with small composable helpers:
      `required_string(value, field, min_len=None, max_len=None)`,
      `positive_number(value, field)`, `one_of(value, field, allowed)`, etc.
      Each returns an error dict or `None`. — Added `required_string`,
      `max_length`, `valid_email`, `strong_password`, `positive_number`,
      `one_of`, `required_list` in `src/utils/validators.py`.
- [x] Migrate `auth_controller.validateRegister/validateLogin` and
      `product_controller.validateProduct` to use them.
- [x] Migrate the inline checks in `category_controller.py` /
      `order_controller.py` to use them too. — Category's required-name
      checks and order's items/status checks now call the shared helpers,
      unpacking `error['msg']` to keep their original
      `{'message': ...}` response shape (only auth/product used the
      `{'type','msg','path'}` field-errors list shape). Verified every
      error-message branch matches the old duplicated code exactly via a
      standalone script exercising all helpers; all controllers still
      import cleanly.

**Commit:** `refactor: introduce shared validation helpers, remove duplicated checks`

---

## Step 7 — Cap pagination is done, now cap recursive category queries
**Size: medium (~1 hr) | Risk: low (only matters if the tree grows)**

`category_controller.py`'s `is_descendant`, `getAllChildIds`, and
`build_tree` each issue one DB query per node, recursively (N+1 pattern).
Not urgent at current data volume, but worth doing while touching this file
in Step 6/8 anyway.

- [x] Replace the per-node recursive queries with a single query that loads
      all categories once and builds the tree/ancestry in memory. — Added
      `src/utils/category_tree.py` (pure, no Flask/SQLAlchemy imports, so it
      moves into `services/category_service.py` unchanged at Step 9) with
      `build_forest`, `collect_subtree_ids`, `ancestry_chain`, `is_descendant`.
- [x] Migrated **four** call sites, not the three listed above — the breadcrumb
      loop in `getCategoryBySlug` is the same N+1 walking *up* the tree, and is
      the "ancestry" half of this step's commit message:
      - `getCategoryTree` — **61 queries → 1**
      - `getProductsByCategory` (`getAllChildIds`) — 11 → 7
      - `getCategoryBySlug` (breadcrumbs + `parent`) — 4 → 3 for a child;
        a root skips the ancestry query entirely and stays at 2
      - `updateCategory` (`is_descendant`) — now walks *up* from the proposed
        parent (depth steps) instead of descending the whole subtree
- [x] **Depth cap removed.** The old `depth < 2` in `build_tree` rendered only
      3 levels, so a 4th level would have silently vanished from
      `/api/categories/tree`. `build_forest` is unlimited by default;
      `build_forest(rows, max_depth=2)` reproduces the old output byte-for-byte
      if a cap is ever wanted again.
- [x] Cycle safety: `collect_subtree_ids` and `ancestry_chain` guard against a
      corrupt `parentId` cycle (the old unbounded versions would have hung).
      `build_forest` needs no guard — `parentId` is single-valued, so a cycle
      forms a component with no root, and the walk only starts from roots.

**Verified:** old vs. new servers run side by side on two ports returned
byte-identical JSON for `/tree`, root slug, child slug, and `/<slug>/products`;
all 60 category pages return 200 with breadcrumbs; helper output matches the old
logic for all 60 categories and all 3,600 `is_descendant` pairs. Write path
re-tested: self-parent / cycle / missing-parent all still 400, legitimate
re-parent and detach still 200. A temporary 5-level chain confirmed the tree now
renders all 5 levels (old code showed 3) and that a 4-level-deep cycle is still
rejected. Test data removed and the DB restored from a backup afterwards.

**Commit:** `perf: build category tree/ancestry from a single query instead of N+1`

---

## Step 8 — Collapse the routes-as-pure-passthrough layer
**Size: medium (~1-2 hrs) | Risk: low (mechanical, one resource at a time)**

Every function in `routes/*.py` currently just forwards to a controller
function with identical arguments — it's a layer that adds no behavior.

- [ ] Do this one resource at a time (`products` first, as a template).
- [ ] Either (a) register controller functions directly as blueprint view
      functions, or (b) move the controller logic straight into the route file.
      Prefer (b), since Step 9 will pull the actual logic out into services
      anyway — so this step is really "delete the redundant middle file" per resource.
- [ ] Re-test each resource's endpoints after collapsing it, before moving to
      the next resource.

**Commit (per resource):** `refactor: collapse products route/controller passthrough`
(repeat for categories, orders, users, auth)

---

## Step 9 — Extract a services layer (the big one)
**Size: large (~half day to a day) | Risk: medium — do this last, one resource at a time**

This is the highest-impact, highest-effort change: controllers currently mix
request-parsing, validation, DB queries, business rules, and response
shaping in one function, which makes them impossible to unit-test without a
running Flask app.

- [ ] Create `services/` with one file per resource:
      `product_service.py`, `category_service.py`, `order_service.py`,
      `user_service.py` (auth logic can fold into `user_service.py` or stay
      separate as `auth_service.py`).
- [ ] Move DB queries + business rules out of each route file into the
      matching service function. Services take plain arguments and return
      plain dicts/model instances — **no `flask.request` / `jsonify` inside
      services.**
- [ ] The route function becomes: parse `request` → call service → shape
      response with `jsonify(...)`.
- [ ] Do this **one resource at a time**, fully re-testing each resource
      (register/login, products CRUD, categories CRUD + tree, orders
      checkout flow) before starting the next, since this is the step most
      likely to introduce a subtle behavior change.
- [ ] Order of resources (simplest data flow first):
      1. `users` (smallest, 3 endpoints)
      2. `auth` (register/login/me — self-contained)
      3. `products` (CRUD + filters, no cross-resource logic)
      4. `categories` (recursive tree logic — benefits from Step 7 being done first)
      5. `orders` (most business-critical — stock decrement + transaction — do last, with the most care)

**Commit (per resource):** `refactor: extract product_service from product routes`
(repeat for auth, categories, orders — orders last)

---

## Step 10 — Add real automated tests against the new services
**Size: large (ongoing) | Risk: none — this is what makes Step 9 safe going forward**

Once services exist and don't depend on a running Flask app, they can be
unit-tested directly. `test_server_creations.py` (the existing manual
`requests`-based script) stays useful as a smoke test, but isn't a
substitute for this.

- [ ] Add `pytest` to `requirements.txt`.
- [ ] Add `tests/` with one test file per service, covering the validation
      and business-rule branches (invalid stock, duplicate email, category
      cycle prevention, etc.).
- [ ] Wire this into whatever CI (if any) runs before merges.

**Commit:** `test: add pytest suite covering the new service layer`

---

## Why this order

- Steps 1-3 are pure deletions/one-line fixes with zero behavioral ambiguity —
  good warm-up, immediate value, no risk of breaking anything.
- Steps 4-7 are refactors that remove duplication **without moving where
  logic lives** — still low-risk, and they shrink the files that Steps 8-9
  will need to touch anyway, making those safer.
- Step 8 removes a structural layer but keeps logic in place — mechanical,
  low-risk, one resource at a time.
- Step 9 is the only step that actually relocates business logic — done last,
  and only after 1-8 have already shrunk/cleaned the code it's moving, and
  done one resource at a time so a mistake in `orders` (the riskiest one)
  doesn't block or contaminate the others.
- Step 10 is what makes all future changes to the service layer safe, so it
  closes out the roadmap rather than starting it — there's nothing meaningful
  to unit-test until Step 9 exists.
