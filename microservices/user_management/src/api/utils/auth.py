from datetime import datetime, timedelta
from typing import Annotated
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException, status
from jose import JWTError, jwt
from api.models.user import User, UserRole
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer

from config import get_settings
from api.dependencies.database import get_db
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")
settings = get_settings()

with open(settings.private_key_path, "rb") as key_file:
    private_key = key_file.read()
with open(settings.public_key_path, "rb") as key_file:
    public_key = key_file.read()

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now() + expires_delta
    else:
        expire = datetime.now() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, private_key, algorithm=settings.algorithm)
    return encoded_jwt
def decode_token(token: Annotated[str, Depends(oauth2_scheme)]):
    return jwt.decode(token, public_key, algorithms=["RS256"], options={"verify_exp": False})

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, public_key, algorithms=["RS256"])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_admin(
    current_user: Annotated[User, Depends(get_current_user)]
):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=400, detail="Insufficient permissions")
    return current_user
