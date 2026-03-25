import io
import pytest
from fastapi.testclient import TestClient


def test_health_check(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_register_user(client):
    resp = client.post("/api/auth/register", json={
        "username": "alice",
        "email": "alice@example.com",
        "password": "password123",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["username"] == "alice"
    assert data["email"] == "alice@example.com"


def test_register_duplicate_username(client):
    payload = {"username": "bob", "email": "bob@example.com", "password": "pw"}
    client.post("/api/auth/register", json=payload)
    resp = client.post("/api/auth/register", json={"username": "bob", "email": "bob2@example.com", "password": "pw"})
    assert resp.status_code == 400


def test_login(client):
    client.post("/api/auth/register", json={"username": "carol", "email": "carol@example.com", "password": "pw123"})
    resp = client.post("/api/auth/login", data={"username": "carol", "password": "pw123"})
    assert resp.status_code == 200
    assert "access_token" in resp.json()


def test_login_wrong_password(client):
    client.post("/api/auth/register", json={"username": "dave", "email": "dave@example.com", "password": "pw123"})
    resp = client.post("/api/auth/login", data={"username": "dave", "password": "wrongpw"})
    assert resp.status_code == 401


def test_create_touch(client, auth_headers):
    resp = client.post("/api/touches/", json={"name": "Test Touch", "description": "desc"}, headers=auth_headers)
    assert resp.status_code == 201
    assert resp.json()["name"] == "Test Touch"


def test_list_touches(client, auth_headers):
    client.post("/api/touches/", json={"name": "Touch1"}, headers=auth_headers)
    client.post("/api/touches/", json={"name": "Touch2"}, headers=auth_headers)
    resp = client.get("/api/touches/", headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_get_touch(client, auth_headers):
    create_resp = client.post("/api/touches/", json={"name": "MyTouch"}, headers=auth_headers)
    touch_id = create_resp.json()["id"]
    resp = client.get(f"/api/touches/{touch_id}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["name"] == "MyTouch"


def test_update_touch(client, auth_headers):
    create_resp = client.post("/api/touches/", json={"name": "OldName"}, headers=auth_headers)
    touch_id = create_resp.json()["id"]
    resp = client.put(f"/api/touches/{touch_id}", json={"name": "NewName"}, headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["name"] == "NewName"


def test_upload_method_file(client, auth_headers):
    create_resp = client.post("/api/touches/", json={"name": "MethodTouch"}, headers=auth_headers)
    touch_id = create_resp.json()["id"]
    method_content = "12345678\n" * 4 + "21436587\n" * 16
    resp = client.post(
        f"/api/touches/{touch_id}/method",
        files={"file": ("method.txt", method_content.encode(), "text/plain")},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["n_bells"] == 8
    assert data["rounds_rows"] == 4


def test_create_performance(client, auth_headers):
    create_resp = client.post("/api/touches/", json={"name": "PerfTouch"}, headers=auth_headers)
    touch_id = create_resp.json()["id"]
    timing_content = "Bell No,Actual Time\n" + "\n".join(
        f"{i % 8 + 1},{10000 + i * 200}" for i in range(160)
    )
    resp = client.post(
        f"/api/touches/{touch_id}/performances",
        data={"label": "Perf1", "order_index": 0},
        files={"file": ("timing.csv", timing_content.encode(), "text/csv")},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    assert resp.json()["label"] == "Perf1"


def test_list_performances(client, auth_headers):
    create_resp = client.post("/api/touches/", json={"name": "PerfTouch"}, headers=auth_headers)
    touch_id = create_resp.json()["id"]
    timing_content = "Bell No,Actual Time\n1,10000.0\n"
    for label in ["A", "B"]:
        client.post(
            f"/api/touches/{touch_id}/performances",
            data={"label": label},
            files={"file": ("t.csv", timing_content.encode(), "text/csv")},
            headers=auth_headers,
        )
    resp = client.get(f"/api/touches/{touch_id}/performances", headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_delete_performance(client, auth_headers):
    create_resp = client.post("/api/touches/", json={"name": "Touch"}, headers=auth_headers)
    touch_id = create_resp.json()["id"]
    timing_content = "Bell No,Actual Time\n1,10000.0\n"
    perf_resp = client.post(
        f"/api/touches/{touch_id}/performances",
        data={"label": "ToDelete"},
        files={"file": ("t.csv", timing_content.encode(), "text/csv")},
        headers=auth_headers,
    )
    perf_id = perf_resp.json()["id"]
    resp = client.delete(f"/api/touches/{touch_id}/performances/{perf_id}", headers=auth_headers)
    assert resp.status_code == 204


def test_delete_touch(client, auth_headers):
    create_resp = client.post("/api/touches/", json={"name": "ToDelete"}, headers=auth_headers)
    touch_id = create_resp.json()["id"]
    resp = client.delete(f"/api/touches/{touch_id}", headers=auth_headers)
    assert resp.status_code == 204
    resp2 = client.get(f"/api/touches/{touch_id}", headers=auth_headers)
    assert resp2.status_code == 404


def test_get_analysis(client, auth_headers):
    method_content = "12345678\n" * 4 + "21436587\n12345678\n" * 8
    bell_chars = "12345678"
    from backend.services.parser import parse_method_file
    import random
    random.seed(1)
    method_rows = parse_method_file(method_content)
    n_rows = min(20, len(method_rows))
    current_time = 10000.0
    interval = 200.0
    lines = ["Bell No,Actual Time"]
    for row_idx in range(n_rows):
        row_bells = method_rows[row_idx]
        for pos, bell in enumerate(row_bells):
            t = current_time + pos * interval + random.gauss(0, 5)
            lines.append(f"{bell_chars[bell-1]},{t:.1f}")
        current_time += 8 * interval + interval
    timing_content = "\n".join(lines) + "\n"

    create_resp = client.post("/api/touches/", json={"name": "AnalysisTouch"}, headers=auth_headers)
    touch_id = create_resp.json()["id"]
    client.post(
        f"/api/touches/{touch_id}/method",
        files={"file": ("m.txt", method_content.encode(), "text/plain")},
        headers=auth_headers,
    )
    client.post(
        f"/api/touches/{touch_id}/performances",
        data={"label": "Run1"},
        files={"file": ("t.csv", timing_content.encode(), "text/csv")},
        headers=auth_headers,
    )
    resp = client.get(f"/api/touches/{touch_id}/analysis", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "performances" in data


def test_get_characteristics(client, auth_headers):
    method_content = "12345678\n" * 4 + "21436587\n12345678\n" * 8
    bell_chars = "12345678"
    from backend.services.parser import parse_method_file
    import random
    random.seed(2)
    method_rows = parse_method_file(method_content)
    n_rows = min(20, len(method_rows))
    current_time = 10000.0
    interval = 200.0
    lines = ["Bell No,Actual Time"]
    for row_idx in range(n_rows):
        row_bells = method_rows[row_idx]
        for pos, bell in enumerate(row_bells):
            t = current_time + pos * interval + random.gauss(0, 5)
            lines.append(f"{bell_chars[bell-1]},{t:.1f}")
        current_time += 8 * interval + interval
    timing_content = "\n".join(lines) + "\n"

    create_resp = client.post("/api/touches/", json={"name": "CharTouch"}, headers=auth_headers)
    touch_id = create_resp.json()["id"]
    client.post(
        f"/api/touches/{touch_id}/method",
        files={"file": ("m.txt", method_content.encode(), "text/plain")},
        headers=auth_headers,
    )
    perf_resp = client.post(
        f"/api/touches/{touch_id}/performances",
        data={"label": "Run1"},
        files={"file": ("t.csv", timing_content.encode(), "text/csv")},
        headers=auth_headers,
    )
    perf_id = perf_resp.json()["id"]
    resp = client.get(f"/api/touches/{touch_id}/analysis/{perf_id}/characteristics", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    # Should have at least one bell
    assert len(data) > 0
