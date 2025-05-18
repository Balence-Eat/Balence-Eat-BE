import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import datetime
import os

# 한글 폰트 설정
matplotlib.rc('font', family='Malgun Gothic')
matplotlib.rcParams['axes.unicode_minus'] = False

# 저장 경로
SAVE_PATH = "saved_meals.csv"
MEAL_LOG_PATH = "meals_log.csv"

@st.cache_data
def load_data():
    return pd.read_csv("C:/Users/jyt63/Downloads/cleaned_grouped_foodDB.csv")

df = load_data()
df["대분류"] = df["대표명"].str.split("_").str[0]

st.title("Balance Eat")

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

    # 영양 정보 표시
    st.subheader(f"{selected_food}의 영양 성분")
    nutrient_data = {
        "열량 (kcal)": row["열량"],
        "탄수화물 (g)": row["탄수화물"],
        "단백질 (g)": row["단백질"],
        "지방 (g)": row["지방"]
    }
    st.write(pd.DataFrame(nutrient_data.items(), columns=["항목", "값"]))

    # 저장 버튼
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

        # CSV 저장
        saved_df = pd.DataFrame(st.session_state["saved"])
        if os.path.exists(SAVE_PATH):
            existing = pd.read_csv(SAVE_PATH)
            saved_df = pd.concat([existing, saved_df], ignore_index=True).drop_duplicates()
        saved_df.to_csv(SAVE_PATH, index=False)

else:
    st.warning("⚠ 해당 조건에 맞는 음식이 없습니다.")

# 저장된 식단 표시 및 삭제 기능
if "saved" in st.session_state and st.session_state["saved"]:
    st.markdown("---")
    st.subheader("저장된 식단")

    saved_df = pd.DataFrame(st.session_state["saved"])

    # 삭제 버튼 눌렀을 때 인덱스 기록
    for idx, row in saved_df.iterrows():
        col1, col2 = st.columns([5, 1])
        with col1:
            st.write(f"{row['대표명']} | 열량: {row['열량']} kcal | 탄: {row['탄수화물']}g, 단: {row['단백질']}g, 지: {row['지방']}g")
        with col2:
            if st.button("목록에서 삭제", key=f"delete_{idx}"):
                st.session_state["delete_index"] = idx

    # 삭제 처리
    if "delete_index" in st.session_state:
        idx_to_delete = st.session_state.pop("delete_index")
        if idx_to_delete < len(st.session_state["saved"]):
            st.session_state["saved"].pop(idx_to_delete)

    # 총 영양 성분 합계
    st.subheader("총 영양 성분")
    total_nutrients = saved_df[["열량", "탄수화물", "단백질", "지방"]].sum()
    st.write(total_nutrients)

    # 그래프로 성분 시각화
    st.subheader("총 섭취 탄/단/지 그래프")
    labels = ["탄수화물", "단백질", "지방"]
    values = [total_nutrients["탄수화물"], total_nutrients["단백질"], total_nutrients["지방"]]

    fig, ax = plt.subplots()
    ax.bar(labels, values, color=["skyblue", "green", "pink"])
    ax.set_ylabel("g")
    st.pyplot(fig)

    # 한끼 저장 기능
    st.markdown("---")
    st.subheader("한끼로 저장")
    if st.button("한끼 저장하기"):
        meal_df = pd.DataFrame(st.session_state["saved"])
        meal_df["저장일시"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        meal_df["한끼ID"] = datetime.datetime.now().strftime("%Y%m%d%H%M%S")

        if os.path.exists(MEAL_LOG_PATH):
            existing = pd.read_csv(MEAL_LOG_PATH)
            meal_df = pd.concat([existing, meal_df], ignore_index=True)

        meal_df.to_csv(MEAL_LOG_PATH, index=False)
        st.success("한끼 저장 완료!")

        # 저장 목록 초기화
        st.session_state["saved"] = []
