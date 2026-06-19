def signup_helper(client, session, user: str, email: str):
    response = client.post("/auth/signup", json={
        "user": user,
        "email": email,
        "password": "testpassword"
    })
    
    
    return response.status_code, response.json(), response.cookies
