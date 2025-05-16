from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.models import User
from app.dependencies import get_db
import os

"""로그인 보안 관련 파일"""

## JWT 토큰 스키마
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

## 비밀번호 해싱 설정
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

## JWT 설정
load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"


## 비번 해싱 함수
def get_password_hash(pwd: str) -> str:
    return pwd_context.hash(pwd)


## 비번 검증
def verify_password(plain_pwd, hased_pwd):
    return pwd_context.verify(plain_pwd, hased_pwd)


## JWT 토큰 생성
def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=30))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


## JWT 토큰 인증
def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
):
    credential_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="유효하지 않은 인증 정보입니다.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        ## 토큰을 decode 하여 user_id 추출
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credential_exception

    except JWTError:
        raise credential_exception

    user = db.query(User).filter(User.user_id == user_id).first()
    ## 추출한 user_id가 없을 시
    if user is None:
        raise credential_exception

    return user
