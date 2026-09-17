from fastapi import APIRouter, HTTPException, Depends, status, Request
from pydantic import BaseModel
from sqlmodel import Session
from core.limiter import limiter
from fastapi.responses import JSONResponse
from fastapi import Cookie
from core.security import create_access_token, create_refresh_token, verify_password, create_verify_token, get_password_hash, SECRET_KEY, ALGORITHM
import jwt
from sqlalchemy.exc import IntegrityError
from core.database import get_session
from pydantic import EmailStr as Emailstr
from services import auth_service

router = APIRouter(prefix="/auth", tags=["Auth"])

class SignupInput(BaseModel):
    user: str
    email: Emailstr
    password: str
class LoginInput(BaseModel):
    email: Emailstr
    password: str

@router.post("/signup", status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
def signup(request: Request, data: SignupInput, session: Session = Depends(get_session)):
    auth_service.signup(session, data.user, data.email, data.password)
    return {"message": "User created successfully"}

@router.post("/login")
@limiter.limit("5/minute")
def login(request: Request, data: LoginInput, session: Session = Depends(get_session)):
    try:
        user = auth_service.authenticate(session, data.email, data.password)
    except auth_service.InvalidCredentials:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    except auth_service.EmailNotVerified:
        raise HTTPException(status_code=401, detail="Email not verified")

    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    access_token = create_access_token(data={"sub": str(user.id)})
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
        user = auth_service.verify_email(session, payload)
    except auth_service.InvalidTokenClaims:
        raise HTTPException(status_code=400, detail="Invalid token")
    except auth_service.MissingSubject:
        raise HTTPException(status_code=401, detail="Invalid token")
    except auth_service.UserNotFound:
        raise HTTPException(status_code=404, detail="User not found")
    except auth_service.AlreadyVerified:
        raise HTTPException(status_code=400, detail="User already verified")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=400, detail="Token has expired")
    except jwt.PyJWTError:
        raise HTTPException(status_code=400, detail="Invalid token")
    except IntegrityError:
        raise HTTPException(status_code=400, detail="Database integrity error")

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


@router.post("/logout")
def logout():
    response = JSONResponse(content={"message": "Logged out successfully"})
    response.delete_cookie(key="refresh_token", path="/auth")
    return response
