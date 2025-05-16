### 현재 폴더 구조
```yaml
BACKEND
│   requirements.txt # Python 의존성 목록 파일
│   erd.vuerd.json # erd 시각화 파일
├───app
│   │   auth.py # 로그인 보안 관련 함수 파일
│   │   database.py # DB 연동 파일
│   │   main.py # 서버 실행 파일
│   │   models.py # ORM 모델 관리 파일
│   │   user_schemas.py # 유저 관련 pydantic 모델 관리 파일
|   |   dependencies.py # DB 의존성 주입 파일
```
---
### 서버 실행 방법

requirements.txt에 맞게 venv 가상환경 실행하시고,
<br>
루트 디렉토리에서 
<br>
```yaml
uvicorn app.main:app --reload
```
<br>
명령어로 서버 실행하시면 됩니다.

---
구현 완료된 기능은 API 명세서 작성했습니다.
궁금한 점이나 수정사항 있으면 편하게 알려주세요~!
