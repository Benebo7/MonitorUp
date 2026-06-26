from fastapi import APIRouter, HTTPException, Depends, status, Request
from pydantic import BaseModel
from sqlmodel import Session, select
from limiter import limiter
from fastapi.responses import JSONResponse
from fastapi import Cookie
from security import create_access_token, create_refresh_token, verify_password,create_verify_token,get_password_hash, SECRET_KEY, ALGORITHM
import jwt
from sqlalchemy.exc import IntegrityError
from email_utils import send_verification_email
from database import get_session, User
from uuid import UUID

router = APIRouter(prefix="/auth", tags=["Auth"])

class SignupInput(BaseModel):
    user: str
    email: str
    password: str
class LoginInput(BaseModel):
    email: str
    password: str

@router.post("/signup", status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
def signup(request: Request, data: SignupInput, session: Session = Depends(get_session)):
   
    new_user = User(
        user=data.user,
        email=data.email,
        password=get_password_hash(data.password),
        is_verified=False
    )
    verify_token = create_verify_token(data={"sub": str(new_user.id)} )
    try:

        session.add(new_user)
        session.commit()
        session.refresh(new_user)
    
    except IntegrityError:
        session.rollback()
        send_verification_email.delay(new_user.email, "user already exists")
        return {"message": "User created successfully"}

    send_verification_email.delay(new_user.email, verify_token)

    

    return {"message": "User created successfully"}

@router.post("/login")
def login(data: LoginInput, session: Session = Depends(get_session)):
    dummy = "$2b$12$LcY8WID9uI856Yg9D6A0O.M7fXpZ6vA9uT9eR9wQ9bC9aX9zY9wQu"

    statement = select(User).where(User.email == data.email)
    register = session.exec(statement).first()

    


    if not register:
        verify_password(data.password, dummy)
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not verify_password(data.password, register.password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if register.is_verified == False:
        verify_token = create_verify_token(data={"sub": str(register.id)})
        send_verification_email.delay(register.email, verify_token)
        raise HTTPException(status_code=401, detail="Email not verified")
        

    refresh_token = create_refresh_token(data={"sub": str(register.id)})
    access_token = create_access_token(data={"sub": str(register.id)})
    response = JSONResponse(content={"access_token": access_token, "token_type": "bearer"})
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        samesite="lax",
        secure=True,
        path="/auth",
        max_age=604800
    )
    return response


@router.post("/refresh")
def refresh(refresh_token: str = Cookie(default=None)):
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Refresh token missing")

    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        new_access_token = create_access_token(data={"sub": user_id})
        return {"access_token": new_access_token, "token_type": "bearer"}

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Refresh token expired")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")


@router.get("/verify")
@limiter.limit("5/minute")
def verify(request: Request, token: str, session: Session = Depends(get_session)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        purpose: str = payload.get("purpose")
        if purpose != "verify_email":
            raise HTTPException(status_code=400, detail="Invalid token")
        expiration = payload.get("exp")
        if expiration is None:
            raise HTTPException(status_code=400, detail="Invalid token")
        
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")

        user = session.exec(select(User).where(User.id == UUID(user_id))).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        if user.is_verified:
            raise HTTPException(status_code=400, detail="User already verified")

        user.is_verified = True
        session.add(user)
        session.commit()
        session.refresh(user)
        refresh_token = create_refresh_token(data={"sub": str(user.id)})
        access_token = create_access_token(data={"sub": str(user.id)})
        response = JSONResponse(content={"access_token": access_token, "token_type": "bearer", "detail": "Email verified successfully"})
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            samesite="lax",
            secure=True,
            path="/auth",
            max_age=604800
        )
        
        return response

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=400, detail="Token has expired")
    except jwt.PyJWTError:
        raise HTTPException(status_code=400, detail="Invalid token")
    except IntegrityError:
        raise HTTPException(status_code=400, detail="Database integrity error")
        
        



@router.post("/logout")        
def logout():
    response = JSONResponse(content={"message": "Logged out successfully"})
    response.delete_cookie(key="refresh_token", path="/auth")
    return response