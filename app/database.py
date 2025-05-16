from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

## .env 파일 로드
load_dotenv()

## .env에 정의된 DB_URL 불러오기
DB_URL = (
    f"mysql+pymysql://{os.getenv("DB_USER")}:{os.getenv("DB_PASSWORD")}"
    f"@{os.getenv("DB_HOST")}:{os.getenv("DB_PORT")}/{os.getenv("DB_NAME")}"
)


## SQLAlchemy 엔진 생성
engine = create_engine(DB_URL, connect_args={"ssl": {"ssl_disabled": False}})

## engine을 세션과 연결, 세션을 통해서 DB와 상호작용 가능
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

## ORM 모델이 상속받을 Base 클래스 생성.
Base = declarative_base()
