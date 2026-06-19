from routers.auth import get_password_hash, verify_password
from tests.signup_helper import signup_helper
def test_hashing():
    
    password = "testpassword"
    hashed_password = get_password_hash(password)

    assert hashed_password != password
    assert verify_password(password, hashed_password) == True
    assert verify_password("wrongpassword", hashed_password) == False

    

