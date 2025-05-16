from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated
from sqlalchemy.orm import Session
from app import models, user_schemas, auth
from app.database import engine
from app.dependencies import get_db

app = FastAPI()

## ORM에서 정의한 테이블을 실제 DB에 생성
models.Base.metadata.create_all(engine)

## DB 의존성 설정
db_dependency = Annotated[Session, Depends(get_db)]


## 회원가입
@app.post("/signup", status_code=201, response_model=user_schemas.UserResponse)
async def signup(user: user_schemas.UserCreate, db: db_dependency):
    ## 이메일 중복 확인
    existing_user = (
        db.query(models.User).filter(models.User.email == user.email).first()
    )
    if existing_user:
        raise HTTPException(status_code=400, detail="이미 존재하는 이메일입니다.")

    ## 비밀번호 해싱
    hashed_pw = auth.get_password_hash(user.password)

    ## 유저 생성
    new_user = models.User(
        email=user.email,
        hashed_pw=hashed_pw,
        name=user.name,
        gender=user.gender,
        height=user.height,
        weight=user.weight,
        age=user.age,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    # user_id가 db에 commit을 해야 생성되기 때문에 refresh 후 goal을 생성해야 함.

    ## 목표 생성
    new_goal = models.Goal(
        user_id=new_user.user_id,
        weight=user.goal.weight,
        date=user.goal.date,
    )

    db.add(new_goal)
    db.commit()
    db.refresh(new_goal)

    ## 관계 연결
    new_user.goal = new_goal

    return new_user


## 로그인
@app.post("/login", status_code=200, response_model=user_schemas.LoginResponse)
async def login(db: db_dependency, request: OAuth2PasswordRequestForm = Depends()):
    ## 유저 이메일 확인
    user = db.query(models.User).filter(models.User.email == request.username).first()
    if not user or not auth.verify_password(request.password, user.hashed_pw):
        raise HTTPException(
            status_code=401, detail="이메일 또는 비밀번호가 틀렸습니다."
        )

    ## 토큰 발급
    token = auth.create_access_token(data={"sub": str(user.user_id)})
    return {"access_token": token, "token_type": "bearer"}


## 프로필 조회
@app.get("/profile", response_model=user_schemas.UserResponse)
async def read_users_me(current_user: models.User = Depends(auth.get_current_user)):
    return current_user
