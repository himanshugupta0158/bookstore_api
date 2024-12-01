from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
from sqlmodel import Session, select
from app.models import User
from app.auth import hash_password, verify_password, create_access_token, decode_access_token, oauth2_scheme
from app.database import get_session
from datetime import datetime

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/register")
def register_user(username: str, password: str, session: Session = Depends(get_session)):
    existing_user = session.exec(
        select(User).where(User.username == username)).first()
    if existing_user:
        raise HTTPException(status_code=400, details="Username already exists")
    hashed_password = hash_password(password)
    new_user = User(username=username, hashed_password=hashed_password)
    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    return JSONResponse(status_code=201, content={"message": "User registered successfully"})


@router.post("/login")
def login_user(
    username: str,
    password: str,
    request: Request,
    session: Session = Depends(get_session)
):
    """
    Handles user login, creates an access token, and cleans up old tokens in the blacklist.
    """
    user = session.exec(select(User).where(User.username == username)).first()
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Generate new token
    token = create_access_token({"sub": user.username})

    # Remove any existing revoked tokens for this user
    tokens_to_remove = [
        existing_token for existing_token, expiry in request.app.state.revoked_tokens.items()
        if decode_access_token(existing_token).get("sub") == username
    ]

    # Remove the identified tokens from the blacklist
    for token_to_remove in tokens_to_remove:
        del request.app.state.revoked_tokens[token_to_remove]

    return JSONResponse(content={"access_token": token, "token_type": "bearer"}, status_code=200)


@router.post("/logout")
def logout_user(request: Request):
    """
    Logs out the user by adding their current token to the revoked tokens blacklist.
    """
    authorization: str = request.headers.get("Authorization")
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="No valid token provided")

    token = authorization.split("Bearer ")[1]
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    # Add the token to the blacklist with its expiry time
    expiration = payload.get("exp", None)
    if expiration:
        request.app.state.revoked_tokens[token] = datetime.fromtimestamp(
            expiration)

    return JSONResponse(status_code=200, content={"message": "Logged out successfully"})
