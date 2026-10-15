# Community Digital Voting System — Complete Documentation

> Written from the final code. Every file, function, class and endpoint named here exists in the project.

## 0. Verification status (read first)

| Item | Status |
|---|---|
| Alembic migration `a1c3e5d7f901` (upgrade, downgrade, upgrade) on a copy of the original `voting.db` | **Run and verified** – all 5 existing votes preserved, `PRAGMA integrity_check` ok, `foreign_key_check` empty |
| Migration applied to the shipped `backend/voting.db` | **Done** (`alembic_version` = `a1c3e5d7f901`) |
| `seed_data.sql` run twice on a DB copy | **Verified idempotent** |
| Frontend ESLint (`npm run lint`) | **Clean** |
| Backend unit tests (`backend/tests`, 26 tests) | **Written, NOT executed in my environment** (no network / Windows-only binaries in the supplied `.venv`) – run `pytest` once after setup |
| Running API, Swagger, live UI in browser, responsive check | **Not executed by me** – follow Section 30–31 and the checklist in Section 34 |
| Python SDK (OpenAPI Generator CLI) | **Not generated** (needs network + Java). Run `generate_sdk.bat` with the backend running (Section 32) |

## 1. Project overview
A full-stack web app where registered users vote **YES / NO / ABSTAIN** on community proposals. Proposals have deadlines, expire automatically, can be force-closed by an admin, and votes can be changed/revoked only while the proposal is active. Identity comes from a JWT, so a user can only ever vote as themselves.

## 2. Objectives
Implement the PDF “Community Digital Voting System”: FastAPI + SQLite + Alembic backend, React + Axios frontend, tests, setup/run scripts, SDK generation, with strict server-side enforcement of: one vote per user per proposal, revoke/change only while active, automatic expiry, admin force-close.

## 3. Features
- Registration, login (JWT), `/auth/me`, logout; USER / ADMIN roles.
- Create, list (filter by status), view proposals with live counts.
- Vote, change vote, revoke vote; duplicate votes rejected (HTTP 409 + DB constraint).
- Automatic EXPIRED status; admin `PATCH /proposals/{id}/close`.
- Results with counts and percentages computed from SQLite.
- UI: login/register, user dashboard (stats, filters, search), proposal cards, detail page, admin dashboard (stats, proposals table, users table), countdown timers, 15 s polling, toasts, confirmation dialogs, skeleton loaders, empty/error states, dark-mode aware, responsive.

## 4. Technology stack
Python 3.12, FastAPI 0.143, Pydantic 2, SQLAlchemy 2, Alembic, SQLite, passlib+bcrypt, python-jose (JWT), pytest + FastAPI TestClient. React 19, Vite, Axios (no router library – small hash router in `router.js`).

## 5. Folder structure
```
community-digital-voting-system/
├─ setupdev.bat            # venv + pip + alembic + npm install
├─ runapplication.bat      # starts backend window + frontend
├─ generate_sdk.bat        # OpenAPI Generator CLI -> voting_sdk/
├─ DOCUMENTATION.md
├─ backend/
│  ├─ main.py              # `python main.py` -> uvicorn on :8000
│  ├─ create_admin.py      # create / promote an ADMIN
│  ├─ seed_data.sql        # optional sample data
│  ├─ requirements.txt
│  ├─ alembic.ini
│  ├─ voting.db            # SQLite database (your data, migrated)
│  ├─ .env.example
│  ├─ alembic/
│  │  ├─ env.py
│  │  └─ versions/
│  │     ├─ 852cf976f459_add_vote_uniqueness_constraint.py
│  │     ├─ 6f9740da17eb_add_users_table.py
│  │     └─ a1c3e5d7f901_link_votes_to_users_and_constraints.py
│  ├─ app/
│  │  ├─ config.py  database.py  models.py  schemas.py  security.py
│  │  ├─ auth_dependencies.py  services.py  init_db.py  main.py
│  │  └─ routers/ auth.py  proposals.py  votes.py  admin.py
│  └─ tests/ conftest.py  test_voting_system.py
└─ frontend/
   ├─ index.html  package.json  vite.config.js
   └─ src/
      ├─ main.jsx  App.jsx  api.js  router.js  index.css
      ├─ context/ AuthContext.jsx  UiContext.jsx
      ├─ components/ common.jsx  VotePanel.jsx  ProposalCard.jsx  CreateProposalModal.jsx  Navbar.jsx
      └─ pages/ AuthPages.jsx  Dashboard.jsx  ProposalDetail.jsx  AdminDashboard.jsx
```

## 6. System architecture
```
Browser (React SPA, :5173)
   │  Axios (JWT in Authorization header)
   ▼
FastAPI (:8000)  ── routers ─▶ dependencies (auth/db) ─▶ services.py (rules)
   │                                                        │
   ▼                                                        ▼
SQLAlchemy ORM  ───────────────────────────────▶  SQLite  backend/voting.db
                                                    ▲
                                          Alembic migrations
```
The frontend never touches the database; all rules are enforced in the backend.

## 7. Frontend architecture
- `main.jsx` wraps `<App/>` in `UiProvider` (toasts + `confirm()` dialog) and `AuthProvider` (user, token, login/register/logout).
- `App.jsx` – route guards (unauthenticated → `#/login`, non-admin on `#/admin` → dashboard + error toast) and page selection.
- `router.js` – `useRoute()`, `navigate()` over `location.hash` (`#/`, `#/login`, `#/register`, `#/proposal/:id`, `#/admin`).
- `api.js` – Axios instance (`baseURL` = `VITE_API_URL` or `http://127.0.0.1:8000`), request interceptor adds the token, response interceptor fires `auth:expired` on 401, `getErrorMessage()` maps 401/403/404/409/422/500/network to friendly text.
- `components/VotePanel.jsx` – submit / update / revoke vote; always re-syncs with the DB through `onChanged`.
- `components/common.jsx` – `StatusBadge`, `Countdown`, `ResultsBars`, `Spinner`, `SkeletonCards`, `EmptyState`, `ErrorState`, `formatDateTime`.

## 8. Backend architecture
Layers: **routers** (HTTP) → **dependencies** (`get_db`, `get_current_user`, `get_optional_user`, `get_current_admin`) → **services.py** (business rules) → **models.py** (ORM). `main.py` registers CORS, routers and a global 500 handler. `config.py` reads settings from environment/`.env`.

## 9. Database architecture
SQLite, 4 tables: `users`, `proposals`, `votes`, `alembic_version`.
```
users 1 ───< votes >─── 1 proposals
          (user_id FK)   (proposal_id FK, ON DELETE CASCADE)
UNIQUE uq_vote_proposal_user (proposal_id, user_id)
```
Foreign keys are enforced: `database.py` runs `PRAGMA foreign_keys=ON` on every connection.

## 10. Tables and important columns
**users** – `id` PK; `username` UNIQUE; `password` (bcrypt hash); `role` ('USER'/'ADMIN').
**proposals** – `id`; `title`; `description`; `created_at` (UTC); `deadline` (UTC); `status` with `CHECK ck_proposal_status` ∈ ACTIVE/CLOSED/EXPIRED.
**votes** – `id`; `proposal_id` FK→proposals (CASCADE); `user_id` INTEGER FK→users (CASCADE); `vote` with `CHECK ck_vote_value` ∈ YES/NO/ABSTAIN; `created_at`; `UNIQUE uq_vote_proposal_user`.
**alembic_version** – `version_num` (currently `a1c3e5d7f901`).

Mapping to the PDF schema: `voter_name` → `votes.user_id` (FK to the logged-in user; the API returns `voter_name` = username); `voted_at` → `created_at`; status/vote values are UPPERCASE (to keep your existing data and your requested ACTIVE/YES style).

## 11. Database file location
`backend/voting.db` (absolute path built in `app/config.py` from `BASE_DIR`; override with `DATABASE_URL`). Open it with `sqlite3 backend/voting.db` or DB Browser for SQLite.

## 12. How data is stored
Each request gets a SQLAlchemy `Session` from `get_db()`; routers add/modify ORM objects and `commit()`. All datetimes are stored as naive **UTC**; API responses serialise them with a trailing `Z` (`OutputDateTime` in `schemas.py`) so the browser converts to local time correctly. Passwords are stored only as bcrypt hashes.

## 13. Registration workflow
`RegisterPage` (`pages/AuthPages.jsx`) validates → `AuthContext.register()` → `POST /auth/register` → `routers/auth.py::register` checks case-insensitive duplicate username (409), hashes with `security.hash_password`, stores role **USER always** (the old code let clients choose ADMIN – fixed) → frontend logs in automatically.

## 14. Login workflow
`POST /auth/login` → `routers/auth.py::login` verifies with `security.verify_password` (401 on failure) → returns `{access_token, token_type, user}` → `AuthContext.login()` saves the token (`tokenStore`, localStorage key `cvs_token`) and the user.

## 15. JWT workflow
`security.create_access_token` signs `{user_id, role, exp}` with HS256 using `SECRET_KEY` (from env, or auto-generated once into `backend/.secret_key`). Expiry: `ACCESS_TOKEN_EXPIRE_MINUTES` (default 60). Every protected route depends on `get_current_user`, which decodes the token and reloads the user from the DB (role changes take effect immediately). Missing/invalid token → 401. Logout: `POST /auth/logout` validates the session, the client deletes the token (JWTs are stateless).

## 16. USER vs ADMIN authorization
| Action | Anonymous | USER | ADMIN |
|---|---|---|---|
| List/view proposals, results | ✔ | ✔ | ✔ |
| Create proposal | ✘ 401 | ✔ | ✔ |
| Vote / change / revoke own vote | ✘ 401 | ✔ | ✔ |
| Modify someone else's vote | – | ✘ 403 | ✘ 403 |
| `PATCH /proposals/{id}/close` | ✘ 401 | ✘ 403 | ✔ |
| `/admin/stats`, `/admin/users` | ✘ 401 | ✘ 403 | ✔ |
`get_current_admin` enforces admin routes. Setting `ALLOW_USER_PROPOSALS=false` restricts creation to admins (your original behaviour). Admins are created with `python create_admin.py <user> <password>`.

## 17. Proposal creation workflow
`CreateProposalModal` → `POST /proposals/` → `proposals.py::create_proposal`: validates (title/description 3+ chars), deadline defaults to **now + 2 days** (`schemas.default_deadline`), rejects past deadlines (422), saves status ACTIVE.

## 18. Voting workflow
`VotePanel` → `POST /proposals/{id}/vote` (`cast_vote`): load proposal with lazy expiry (`services.get_proposal_or_404`) → `services.ensure_votable` (CLOSED/EXPIRED → 409) → duplicate check → insert Vote with `user_id = current_user.id` (the body only carries `vote`). Change: `PUT /votes/{vote_id}`; revoke: `DELETE /votes/{vote_id}` (`routers/votes.py`), both owner-only and only while active. The UI then refetches the proposal so counts update.

## 19. Duplicate vote prevention
Two layers: (1) `cast_vote` checks for an existing vote → **409**; (2) database `UNIQUE uq_vote_proposal_user (proposal_id, user_id)` – a race that slips past (1) raises `IntegrityError`, caught and turned into 409. Tested by `test_duplicate_vote_rejected_409` and `test_db_unique_constraint_blocks_duplicates`. To change a vote the user uses PUT or revokes and votes again.

## 20. Results calculation workflow
`services.tally` runs `SELECT proposal_id, vote, COUNT(id) … GROUP BY` on `votes`; `build_proposal_responses` adds `yes/no/abstain/total` to every proposal; `build_results` adds percentages (`GET /proposals/{id}/results`). Nothing is hardcoded or cached. The UI renders bars in `ResultsBars`.

## 21. Frontend → Axios → FastAPI → SQLAlchemy → SQLite
```
click "Submit vote" → VotePanel.submit() → api.post('/proposals/3/vote')
→ interceptor adds Bearer token → FastAPI cast_vote()
→ get_current_user (JWT) → services rules → SQLAlchemy db.add(Vote)/commit
→ INSERT INTO votes … (SQLite) → 201 JSON → toast + onChanged() → GET /proposals/ → UI re-render
```

## 22. API endpoints
| Method & path | Auth | Purpose | Main errors |
|---|---|---|---|
| POST `/auth/register` | – | Register (role USER) | 409, 422 |
| POST `/auth/login` | – | Get JWT + user | 401, 422 |
| GET `/auth/me` | user | Current user | 401 |
| POST `/auth/logout` | user | Confirm logout | 401 |
| POST `/proposals/` | user | Create proposal | 401, 403*, 422 |
| GET `/proposals/?status=` | optional | List with counts (+`my_vote`) | 422 |
| GET `/proposals/{id}` | optional | One proposal + counts | 404 |
| GET `/proposals/{id}/results` | – | Counts + percentages | 404 |
| POST `/proposals/{id}/vote` | user | Cast vote | 401, 404, 409, 422 |
| PATCH `/proposals/{id}/close` | admin | Force close | 401, 403, 404, 409 |
| GET `/votes/me` | user | My votes | 401 |
| PUT `/votes/{vote_id}` | owner | Change vote | 403, 404, 409 |
| DELETE `/votes/{vote_id}` | owner | Revoke vote | 403, 404, 409 |
| GET `/admin/stats` | admin | Totals | 401, 403 |
| GET `/admin/users` | admin | Users + votes cast | 401, 403 |
\*only when `ALLOW_USER_PROPOSALS=false`. Swagger: `/docs`, schema: `/openapi.json`.
**Removed vs. old API:** `POST /proposals/{id}/votes/` (trusted a client-supplied `user_id`), `DELETE /proposals/{id}/votes/{user_id}`, `POST /proposals/{id}/close` – replaced by the PDF-specified routes above.

## 23. Alembic migration workflow
`alembic.ini` + `alembic/env.py` (uses `app.config.DATABASE_URL`, `render_as_batch=True` for SQLite). Chain: `852cf976f459` → `6f9740da17eb` → `a1c3e5d7f901`. The last one: adds the status CHECK, creates a placeholder user (no usable password) for every legacy free-text voter (`user101`, `user102`, `104`, `105`, `106`), rebuilds `votes` with integer `user_id` FK, CASCADE, `uq_vote_proposal_user`, vote CHECK, recreates indexes. Commands (inside `backend/`): `alembic upgrade head`, `alembic downgrade -1`, `alembic current`, `alembic revision --autogenerate -m "msg"`.

## 24. Error handling
Backend: `HTTPException` with proper codes (401/403/404/409/422), Pydantic validation → 422, global handler in `main.py` → 500 `{"detail":"Internal server error"}`. Frontend: `getErrorMessage()` in `api.js` converts each status to a readable message shown in toasts/alerts; 401 on an authenticated call logs the user out.

## 25. Security
bcrypt hashing; JWT with expiry; secret from env / generated file (not in source); server derives voter identity from the token; role never accepted from registration; admin checks in dependencies (frontend guards are only UX); CORS limited to `CORS_ORIGINS`; DB-level constraints (unique, CHECK, FK); password max 72 bytes (bcrypt limit). Known limitation: token stored in localStorage; no rate limiting; logout does not revoke tokens server-side.

## 26. USER journey
Register → auto sign-in → dashboard (stats: open, awaiting your vote, votes cast) → filter/search → pick Yes/No/Abstain → **Submit vote** → see counts update → change choice → **Update vote** or **Revoke vote** (confirmation) → after deadline/close the panel is locked → **Sign out** (confirmation).

## 27. ADMIN journey
Sign in with an ADMIN account → **Admin** menu → stats, proposals table (counts per option), **Close** with confirmation (also on the detail page), users table with votes cast. Admins can also vote and create proposals.

## 28. Where business logic lives
| Rule | Location |
|---|---|
| One vote per user/proposal | `routers/proposals.py::cast_vote` + `models.Vote` constraint |
| Active-only vote/change/revoke | `services.ensure_votable`, used by `cast_vote`, `change_vote`, `revoke_vote` |
| Auto-expiry | `services.expire_overdue` (list/stats), `services.get_proposal_or_404` (single) |
| Default 2-day deadline | `schemas.default_deadline`, `create_proposal` |
| Admin force-close | `proposals.py::close_proposal` + `get_current_admin` |
| Owner-only revoke/change | `votes.py::_own_vote_or_error` |
| Counts/percentages | `services.tally`, `build_results` |

## 29. Important files and responsibilities
`app/config.py` settings/secret · `app/database.py` engine, `get_db`, FK pragma · `app/models.py` `User`, `Proposal`, `Vote`, `utcnow` · `app/schemas.py` request/response models, UTC serialisation · `app/security.py` `hash_password`, `verify_password`, `create_access_token` · `app/auth_dependencies.py` `get_current_user`, `get_optional_user`, `get_current_admin` · `app/services.py` rules and aggregation · `app/routers/*` endpoints · `tests/conftest.py` in-memory DB fixtures (`client`, `user1`, `user2`, `admin`, `proposal`) · frontend files listed in Section 7.

## 30. Start the backend
```
cd backend
env\Scripts\activate
python main.py          # http://127.0.0.1:8000   Swagger: /docs
```
## 31. Start the frontend
```
cd frontend
npm start               # http://localhost:5173
```
Or run `runapplication.bat` from the project root (opens the backend in its own window, then the frontend).

## 32. Dependencies and setup
Requires Python 3.10+ (project uses 3.12), Node 18+. `setupdev.bat` does: create `backend\env`, `pip install -r requirements.txt`, `alembic upgrade head`, `npm install`. Backend packages: see `backend/requirements.txt`. **SDK:** with the backend running and Java installed, run `generate_sdk.bat` (`openapi-generator-cli generate -i http://localhost:8000/openapi.json -g python -o voting_sdk`).

## 33. Environment variables (`backend/.env`, optional)
`SECRET_KEY`, `ACCESS_TOKEN_EXPIRE_MINUTES` (60), `DATABASE_URL`, `CORS_ORIGINS` (`http://localhost:5173,http://127.0.0.1:5173`), `ALLOW_USER_PROPOSALS` (true). Frontend: `VITE_API_URL` (default `http://127.0.0.1:8000`).

## 34. Testing checklist
Automated: `cd backend && pytest -v` (26 tests: registration, login, hashing, 401/403, admin-only, create/past deadline, voting all choices, duplicate 409, DB unique constraint, revoke/change, other user's vote 403, closed, expired, auto-expiry, counts/percentages, cascade).
Manual UI:
- [ ] Register → lands on dashboard; duplicate username shows error
- [ ] Wrong password shows error; correct login works
- [ ] Create proposal (default deadline) appears as ACTIVE with countdown
- [ ] Vote Yes → counts update; vote again impossible (use Update/Revoke)
- [ ] Revoke asks confirmation and removes vote
- [ ] Admin closes proposal → badge CLOSED, voting locked
- [ ] Proposal past deadline shows EXPIRED, voting locked
- [ ] USER visiting `#/admin` is redirected with an error
- [ ] Sign out; protected pages redirect to login
- [ ] Resize to phone width: hamburger menu, single-column cards

## 35. Viva questions
1. **How is one vote per user enforced?** Server check in `cast_vote` plus DB `UNIQUE (proposal_id, user_id)`; races become 409.
2. **Why is `user_id` not sent by the client?** It would allow impersonation; the voter is taken from the JWT.
3. **How does expiry work?** Deadline compared to UTC now; `expire_overdue`/`get_proposal_or_404` flip ACTIVE→EXPIRED on access; `ensure_votable` also checks the deadline directly.
4. **Why 409 for closed/duplicate?** The request is valid but conflicts with current state.
5. **How are passwords stored?** bcrypt via passlib.
6. **What is in the JWT?** `user_id`, `role`, `exp`; signed HS256.
7. **Why Alembic?** Versioned, reversible schema changes; here it converted free-text voters to real user FKs without losing data.
8. **Why `PRAGMA foreign_keys=ON`?** SQLite ignores FKs/CASCADE otherwise.
9. **How is USER blocked from admin routes?** `get_current_admin` → 403, independent of the UI.
10. **Why dependency injection?** `get_db`/auth dependencies are overridden in tests (`conftest.py`) for an in-memory DB.
11. **How are results computed?** SQL `GROUP BY` counts at request time.
12. **Why UTC + `Z`?** Avoids local-time misinterpretation of deadlines.
13. **How does the UI stay current?** Re-fetch after every action, 10–15 s polling, countdown triggers refresh at expiry.

## 36. End-to-end workflow
```
Register/Login → JWT stored → Dashboard GET /proposals/ (with my_vote)
   → Vote POST /proposals/{id}/vote → UNIQUE + rules → DB
   → Change PUT /votes/{id}  | Revoke DELETE /votes/{id}   (active only)
   → Deadline passes → status EXPIRED automatically  | Admin PATCH close → CLOSED
   → Results GET /proposals/{id}/results (counts + %)
   → Logout → token discarded
```
## Notes on the existing data
Your admin account `admin123` and users `testuser`, `testuser1` are untouched (original passwords still work). Legacy voters from the old free-text field were converted to login-less placeholder users so existing results are unchanged. Proposal 5 (“food vote”) has a deadline that may already have passed and will show as EXPIRED.
