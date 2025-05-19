from pydantic import BaseModel

"""음식 관련"""

# ====================== 음식 ======================


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
    food_id: int
    quantity: int
