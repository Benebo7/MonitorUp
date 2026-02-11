from fastapi import APIRouter, HTTPException, Depends, status, Request
from pydantic import BaseModel
from sqlmodel import Session, select
from limiter import limiter
from fastapi.responses import JSONResponse
from fastapi import Cookie
from security import create_access_token, create_refresh_token, verify_password, get_password_hash, SECRET_KEY, ALGORITHM
import jwt

from database import get_session, User

router = APIRouter(prefix="/auth", tags=["Auth"])

class LoginInput(BaseModel):
    user: str
    email: str
    password: str


@router.post("/signup", status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
def signup(request: Request, data: LoginInput, session: Session = Depends(get_session)):
    statement = select(User).where(User.user == data.user)
    if session.exec(statement).first():
        raise HTTPException(status_code=400, detail="User already exists")

    new_user = User(
        user=data.user,
        email=data.email,
        password=get_password_hash(data.password)
    )

    session.add(new_user)
    session.commit()

    return {"message": "User created successfully"}


@router.post("/login")
def login(data: LoginInput, session: Session = Depends(get_session)):
    statement = select(User).where(User.user == data.user)
    register = session.exec(statement).first()

    if not register:
        raise HTTPException(status_code=400, detail="Invalid user or password")

    if not verify_password(data.password, register.password):
        raise HTTPException(status_code=401, detail="Invalid user or password")

    refresh_token = create_refresh_token(data={"sub": str(register.id)})
    access_token = create_access_token(data={"sub": str(register.id)})
    response = JSONResponse(content={"access_token": access_token, "token_type": "bearer"})
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        samesite="lax",
        secure=False,
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
