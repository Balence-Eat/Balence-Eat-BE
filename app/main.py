from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, timezone, date as date_class
from typing import List

from app import models, user_schemas, food_schemas, auth
from app.models import Meal, Food, MealFood, User
from app.food_schemas import (
    MealCreate, MealOut, InventoryOut, MealFoodOut,
    FoodRegisterResponse, MessageResponse, AIDietResponse,
    FoodSearchOut, MealUpdate
)
from app.database import engine
from app.dependencies import get_db
from app.gemini_client import ask_gemini

app = FastAPI()
models.Base.metadata.create_all(engine)

@app.post("/signup", status_code=201, response_model=user_schemas.UserResponse)
async def signup(user: user_schemas.UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(models.User).filter(models.User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="이미 존재하는 이메일입니다.")
    hashed_pw = auth.get_password_hash(user.password)
    new_user = models.User(
        email=user.email,
        hashed_pw=hashed_pw,
        name=user.name,
        gender=user.gender,
        height=user.height,
        weight=user.weight,
        age=user.age,
        allergies=user.allergies,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    new_goal = models.Goal(user_id=new_user.user_id, weight=user.goal.weight, date=user.goal.date)
    db.add(new_goal)
    db.commit()
    db.refresh(new_goal)
    new_user.goal = new_goal
    return new_user

@app.post("/login", status_code=200, response_model=user_schemas.LoginResponse)
async def login(db: Session = Depends(get_db), request: OAuth2PasswordRequestForm = Depends()):
    user = db.query(models.User).filter(models.User.email == request.username).first()
    if not user or not auth.verify_password(request.password, user.hashed_pw):
        raise HTTPException(status_code=401, detail="이메일 또는 비밀번호가 틀렸습니다.")
    token = auth.create_access_token(data={"sub": str(user.user_id)})
    return {"access_token": token, "token_type": "bearer"}

@app.get("/profile", response_model=user_schemas.UserResponse)
async def read_users_me(current_user: models.User = Depends(auth.get_current_user)):
    return current_user

@app.patch("/profile/allergies", response_model=MessageResponse)
def update_allergies(allergies: str, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    current_user.allergies = allergies
    db.commit()
    return {"message": "알레르기 정보가 업데이트되었습니다"}

@app.patch("/profile/edit-profile", response_model=MessageResponse)
def edit_profile(update_data: user_schemas.UserUpdate, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    for field, value in update_data.model_dump(exclude_unset=True).items():
        if field == "goal" and value is not None:
            if current_user.goal:
                for sub_field, sub_value in value.items():
                    setattr(current_user.goal, sub_field, sub_value)
            else:
                new_goal = models.Goal(**value)
                current_user.goal = new_goal
                db.add(new_goal)
        else:
            setattr(current_user, field, value)
    db.commit()
    db.refresh(current_user)
    return {"message": "프로필 정보가 업데이트되었습니다"}

@app.post("/foods", response_model=FoodRegisterResponse)
def add_food(food: food_schemas.FoodCreate, db: Session = Depends(get_db)):
    new_food = models.Food(**food.dict())
    db.add(new_food)
    db.commit()
    return {"message": "음식이 등록되었습니다", "food_id": new_food.food_id}

@app.post("/inventory", response_model=MessageResponse)
def add_inventory(data: food_schemas.InventoryBase, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    item = db.query(models.UserFoodInventory).filter_by(user_id=current_user.user_id, food_id=data.food_id).first()
    if item:
        item.quantity += data.quantity
    else:
        item = models.UserFoodInventory(user_id=current_user.user_id, **data.dict())
        db.add(item)
    db.commit()
    return {"message": "재고가 추가되었습니다"}

@app.get("/inventory", response_model=List[InventoryOut])
def get_inventory(db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    inventories = db.query(models.UserFoodInventory).filter_by(user_id=current_user.user_id).all()
    result = []
    for inv in inventories:
        food = db.query(models.Food).filter_by(food_id=inv.food_id).first()
        result.append({"food_id": inv.food_id, "food_name": food.name if food else "Unknown", "quantity": inv.quantity})
    return result

@app.post("/meals", response_model=MessageResponse)
def add_meal(meal: MealCreate, db: Session = Depends(get_db), current_user: User = Depends(auth.get_current_user)):
    new_meal = Meal(user_id=current_user.user_id, meal_type=meal.meal_type, datetime=datetime.now(timezone.utc))
    db.add(new_meal)
    db.flush()
    for item in meal.items:
        food = db.query(Food).filter(Food.food_id == item.food_id).first()
        if not food:
            raise HTTPException(status_code=404, detail="해당 음식이 존재하지 않습니다.")
        meal_food = MealFood(
            meal_id=new_meal.meal_id,
            food_id=food.food_id,
            quantity=item.quantity,
            calories=(food.calories_per_unit or 0) * item.quantity,
            protein=(food.protein_per_unit or 0) * item.quantity,
            carbs=(food.carbs_per_unit or 0) * item.quantity,
            fat=(food.fat_per_unit or 0) * item.quantity
        )
        db.add(meal_food)
    db.commit()
    return {"message": "한 끼 저장 완료"}

@app.get("/meals", response_model=List[MealOut])
def get_meals(date: str = None, meal_type: str = None, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    query = db.query(models.Meal).filter(models.Meal.user_id == current_user.user_id)
    if date:
        try:
            date_obj = datetime.strptime(date, "%Y-%m-%d").date()
            query = query.filter(models.Meal.datetime.cast(date_class) == date_obj)
        except ValueError:
            raise HTTPException(status_code=400, detail="날짜 형식은 YYYY-MM-DD여야 합니다.")
    if meal_type:
        query = query.filter(models.Meal.meal_type == meal_type)
    meals = query.order_by(models.Meal.datetime.desc()).all()
    result = []
    for meal in meals:
        total = {"calories": 0, "protein": 0, "carbs": 0, "fat": 0}
        foods = []
        for mf in meal.meal_foods:
            foods.append({
                "food_name": mf.food.name,
                "quantity": mf.quantity,
                "calories": mf.calories,
                "protein": mf.protein,
                "carbs": mf.carbs,
                "fat": mf.fat
            })
            total["calories"] += mf.calories or 0
            total["protein"] += mf.protein or 0
            total["carbs"] += mf.carbs or 0
            total["fat"] += mf.fat or 0
        result.append({
            "meal_id": meal.meal_id,
            "datetime": meal.datetime.isoformat(),
            "meal_type": meal.meal_type,
            "total": total,
            "foods": foods
        })
    return result

@app.get("/ai-diet", response_model=AIDietResponse)
def get_ai_diet(db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    user = current_user
    goal = db.query(models.Goal).filter_by(user_id=user.user_id).order_by(models.Goal.date.desc()).first()
    meals = db.query(models.Meal).filter(models.Meal.user_id == user.user_id).all()
    total_eaten = 0
    for meal in meals:
        for mf in meal.meal_foods:
            total_eaten += mf.calories or 0
    inventory = db.query(models.UserFoodInventory).filter_by(user_id=user.user_id).all()
    food_items = [
        {"name": db.query(models.Food).filter_by(food_id=inv.food_id).first().name, "quantity": inv.quantity}
        for inv in inventory if db.query(models.Food).filter_by(food_id=inv.food_id).first()
    ]
    def filter_allergens(user, items):
        if not user.allergies:
            return items
        allergy_list = [a.strip() for a in user.allergies.split(",")]
        return [item for item in items if item["name"] not in allergy_list]
    safe_items = filter_allergens(user, food_items)
    prompt = f"""사용자의 목표 칼로리는 {goal.weight * 30}kcal이며, 오늘 섭취한 칼로리는 {total_eaten}kcal입니다.\n현재 가지고 있는 재료는 다음과 같습니다:\n{', '.join([f'{item["name"]}({item["quantity"]}개)' for item in safe_items])}\n이 재료와 정보를 바탕으로 아침, 점심, 저녁 식단을 추천해주세요."""
    ai_response = ask_gemini(prompt)
    return {"recommendation": ai_response.strip()}

@app.get("/foods/search", response_model=List[FoodSearchOut])
def search_foods(name: str, db: Session = Depends(get_db)):
    results = db.query(models.Food).filter(models.Food.name.ilike(f"%{name}%")).all()
    return [{"food_id": food.food_id, "name": food.name} for food in results]

@app.patch("/meals/edit-meal", response_model=MessageResponse)
def edit_mealfood(update_data: MealUpdate, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    meal = db.query(models.Meal).filter(
        models.Meal.meal_id == update_data.meal_id,
        models.Meal.user_id == current_user.user_id
    ).first()

    if not meal:
        raise HTTPException(status_code=404, detail="해당 식사가 존재하지 않습니다.")

    if update_data.meal_type:
        meal.meal_type = update_data.meal_type

    if update_data.items is not None:
        db.query(models.MealFood).filter(models.MealFood.meal_id == meal.meal_id).delete()
        db.flush()

        for item in update_data.items:
            food = db.query(models.Food).filter_by(food_id=item.food_id).first()
            if not food:
                raise HTTPException(status_code=404, detail=f"음식 ID {item.food_id}가 존재하지 않습니다.")

            new_meal_food = models.MealFood(
                meal_id=meal.meal_id,
                food_id=food.food_id,
                quantity=item.quantity,
                calories=food.calories_per_unit * item.quantity,
                protein=food.protein_per_unit * item.quantity,
                carbs=food.carbs_per_unit * item.quantity,
                fat=food.fat_per_unit * item.quantity
            )
            db.add(new_meal_food)

    db.commit()
    return {"message": "식사 정보가 수정되었습니다."}
