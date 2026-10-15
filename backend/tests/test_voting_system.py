from datetime import datetime, timedelta, timezone

from app.models import Proposal, Vote


def vote(client, pid, choice, headers):
    return client.post(f"/proposals/{pid}/vote", json={"vote": choice}, headers=headers)


# ---------- auth ----------
def test_register_login_me_logout(client):
    r = client.post("/auth/register", json={"username": "alice", "password": "Secret123"})
    assert r.status_code == 201 and r.json()["role"] == "USER"
    r = client.post("/auth/login", json={"username": "alice", "password": "Secret123"})
    assert r.status_code == 200
    h = {"Authorization": f"Bearer {r.json()['access_token']}"}
    assert client.get("/auth/me", headers=h).json()["username"] == "alice"
    assert client.post("/auth/logout", headers=h).status_code == 200


def test_register_cannot_choose_admin_role(client):
    r = client.post(
        "/auth/register", json={"username": "mallory", "password": "Secret123", "role": "ADMIN"}
    )
    assert r.status_code == 201 and r.json()["role"] == "USER"


def test_duplicate_username_409_and_validation_422(client):
    body = {"username": "bob", "password": "Secret123"}
    assert client.post("/auth/register", json=body).status_code == 201
    assert client.post("/auth/register", json=body).status_code == 409
    assert client.post("/auth/register", json={"username": "x", "password": "short"}).status_code == 422


def test_wrong_password_401_and_password_is_hashed(client, db_session):
    client.post("/auth/register", json={"username": "carol", "password": "Secret123"})
    assert client.post("/auth/login", json={"username": "carol", "password": "nope"}).status_code == 401
    from app.models import User

    stored = db_session.query(User).filter_by(username="carol").one().password
    assert stored != "Secret123" and stored.startswith("$2")


def test_protected_routes_require_token(client, proposal):
    assert client.get("/auth/me").status_code == 401
    assert client.post(f"/proposals/{proposal['id']}/vote", json={"vote": "YES"}).status_code == 401
    assert client.get("/auth/me", headers={"Authorization": "Bearer garbage"}).status_code == 401


# ---------- proposals / authorization ----------
def test_create_proposal_defaults_deadline_two_days(client, proposal):
    created = datetime.fromisoformat(proposal["created_at"].rstrip("Z"))
    deadline = datetime.fromisoformat(proposal["deadline"].rstrip("Z"))
    assert abs((deadline - created) - timedelta(days=2)) < timedelta(seconds=5)
    assert proposal["status"] == "ACTIVE"


def test_create_proposal_past_deadline_rejected(client, user1):
    past = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    r = client.post(
        "/proposals/",
        json={"title": "Old", "description": "Past deadline", "deadline": past},
        headers=user1,
    )
    assert r.status_code == 422


def test_user_cannot_close_admin_can(client, proposal, user1, admin):
    pid = proposal["id"]
    assert client.patch(f"/proposals/{pid}/close", headers=user1).status_code == 403
    assert client.patch(f"/proposals/{pid}/close").status_code == 401
    r = client.patch(f"/proposals/{pid}/close", headers=admin)
    assert r.status_code == 200 and r.json()["status"] == "CLOSED"
    assert client.patch(f"/proposals/{pid}/close", headers=admin).status_code == 409


def test_user_cannot_access_admin_endpoints(client, user1, admin):
    assert client.get("/admin/stats", headers=user1).status_code == 403
    assert client.get("/admin/users", headers=user1).status_code == 403
    assert client.get("/admin/stats", headers=admin).status_code == 200


def test_get_unknown_proposal_404(client):
    assert client.get("/proposals/9999").status_code == 404


def test_list_and_get_proposal_counts(client, proposal, user1, user2):
    pid = proposal["id"]
    vote(client, pid, "YES", user1)
    vote(client, pid, "NO", user2)
    one = client.get(f"/proposals/{pid}").json()
    assert (one["yes"], one["no"], one["abstain"], one["total"]) == (1, 1, 0, 2)
    assert len(client.get("/proposals/").json()) == 1
    assert client.get("/proposals/?status=CLOSED").json() == []


# ---------- voting rules ----------
def test_vote_all_choices(client, proposal, make_user):
    for i, choice in enumerate(["YES", "NO", "ABSTAIN"]):
        h = make_user(f"voter{i}")
        r = vote(client, proposal["id"], choice, h)
        assert r.status_code == 201 and r.json()["vote"] == choice
        assert r.json()["voter_name"] == f"voter{i}"
    res = client.get(f"/proposals/{proposal['id']}/results").json()
    assert (res["yes"], res["no"], res["abstain"], res["total"]) == (1, 1, 1, 3)
    assert res["yes_percent"] == 33.3


def test_invalid_vote_value_422(client, proposal, user1):
    assert vote(client, proposal["id"], "MAYBE", user1).status_code == 422


def test_duplicate_vote_rejected_409(client, proposal, user1):
    assert vote(client, proposal["id"], "YES", user1).status_code == 201
    r = vote(client, proposal["id"], "NO", user1)
    assert r.status_code == 409
    assert client.get(f"/proposals/{proposal['id']}/results").json()["total"] == 1


def test_db_unique_constraint_blocks_duplicates(db_session, client, proposal, user1):
    import pytest
    from sqlalchemy.exc import IntegrityError

    vote(client, proposal["id"], "YES", user1)
    existing = db_session.query(Vote).one()
    db_session.add(Vote(proposal_id=existing.proposal_id, user_id=existing.user_id, vote="NO"))
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_revoke_then_vote_again(client, proposal, user1):
    v = vote(client, proposal["id"], "YES", user1).json()
    assert client.delete(f"/votes/{v['id']}", headers=user1).status_code == 200
    assert client.get(f"/proposals/{proposal['id']}/results").json()["total"] == 0
    assert vote(client, proposal["id"], "NO", user1).status_code == 201


def test_change_vote_while_active(client, proposal, user1):
    v = vote(client, proposal["id"], "YES", user1).json()
    r = client.put(f"/votes/{v['id']}", json={"vote": "NO"}, headers=user1)
    assert r.status_code == 200 and r.json()["vote"] == "NO"
    res = client.get(f"/proposals/{proposal['id']}/results").json()
    assert (res["yes"], res["no"]) == (0, 1)


def test_cannot_revoke_or_change_someone_elses_vote(client, proposal, user1, user2):
    v = vote(client, proposal["id"], "YES", user1).json()
    assert client.delete(f"/votes/{v['id']}", headers=user2).status_code == 403
    assert client.put(f"/votes/{v['id']}", json={"vote": "NO"}, headers=user2).status_code == 403
    assert client.delete("/votes/9999", headers=user2).status_code == 404


def test_closed_proposal_rejects_vote_revoke_change(client, proposal, user1, user2, admin):
    pid = proposal["id"]
    v = vote(client, pid, "YES", user1).json()
    client.patch(f"/proposals/{pid}/close", headers=admin)
    assert vote(client, pid, "YES", user2).status_code == 409
    assert client.delete(f"/votes/{v['id']}", headers=user1).status_code == 409
    assert client.put(f"/votes/{v['id']}", json={"vote": "NO"}, headers=user1).status_code == 409
    assert client.get(f"/proposals/{pid}/results").json()["total"] == 1  # results still readable


def _expire(db_session, pid):
    p = db_session.get(Proposal, pid)
    p.deadline = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(minutes=1)
    db_session.commit()


def test_expired_proposal_rejects_vote_and_status_flips(client, db_session, proposal, user1):
    _expire(db_session, proposal["id"])
    r = vote(client, proposal["id"], "YES", user1)
    assert r.status_code == 409
    assert client.get(f"/proposals/{proposal['id']}").json()["status"] == "EXPIRED"


def test_expired_proposal_rejects_revoke(client, db_session, proposal, user1):
    v = vote(client, proposal["id"], "YES", user1).json()
    _expire(db_session, proposal["id"])
    assert client.delete(f"/votes/{v['id']}", headers=user1).status_code == 409


def test_list_auto_expires_overdue(client, db_session, proposal):
    _expire(db_session, proposal["id"])
    assert client.get("/proposals/").json()[0]["status"] == "EXPIRED"


def test_admin_cannot_close_expired(client, db_session, proposal, admin):
    _expire(db_session, proposal["id"])
    assert client.patch(f"/proposals/{proposal['id']}/close", headers=admin).status_code == 409


def test_my_vote_reported_per_user(client, proposal, user1, user2):
    vote(client, proposal["id"], "YES", user1)
    mine = client.get(f"/proposals/{proposal['id']}", headers=user1).json()
    other = client.get(f"/proposals/{proposal['id']}", headers=user2).json()
    assert mine["my_vote"] == "YES" and mine["my_vote_id"] is not None
    assert other["my_vote"] is None


def test_voter_identity_comes_from_token_not_body(client, proposal, user1, user2):
    r = client.post(
        f"/proposals/{proposal['id']}/vote",
        json={"vote": "YES", "user_id": 999, "voter_name": "someone-else"},
        headers=user1,
    )
    assert r.status_code == 201 and r.json()["voter_name"] == "user1"


def test_deleting_proposal_cascades_votes(db_session, client, proposal, user1):
    vote(client, proposal["id"], "YES", user1)
    db_session.delete(db_session.get(Proposal, proposal["id"]))
    db_session.commit()
    assert db_session.query(Vote).count() == 0
