from sqlmodel import select
from database import User
from security import create_verify_token

def signup_helper(client, session, user: str, email: str):
    response_signup = client.post("/auth/signup", json={
        "user": user,
        "email": email,
        "password": "testpassword"
    })
    
    new_user = session.exec(select(User).where(User.email == email)).first()
    
    verify_token = create_verify_token(data={"sub": str(new_user.id)} )
    response = client.get(f"/auth/verify?token={verify_token}")


    
    
    return response.status_code, response.json(), response.cookies
