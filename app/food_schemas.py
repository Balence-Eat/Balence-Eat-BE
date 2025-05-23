from pydantic import BaseModel
from enum import Enum


class MealType(str, Enum):
    아침 = "아침"
    점심 = "점심"
    저녁 = "저녁"
class FoodCreate(BaseModel):
    name: str
    unit: int
    calories_per_unit: int
    protein_per_unit: int
    carbs_per_unit: int
    fat_per_unit: int
    allergens: str = None


# ====================== 재고 ======================


class InventoryBase(BaseModel):
    food_id: int
    quantity: int


# ====================== 식사 기록 ======================

class MealCreate(BaseModel):
    food_name: str
    quantity: int
    meal_type: MealType 
    
class MealFoodItem(BaseModel):
    food_id: int
    quantity: int

class MealCreate(BaseModel):
    meal_type: MealType
    items: list[MealFoodItem]
