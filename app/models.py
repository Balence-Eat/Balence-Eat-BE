from sqlalchemy import Column, Integer, String, Enum, ForeignKey, Date, DateTime
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime, timezone

"""DB 모델"""


class Meal(Base):
    __tablename__ = "meals"
    meal_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"))
    datetime = Column(DateTime, default=datetime.now(timezone.utc))
    meal_type = Column(
        Enum("아침", "점심", "저녁", name="meal_type_enum"), nullable=False
    )

    user = relationship("User", back_populates="meals")
    meal_foods = relationship(
        "MealFood", back_populates="meal", cascade="all, delete-orphan"
    )


class MealFood(Base):
    __tablename__ = "meal_food"

    id = Column(Integer, primary_key=True)
    meal_id = Column(Integer, ForeignKey("meals.meal_id", ondelete="CASCADE"))
    food_id = Column(Integer, ForeignKey("foods.food_id", ondelete="CASCADE"))
    quantity = Column(Integer, nullable=False)
    calories = Column(Integer)
    protein = Column(Integer)
    carbs = Column(Integer)
    fat = Column(Integer)

    meal = relationship("Meal", back_populates="meal_foods")
    food = relationship("Food")


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

    allergies = Column(String(255), nullable=True)

    goal = relationship(
        "Goal", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    inventory = relationship(
        "UserFoodInventory", back_populates="user", cascade="all, delete-orphan"
    )
    meals = relationship("Meal", back_populates="user", cascade="all, delete-orphan")


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


## Food 테이블 (영양 정보 포함)
class Food(Base):
    __tablename__ = "foods"

    food_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)

    unit = Column(Integer, nullable=True)
    calories_per_unit = Column(Integer, nullable=True)
    protein_per_unit = Column(Integer, nullable=True)
    carbs_per_unit = Column(Integer, nullable=True)
    fat_per_unit = Column(Integer, nullable=True)
    allergens = Column(String(500), nullable=True)

    inventories = relationship("UserFoodInventory", back_populates="food")


## UserFoodInventory 테이블
class UserFoodInventory(Base):
    __tablename__ = "user_food_inventory"

    inventory_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False
    )
    food_id = Column(
        Integer, ForeignKey("foods.food_id", ondelete="CASCADE"), nullable=False
    )
    quantity = Column(Integer, default=0, nullable=False)

    user = relationship("User", back_populates="inventory")
    food = relationship("Food", back_populates="inventories")
