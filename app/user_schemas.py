from pydantic import BaseModel, EmailStr, Field, NaiveDatetime
from enum import Enum

class Gender(Enum):
    M = "M"
    F = "F"

class GoalCreate(BaseModel):
    weight: int = Field(ge=1, description="몸무게는 1kg 이상이어야 합니다.")
    date: NaiveDatetime

class GoalResponse(BaseModel):
    weight: int
    date: NaiveDatetime

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str
    gender: Gender
    height: int = Field(ge=1)
    weight: int = Field(ge=1)
    age: int = Field(ge=1)
    allergies: str = None
    goal: GoalCreate
    class Config:
        use_enum_values = True

class UserResponse(BaseModel):
    name: str
    gender: Gender
    height: int
    weight: int
    goal: GoalResponse
    class Config:
        use_enum_values = True

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

