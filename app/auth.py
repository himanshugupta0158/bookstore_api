from passlib.context import CryptContext
from fastapi import Request, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from datetime import datetime, timedelta

# configuration | NOTE : use below thing in .env file 
SECRET_KEY = "wgYpKiwQ-r86sjhO1psENvZwfjgwumpmYSjVBsZnzJ4"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="users/login")


# Hashing password
def hash_password(password: str) -> str:
    return pwd_context.hash(password)


# verify password
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


# Creating access token
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# Decode access token
def decode_access_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=ALGORITHM)
        return payload
    except JWTError:
        return None


# Dependency to verify the current user
def get_current_user(request: Request, token: str = Depends(oauth2_scheme)):
    """
    Dependency to extract and verify the current user.
    Checks if the token is revoked using the application's state.
    """
    # Check if the token is in the blacklist
    if token in request.app.state.revoked_tokens:
        # If expired, clean up from the blacklist
        if datetime.utcnow() > request.app.state.revoked_tokens[token]:
            del request.app.state.revoked_tokens[token]
        else:
            raise HTTPException(
                status_code=401,
                detail="Token has been revoked. Please log in again."
            )

    # Decode and validate the token
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication credentials."
        )
    return payload["sub"]  # Return the username or user ID