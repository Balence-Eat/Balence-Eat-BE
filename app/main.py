from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from app import models, user_schemas, food_schemas, auth
from app.database import engine
from app.dependencies import get_db
from app.gemini_client import ask_gemini


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
        allergies=user.allergies,
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


## 알러지 정보 수정
@app.patch("/profile/allergies")
def update_allergies(
    allergies: str,
    db: db_dependency,
    current_user: models.User = Depends(auth.get_current_user),
):
    current_user.allergies = allergies
    db.commit()
    return {"message": "알레르기 정보가 업데이트되었습니다"}


## 먹은 음식 등록
@app.post("/foods")
def add_food(food: food_schemas.FoodCreate, db: db_dependency):
    new_food = models.Food(**food.dict())
    db.add(new_food)
    db.commit()
    return {"message": "음식이 등록되었습니다", "food_id": new_food.food_id}


## 음식 재고 등록
@app.post("/inventory")
def add_inventory(
    data: food_schemas.InventoryBase,
    db: db_dependency,
    current_user: models.User = Depends(auth.get_current_user),
):
    item = (
        db.query(models.UserFoodInventory)
        .filter_by(user_id=current_user.user_id, food_id=data.food_id)
        .first()
    )
    if item:
        item.quantity += data.quantity
    else:
        item = models.UserFoodInventory(user_id=current_user.user_id, **data.dict())
        db.add(item)
    db.commit()
    return {"message": "재고가 추가되었습니다"}


## 음식 재고 보기
@app.get("/inventory")
def get_inventory(
    db: db_dependency,
    current_user: models.User = Depends(auth.get_current_user),
):
    inventories = (
        db.query(models.UserFoodInventory).filter_by(user_id=current_user.user_id).all()
    )
    result = []
    for inv in inventories:
        food = db.query(models.Food).filter_by(food_id=inv.food_id).first()
        result.append(
            {
                "food_id": inv.food_id,
                "food_name": food.name if food else "Unknown",
                "quantity": inv.quantity,
            }
        )
    return result


## 식사 저장
@app.post("/meals")
def add_meal(
    meal: food_schemas.MealCreate,
    db: db_dependency,
    current_user: models.User = Depends(auth.get_current_user),
):
    new_meal = models.Meal(
        user_id=current_user.user_id,
        food_id=meal.food_id,
        quantity=meal.quantity,
        datetime=datetime.now(timezone.utc),
    )
    db.add(new_meal)
    db.commit()
    return {"message": "식사 기록이 저장되었습니다"}


## ai 식단 추천
@app.get("/ai-diet")
def get_ai_diet(
    db: db_dependency,
    current_user: models.User = Depends(auth.get_current_user),
):
    user = current_user
    goal = (
        db.query(models.Goal)
        .filter_by(user_id=user.user_id)
        .order_by(models.Goal.date.desc())
        .first()
    )
    meals = db.query(models.Meal).filter(models.Meal.user_id == user.user_id).all()

    total_eaten = 0
    for meal in meals:
        food = db.query(models.Food).filter_by(food_id=meal.food_id).first()
        if food:
            total_eaten += (food.calories_per_unit or 0) * meal.quantity

    inventory = db.query(models.UserFoodInventory).filter_by(user_id=user.user_id).all()
    food_items = []
    for inv in inventory:
        food = db.query(models.Food).filter_by(food_id=inv.food_id).first()
        if food:
            food_items.append({"name": food.name, "quantity": inv.quantity})

    def filter_allergens(user, items):
        if not user.allergies:
            return items
        allergy_list = [a.strip() for a in user.allergies.split(",")]
        return [item for item in items if item["name"] not in allergy_list]

    safe_items = filter_allergens(user, food_items)

    prompt = f"""사용자의 목표 칼로리는 {goal.weight * 30}kcal이며, 오늘 섭취한 칼로리는 {total_eaten}kcal입니다.
현재 가지고 있는 재료는 다음과 같습니다:
{', '.join([f'{item["name"]}({item["quantity"]}개)' for item in safe_items])}
이 재료와 정보를 바탕으로 아침, 점심, 저녁 식단을 추천해주세요."""

    ai_response = ask_gemini(prompt)
    return {"recommendation": ai_response.strip()}
