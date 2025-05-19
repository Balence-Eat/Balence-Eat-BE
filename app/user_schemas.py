from pydantic import BaseModel, EmailStr, Field, NaiveDatetime
from enum import Enum

"""FastAPI 요청/응답 데이터 검증용 모델"""
"""유저 관련"""


## 성별 설정을 위한 Enum 모델
class Gender(Enum):
    M = "M"
    F = "F"


## Goal 생성
class GoalCreate(BaseModel):
    weight: int = Field(ge=1, description="몸무게는 1kg 이상이어야 합니다.")
    date: NaiveDatetime


## Goal 조회
class GoalResponse(BaseModel):
    weight: int
    date: NaiveDatetime


## User 생성 (회원가입)
class UserCreate(BaseModel):
    email: EmailStr
    password: str

    name: str
    gender: Gender
    height: int = Field(ge=1, description="키는 1cm 이상이어야 합니다.")
    weight: int = Field(ge=1, description="몸무게는 1kg 이상이어야 합니다.")
    age: int = Field(ge=1, description="나이는 1세 이상이어야 합니다.")
    allergies: str = None

    goal: GoalCreate  # 회원가입시 목표도 설정

    class Config:
        use_enum_values = True  ## Enum 타입을 직렬화하기 위해 설정


## User 조회 (프로필 보기)
class UserResponse(BaseModel):
    name: str
    gender: Gender
    height: int
    weight: int

    goal: GoalResponse

    class Config:
        use_enum_values = True


## 로그인 응답 (JWT 토근 발급)
class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
