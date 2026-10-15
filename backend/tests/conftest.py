import os

# Must be set BEFORE the app is imported so tests never touch voting.db
os.environ["DATABASE_URL"] = "sqlite://"
os.environ["SECRET_KEY"] = "test-secret-key"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models import User
from app.security import hash_password


@pytest.fixture()
def db_session():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    from sqlalchemy import event

    @event.listens_for(engine, "connect")
    def _fk(dbapi_con, _):
        dbapi_con.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, autoflush=False)
    session = Session()
    yield session
    session.close()


@pytest.fixture()
def client(db_session):
    def override():
        yield db_session

    app.dependency_overrides[get_db] = override
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def _login(client, username, password):
    r = client.post("/auth/login", json={"username": username, "password": password})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture()
def make_user(client, db_session):
    def _make(username, password="Password1!", role="USER"):
        db_session.add(User(username=username, password=hash_password(password), role=role))
        db_session.commit()
        return _login(client, username, password)

    return _make


@pytest.fixture()
def user1(make_user):
    return make_user("user1")


@pytest.fixture()
def user2(make_user):
    return make_user("user2")


@pytest.fixture()
def admin(make_user):
    return make_user("admin", role="ADMIN")


@pytest.fixture()
def proposal(client, admin):
    r = client.post(
        "/proposals/",
        json={"title": "Build a park", "description": "Should we build a park?"},
        headers=admin,
    )
    assert r.status_code == 201, r.text
    return r.json()
