from pydantic import BaseModel
from enum import Enum
from typing import List, Dict, Optional


# ====================== ENUM ======================

class MealType(str, Enum):
    아침 = "아침"
    점심 = "점심"
    저녁 = "저녁"


<<<<<<< HEAD
# ====================== 음식 등록 ======================

=======
>>>>>>> 74a10d5e201312c706adbb16532ab7c94e60c495
class FoodCreate(BaseModel):
    name: str
    unit: int
    calories_per_unit: int
    protein_per_unit: int
    carbs_per_unit: int
    fat_per_unit: int
    allergens: Optional[str] = None


# ====================== 음식 검색 응답 ======================

class FoodSearchOut(BaseModel):
    food_id: int
    name: str


# ====================== 재고 등록/조회 ======================

class InventoryBase(BaseModel):
    food_id: int
    quantity: int


<<<<<<< HEAD
class InventoryOut(BaseModel):
    food_id: int
    food_name: str
    quantity: int


# ====================== 식사 기록 저장 요청 ======================

=======
# ====================== 식사 기록 ======================


class MealCreate(BaseModel):
    food_name: str
    quantity: int
    meal_type: MealType


>>>>>>> 74a10d5e201312c706adbb16532ab7c94e60c495
class MealFoodItem(BaseModel):
    food_id: int
    quantity: int


class MealCreate(BaseModel):
    meal_type: MealType
<<<<<<< HEAD
    items: List[MealFoodItem]


# ====================== 식사 기록 수정 요청 ======================

class MealUpdate(BaseModel):
    meal_id: int
    meal_type: Optional[MealType] = None
    items: Optional[List[MealFoodItem]] = None


# ====================== 식사 기록 응답 ======================

class MealFoodOut(BaseModel):
    food_name: str
    quantity: int
    calories: int
    protein: int
    carbs: int
    fat: int


class MealOut(BaseModel):
    meal_id: int
    datetime: str
    meal_type: MealType
    total: Dict[str, int]
    foods: List[MealFoodOut]


# ====================== 공통 메시지 응답 ======================

class MessageResponse(BaseModel):
    message: str


# ====================== 음식 등록 응답 ======================

class FoodRegisterResponse(BaseModel):
    message: str
    food_id: int


# ====================== AI 식단 추천 응답 ======================

class AIDietResponse(BaseModel):
    recommendation: str
=======
    items: list[MealFoodItem]


class MealUpdate(BaseModel):
    meal_id: int
    meal_type: MealType | None = None
    items: list[MealFoodItem] | None = None
>>>>>>> 74a10d5e201312c706adbb16532ab7c94e60c495
