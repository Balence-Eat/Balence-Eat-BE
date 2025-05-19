# app/gemini_client.py
import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")


def ask_gemini(prompt: str):
    if not API_KEY:
        raise Exception("❗ GEMINI_API_KEY가 .env에 설정되어 있지 않습니다.")

    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-pro-002:generateContent?key={API_KEY}"  # ✅ 변수명 수정
    headers = {"Content-Type": "application/json"}
    body = {"contents": [{"parts": [{"text": prompt}]}]}

    response = requests.post(url, headers=headers, json=body)
    if response.status_code != 200:
        raise Exception(f"Gemini 호출 실패: {response.status_code} - {response.text}")

    data = response.json()
    return data["candidates"][0]["content"]["parts"][0]["text"]
