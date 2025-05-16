from sqlalchemy import Column, Integer, String, Enum, ForeignKey, Date
from sqlalchemy.orm import relationship
from app.database import Base

"""DB 모델"""


## User 테이블
class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_pw = Column(String(100), nullable=False)

    name = Column(String(100), nullable=False)
    gender = Column(Enum("M", "F", name="gender_enum"), nullable=False)
    height = Column(Integer, nullable=False)
    weight = Column(Integer, nullable=False)
    age = Column(Integer, nullable=False)

    goal = relationship(
        "Goal", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )


## Goal 테이블
class Goal(Base):
    __tablename__ = "goals"

    goal_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False
    )
    weight = Column(Integer, nullable=False)
    date = Column(Date, nullable=False)

    user = relationship("User", back_populates="goal")
