from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from models import User
from core.security import create_verify_token, get_password_hash, verify_password
from email_utils import send_verification_email

DUMMY_HASH = "$2b$12$LcY8WID9uI856Yg9D6A0O.M7fXpZ6vA9uT9eR9wQ9bC9aX9zY9wQu"


class InvalidCredentials(Exception):
    pass


class EmailNotVerified(Exception):
    pass


class InvalidTokenClaims(Exception):
    pass


class MissingSubject(Exception):
    pass


class UserNotFound(Exception):
    pass


class AlreadyVerified(Exception):
    pass


def signup(session: Session, user: str, email: str, password: str) -> None:
    new_user = User(user=user, email=email, password=get_password_hash(password), is_verified=False)
    verify_token = create_verify_token(data={"sub": str(new_user.id)})
    try:
        session.add(new_user)
        session.commit()
        session.refresh(new_user)
    except IntegrityError:
        session.rollback()
        send_verification_email.delay(new_user.email, "user already exists")
        return

    send_verification_email.delay(new_user.email, verify_token)


def authenticate(session: Session, email: str, password: str) -> User:
    statement = select(User).where(User.email == email)
    register = session.exec(statement).first()

    if not register:
        verify_password(password, DUMMY_HASH)
        raise InvalidCredentials()

    if not verify_password(password, register.password):
        raise InvalidCredentials()

    if not register.is_verified:
        verify_token = create_verify_token(data={"sub": str(register.id)})
        send_verification_email.delay(register.email, verify_token)
        raise EmailNotVerified()

    return register


def verify_email(session: Session, payload: dict) -> User:
    purpose = payload.get("purpose")
    if purpose != "verify_email":
        raise InvalidTokenClaims()
    if payload.get("exp") is None:
        raise InvalidTokenClaims()

    user_id = payload.get("sub")
    if user_id is None:
        raise MissingSubject()

    user = session.exec(select(User).where(User.id == UUID(user_id))).first()
    if not user:
        raise UserNotFound()
    if user.is_verified:
        raise AlreadyVerified()

    user.is_verified = True
    session.add(user)
    session.commit()
    session.refresh(user)
    return user
