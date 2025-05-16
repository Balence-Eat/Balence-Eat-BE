from app.database import SessionLocal


def get_db():
    db = SessionLocal()  # 세션 객체 생성
    try:
        yield db  # 세션 객체 반환
    finally:
        db.close()  # 요청이 끝나면 세션 종료
