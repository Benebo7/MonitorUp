from tests.signup_helper import signup_helper
from sqlmodel import select
from database import User
from security import checkuser
from fastapi.security import HTTPAuthorizationCredentials
from security import create_verify_token
def test_signup_simple(client, session):
    response = client.post("/auth/signup", json={
        "user": "testuser",
        "email": "testuser@example.com",
        "password": "testpassword"
    })
    assert response.status_code == 201
    user = session.exec(select(User).where(User.email == "testuser@example.com")).first()
    assert user is not None
    assert user.user == "testuser"
    assert user.email == "testuser@example.com"
    assert user.password is not None and user.password != "testpassword"
    assert user.is_verified is False
    
def test_signup_full(client, session):
    status_code, response_json, response_cookies = signup_helper(client, session, "testuser", "testuser@example.com")
    assert status_code == 200
    assert response_json["detail"] == "Email verified successfully"
    assert "access_token" in response_json and response_json["access_token"] is not None
    assert "refresh_token" in response_cookies and response_cookies["refresh_token"] is not None



def test_signup_duplicate_email(client, session):
    
    signup_helper(client, session, "testuser1", "testuser1@example.com")

    
    status_code, response_json, response_cookies = signup_helper(client, session, "testuser2", "testuser1@example.com")
    users = session.exec(select(User).where(User.email == "testuser1@example.com")).all()
    assert len(users) == 1
    assert users[0].user == "testuser1"
    assert status_code == 400 and response_json["detail"] == "User already verified"


def test_login(client, session):
    signup_helper(client, session, "testuser", "testuser@example.com")
    response = client.post("/auth/login", json={
        "email": "testuser@example.com",
        "password": "testpassword"
    })  
    assert response.status_code == 200
    assert "access_token" in response.json() and response.json()["access_token"] is not None
    assert "refresh_token" in response.cookies and response.cookies["refresh_token"] is not None

def test_login_not_verified(client, session):
    client.post("/auth/signup", json={
        "user": "testuser",
        "email": "testuser@example.com",
        "password": "testpassword"
    })
    response = client.post("/auth/login", json={
        "email": "testuser@example.com",
        "password": "testpassword"
    })
    assert response.status_code == 401
    assert response.json()["detail"] == "Email not verified"
    new_user = session.exec(select(User).where(User.email == "testuser@example.com")).first()

    verify_token = create_verify_token(data={"sub": str(new_user.id)} )
    response_verify = client.get(f"/auth/verify?token={verify_token}")
    assert response_verify.status_code == 200
    assert "access_token" in response_verify.json() and response_verify.json()["access_token"] is not None
    assert "refresh_token" in response_verify.cookies and response_verify.cookies["refresh_token"] is not None


def test_login_invalid_email(client, session):
    signup_helper(client, session, "testuser", "testuser@example.com")
    response = client.post("/auth/login", json={
        "email": "testuser2@example.com",
        "password": "wrongpassword"
    })
    assert response.status_code == 401
def test_login_invalid_password(client, session):
    signup_helper(client, session, "testuser", "testuser@example.com")
    response = client.post("/auth/login", json={
        "email": "testuser@example.com",
        "password": "wrongpassword"
    })
    assert response.status_code == 401


    
def test_access_token(client, session):
    status_code, response_json, response_cookies = signup_helper(client, session, "testuser", "testuser@example.com")
    
    
    checks = checkuser(HTTPAuthorizationCredentials(scheme="Bearer", credentials=response_json["access_token"]))
    assert checks == str(session.exec(select(User).where(User.email == "testuser@example.com")).first().id)

def test_refresh_token(client, session):
    status_code, response_json, response_cookies = signup_helper(client, session, "testuser", "testuser@example.com")
    client.cookies.set("refresh_token", response_cookies["refresh_token"])
    response = client.post("/auth/refresh")
    assert response.status_code == 200
    assert "access_token" in response.json() and response.json()["access_token"] is not None