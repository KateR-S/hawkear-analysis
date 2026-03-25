import io
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.database import Base, get_db
from backend.main import app

SQLALCHEMY_TEST_URL = "sqlite://"

engine_test = create_engine(
    SQLALCHEMY_TEST_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine_test)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def test_db():
    Base.metadata.create_all(bind=engine_test)
    yield
    Base.metadata.drop_all(bind=engine_test)


@pytest.fixture
def client(test_db):
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers(client):
    client.post("/api/auth/register", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpassword123",
    })
    resp = client.post("/api/auth/login", data={
        "username": "testuser",
        "password": "testpassword123",
    })
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def sample_method_content():
    """8-bell method: 4 rounds then 16 rows of changes."""
    rounds = "12345678\n" * 4
    changes = [
        "21436587",
        "12345678",
        "21436587",
        "12345678",
        "21436587",
        "12345678",
        "21436587",
        "12345678",
        "21436587",
        "12345678",
        "21436587",
        "12345678",
        "21436587",
        "12345678",
        "21436587",
        "12345678",
    ]
    return rounds + "\n".join(changes) + "\n"


@pytest.fixture
def sample_timing_content(sample_method_content):
    """Synthetic CSV timing matching 8 bells, 20 rows."""
    import random
    random.seed(42)
    lines = ["Bell No,Actual Time"]
    n_bells = 8
    n_rows = 20
    current_time = 10000.0
    interval = 200.0
    # Parse the method to get bell ordering per row
    from backend.services.parser import parse_method_file
    method_rows = parse_method_file(sample_method_content)
    bell_chars = "1234567890ET"
    for row_idx in range(n_rows):
        if row_idx < len(method_rows):
            row_bells = method_rows[row_idx]
        else:
            row_bells = list(range(1, n_bells + 1))
        for pos, bell in enumerate(row_bells):
            t = current_time + pos * interval + random.gauss(0, 10)
            bell_char = bell_chars[bell - 1]
            lines.append(f"{bell_char},{t:.1f}")
        current_time += n_bells * interval + interval
    return "\n".join(lines) + "\n"
