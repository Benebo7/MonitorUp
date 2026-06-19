from sqlmodel import select
from database import User, Monitor
from tests.signup_helper import signup_helper
from fastapi.security import HTTPAuthorizationCredentials
from security import checkuser
def test_monitor_create(client, session, httpx_mock):
    httpx_mock.add_response(url="https://www.google.com", status_code=200)
    status_code, response_json, response_cookies = signup_helper(client, session, "testuser", "testuser@example.com")
    access_token = response_json["access_token"]
    response = client.post("/monitor/create", json={
        "url": "https://www.google.com",
        "name": "Google"
    }, headers={
        "Authorization": f"Bearer {access_token}"
    })
    print(response.json())
    #Us = session.exec(select(User).where(User.email == "testuser@example.com")).first()
    #monitor = session.exec(select(Monitor).where(Monitor.user_id == Us.id)).first()
    monitor = session.exec(select(Monitor).join(User).where(User.email == "testuser@example.com")).first()
    assert monitor is not None
    assert monitor.name == "Google"
    assert monitor.url == "https://www.google.com"
    assert monitor.status_code == 200



def test_monitor_create_invalid_url(client, session, httpx_mock):
    status_code, response_json, response_cookies = signup_helper(client, session, "testuser", "testuser@example.com")
    access_token = response_json["access_token"]
    httpx_mock.add_response(url="https://httpstat.us/500", status_code=500)
    response = client.post("/monitor/create", json={
        "url": "https://httpstat.us/500",
        "name": "Google"
    }, headers={
        "Authorization": f"Bearer {access_token}"
    })
    monitor = session.exec(select(Monitor).join(User).where(User.email == "testuser@example.com")).first()
    assert monitor is not None
    assert monitor.status_code == 500




def test_monitor_update(client, session, httpx_mock):
    status_code, response_json, response_cookies = signup_helper(client, session, "testuser", "testuser@example.com")
    access_token = response_json["access_token"]
    httpx_mock.add_response(url="https://www.google.com", status_code=200)
    httpx_mock.add_response(url="https://www.github.com", status_code=200)
    rp = client.post("/monitor/create", json={
        "url": "https://www.google.com",
        "name": "Google"
    }, headers={
        "Authorization": f"Bearer {access_token}"
    })
    print(rp.json())
    moni = session.exec(select(Monitor)).first()
    resp = client.put(f"/monitor/update/{moni.id}", json={
        "url": "https://www.github.com",
        "name": "GitHub"
    }, headers={
        "Authorization": f"Bearer {access_token}"
    })
    monitor = session.exec(select(Monitor).join(User).where(User.id == Monitor.user_id)).first()
    print(resp.json())
    if monitor:
        session.refresh(monitor)
    assert monitor is not None
    assert monitor.name == "GitHub"
    assert monitor.url == "https://www.github.com"



def test_monitor_delete(client, session, httpx_mock):
    status_code, response_json, response_cookies = signup_helper(client, session, "testuser", "testuser@example.com")
    access_token = response_json["access_token"]
    httpx_mock.add_response(url="https://www.google.com", status_code=200)
    client.post("/monitor/create", json={
        "url": "https://www.google.com",
        "name": "Google"
    }, headers={
        "Authorization": f"Bearer {access_token}"
    })
    moni = session.exec(select(Monitor)).first()
    client.delete(f"/monitor/delete/{moni.id}", headers={
        "Authorization": f"Bearer {access_token}"
    })
    monitor = session.exec(select(Monitor).join(User).where(User.email == "testuser@example.com")).first()
    assert monitor is None

