import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import datetime
import os
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

# 검색 기능
search_term = st.text_input("음식 이름을 입력해주세요").lower().strip()

if search_term:
    mask = df["대표명"].str.contains(search_term, case=False) | df["대분류"].str.contains(search_term, case=False)
    search_filtered = df[mask]
else:
    search_filtered = df

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

        saved_row = {
            "대표명": row["대표명"],
            "열량": row["열량"],
            "탄수화물": row["탄수화물"],
            "단백질": row["단백질"],
            "지방": row["지방"],
            "저장시간": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        st.session_state["saved"].append(saved_row)
        st.success("저장 완료")

else:
    st.warning("⚠ 해당 조건에 맞는 음식이 없습니다.")

if "saved" in st.session_state and st.session_state["saved"]:
    st.markdown("---")
    st.subheader("저장된 식단")

    saved_df = pd.DataFrame(st.session_state["saved"])

    for idx, row in saved_df.iterrows():
        col1, col2 = st.columns([5, 1])
        with col1:
            st.write(f"{row['대표명']} | 열량: {row['열량']} kcal | 탄: {row['탄수화물']}g, 단: {row['단백질']}g, 지: {row['지방']}g")
        with col2:
            if st.button("목록에서 삭제", key=f"delete_{idx}"):
                st.session_state["delete_index"] = idx

    if "delete_index" in st.session_state:
        idx_to_delete = st.session_state.pop("delete_index")
        if idx_to_delete < len(st.session_state["saved"]):
            st.session_state["saved"].pop(idx_to_delete)

    st.subheader("총 영양 성분")
    total_nutrients = saved_df[["열량", "탄수화물", "단백질", "지방"]].sum()
    st.write(total_nutrients)

    st.subheader("총 섭취 탄/단/지 그래프")
    labels = ["탄수화물", "단백질", "지방"]
    values = [total_nutrients["탄수화물"], total_nutrients["단백질"], total_nutrients["지방"]]

    fig, ax = plt.subplots()
    ax.bar(labels, values, color=["skyblue", "green", "pink"])
    ax.set_ylabel("g")
    st.pyplot(fig)

    st.markdown("---")
    st.subheader("한끼로 FastAPI에 저장")

    if st.button("한끼 저장하기"):
        if not token:
            st.warning("⚠️ JWT 토큰을 입력해야 합니다.")
        else:
            success = True
            for row in st.session_state["saved"]:
                try:
                    # ✅ 수정: food_id 제거 → food_name만 전달
                    response = requests.post(
                        "http://localhost:8000/meals",
                        json={"food_name": row["대표명"], "quantity": 1},
                        headers={"Authorization": f"Bearer {token}"}
                    )   

                    if response.status_code != 200:
                        success = False
                        st.error(f"❌ 실패: {response.status_code} - {response.text}")
                except Exception as e:
                    success = False
                    st.error(f"❌ 예외 발생: {e}")
            if success:
                st.success("✅ 한끼 저장 완료 (FastAPI)")
                st.session_state["saved"] = []

if st.button("서버에서 식사 기록 불러오기"):
    response = requests.get(
        "http://localhost:8000/meals",
        headers={"Authorization": f"Bearer {token}"}
    )
    if response.status_code == 200:
        data = response.json()
        total = {"calories": 0, "protein": 0, "carbs": 0, "fat": 0}
        for meal in data:
            st.markdown(f"""
            - 🍽 **{meal['food_name']}** x {meal['quantity']}  
              - 열량: {meal['calories']} kcal  
              - 탄수화물: {meal['carbs']}g / 단백질: {meal['protein']}g / 지방: {meal['fat']}g  
              - 시간: `{meal['datetime']}`
            """)
            total["calories"] += meal["calories"]
            total["protein"] += meal["protein"]
            total["carbs"] += meal["carbs"]
            total["fat"] += meal["fat"]

        st.markdown("---")
        st.subheader("🥗 전체 총합")
        st.write(f"""
        - 총 열량: {total['calories']} kcal  
        - 탄수화물: {total['carbs']}g  
        - 단백질: {total['protein']}g  
        - 지방: {total['fat']}g
        """)
    else:
        st.error("식사 기록을 불러오는 데 실패했습니다.")
