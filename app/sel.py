import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import datetime
import requests

# 한글 폰트 설정
matplotlib.rc('font', family='Malgun Gothic')
matplotlib.rcParams['axes.unicode_minus'] = False

@st.cache_data
def load_data():
    return pd.read_csv("C:/Users/tiran/Downloads/cleaned_grouped_foodDB.csv")

df = load_data()
df["대분류"] = df["대표명"].str.split("_").str[0]

st.title("Balance Eat")

# ✅ JWT 토큰 입력
token = st.text_input("✅ JWT 토큰을 입력해주세요", type="password")

# 음식 검색
search_term = st.text_input("음식 이름을 입력해주세요").lower().strip()
search_filtered = df[df["대표명"].str.contains(search_term, case=False)] if search_term else df

# 대분류 선택
available_categories = sorted(search_filtered["대분류"].unique())
selected_category = st.selectbox("대분류 선택", available_categories)

category_filtered = search_filtered[search_filtered["대분류"] == selected_category]
food_options = category_filtered["대표명"].tolist()

if food_options:
    selected_food = st.selectbox("음식 선택", food_options)
    row = category_filtered[category_filtered["대표명"] == selected_food].iloc[0]

    st.subheader(f"{selected_food}의 영양 성분")
    nutrient_data = {
        "열량 (kcal)": row["열량"],
        "탄수화물 (g)": row["탄수화물"],
        "단백질 (g)": row["단백질"],
        "지방 (g)": row["지방"]
    }
    st.write(pd.DataFrame(nutrient_data.items(), columns=["항목", "값"]))

    if st.button("선택한 음식 저장"):
        if "saved" not in st.session_state:
            st.session_state["saved"] = []

        st.session_state["saved"].append({
            "대표명": row["대표명"],
            "열량": row["열량"],
            "탄수화물": row["탄수화물"],
            "단백질": row["단백질"],
            "지방": row["지방"],
            "저장시간": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        st.success("✅ 저장 완료")

else:
    st.warning("⚠ 해당 조건에 맞는 음식이 없습니다.")

# 저장된 음식 목록 표시
if "saved" in st.session_state and st.session_state["saved"]:
    st.markdown("---")
    st.subheader("저장된 식단")

    saved_df = pd.DataFrame(st.session_state["saved"])

    for idx, row in saved_df.iterrows():
        col1, col2 = st.columns([5, 1])
        with col1:
            st.write(f"{row['대표명']} | 열량: {row['열량']} kcal | 탄: {row['탄수화물']}g, 단: {row['단백질']}g, 지: {row['지방']}g")
        with col2:
            if st.button("❌ 삭제", key=f"delete_{idx}"):
                st.session_state["delete_index"] = idx

    if "delete_index" in st.session_state:
        del_idx = st.session_state.pop("delete_index")
        st.session_state["saved"].pop(del_idx)

    st.subheader("총 영양 성분")
    total = saved_df[["열량", "탄수화물", "단백질", "지방"]].sum()
    st.write(total)

    st.subheader("총 섭취 그래프 (탄/단/지)")
    fig, ax = plt.subplots()
    ax.bar(["탄수화물", "단백질", "지방"], [total["탄수화물"], total["단백질"], total["지방"]])
    st.pyplot(fig)

    # ✅ 식사 타입 선택 추가
    st.markdown("---")
    st.subheader("한끼로 FastAPI에 저장")
    meal_type = st.selectbox("식사 타입 선택", ["아침", "점심", "저녁"])

    if st.button("한끼 저장하기"):
        if not token:
            st.warning("❗ JWT 토큰을 입력해주세요.")
        else:
            success = True
            for row in st.session_state["saved"]:
                try:
                    res = requests.post(
                        "http://localhost:8000/meals",
                        headers={"Authorization": f"Bearer {token}"},
                        json={
                            "food_name": row["대표명"],
                            "quantity": 1,
                            "meal_type": meal_type
                        }
                    )
                    if res.status_code != 200:
                        success = False
                        st.error(f"❌ 실패: {res.status_code} - {res.text}")
                except Exception as e:
                    success = False
                    st.error(f"❌ 예외 발생: {e}")

            if success:
                st.success("✅ FastAPI에 한끼 저장 완료!")
                st.session_state["saved"] = []

# ✅ 서버에서 식사 기록 조회
if st.button("서버에서 식사 기록 불러오기"):
    res = requests.get("http://localhost:8000/meals", headers={"Authorization": f"Bearer {token}"})
    if res.status_code == 200:
        meals = res.json()
        total = {"calories": 0, "protein": 0, "carbs": 0, "fat": 0}
        for meal in meals:
            st.markdown(f"""
            - 🍱 {meal['food_name']} x {meal['quantity']}
              - 열량: {meal['calories']}kcal / 탄: {meal['carbs']}g / 단: {meal['protein']}g / 지: {meal['fat']}g
              - 🕒 {meal['datetime']} / 🍽 {meal['meal_type']}
            """)
            total["calories"] += meal["calories"]
            total["protein"] += meal["protein"]
            total["carbs"] += meal["carbs"]
            total["fat"] += meal["fat"]

        st.subheader("전체 총합")
        st.write(f"🔥 열량: {total['calories']} kcal")
        st.write(f"🥔 탄수화물: {total['carbs']}g")
        st.write(f"🍗 단백질: {total['protein']}g")
        st.write(f"🥑 지방: {total['fat']}g")
    else:
        st.error(f"❌ 식사 기록 불러오기 실패: {res.status_code}")
