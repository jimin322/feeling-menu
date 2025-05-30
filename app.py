import streamlit as st
import google.generativeai as genai
from datetime import datetime
import json

# 페이지 설정
st.set_page_config(
    page_title="🍜 기분의 한 끼 메뉴판",
    page_icon="🍜",
    layout="centered"
)

# CSS 스타일 적용
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    }
    .stButton > button {
        border-radius: 20px;
        padding: 10px 24px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        width: 100%;
    }
    .stSelectbox {
        border-radius: 15px;
    }
    div[data-testid="stMarkdownContainer"] > h1 {
        color: #1e1e1e;
        text-align: center;
        font-weight: 800;
    }
    .mood-card {
        background: white;
        padding: 2rem;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin: 1rem 0;
    }
    .result-card {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        border-left: 5px solid #667eea;
    }
    .menu-image {
        border-radius: 10px;
        width: 100%;
        margin: 1rem 0;
    }
    .comment {
        font-style: italic;
        color: #4a4a4a;
        text-align: center;
        padding: 1rem;
        background: #f8f9fa;
        border-radius: 10px;
        margin: 1rem 0;
    }
    .info-grid {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 1rem;
        margin-bottom: 1.5rem;
    }
    .info-item {
        background: #f8f9fa;
        padding: 0.8rem;
        border-radius: 8px;
        text-align: center;
    }
    .info-label {
        font-size: 0.8rem;
        color: #666;
        margin-bottom: 0.3rem;
    }
    .info-value {
        font-size: 1rem;
        color: #1e1e1e;
        font-weight: 500;
    }
    .menu-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 10px;
        text-align: center;
        margin: 1.5rem 0;
    }
    .place-tag {
        display: inline-block;
        background: rgba(255, 255, 255, 0.2);
        padding: 0.4rem 1rem;
        border-radius: 20px;
        font-size: 0.9rem;
        margin-top: 0.5rem;
    }
    .comment-box {
        background: white;
        padding: 1.2rem;
        border-radius: 10px;
        margin-top: 1rem;
        text-align: center;
        font-style: italic;
        color: #4a4a4a;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    }
</style>
""", unsafe_allow_html=True)

# 선택지 데이터
MOODS = [
    "😤 스트레스 받는다",
    "😐 무난함",
    "😍 설렌다",
    "😩 피곤하다",
    "😴 나른하다",
    "🥳 신난다",
    "😭 우울하다",
    "😵 멘붕이다"
]

FOOD_TYPES = [
    "🍜 국물 있는 음식",
    "🍝 면 요리",
    "🍚 밥 요리",
    "🥖 빵/디저트",
    "🍖 고기",
    "🦞 해산물",
    "❓ 모르겠음"
]

TIME_SLOTS = [
    "🌅 아침",
    "🌞 점심",
    "🌙 저녁",
    "🌃 야식",
    "🌀 상관없음"
]

BUDGETS = [
    "💸 만 원 내외",
    "💰 2만 원 내외",
    "💳 플렉스!"
]


COMPANIONS = [
    "🧍 혼자",
    "🧑‍🤝‍🧑 친구랑",
    "💑 연인이랑",
    "👨‍👩‍👧 가족이랑",
    "👔 직장 동료랑"
]

AVOID_FOODS = [
    "🦐 해산물",
    "🥩 고기",
    "🍞 밀가루",
    "🧄 자극적인 음식",
    "✅ 없음"
]

# Gemini API 설정
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-1.5-flash')

# 세션 상태 초기화
if 'history' not in st.session_state:
    st.session_state.history = []

def get_menu_recommendation(mood, food_type, time_slot, budget, companion, avoid_foods):
    avoid_foods_text = ", ".join(avoid_foods) if avoid_foods and "✅ 없음" not in avoid_foods else "없음"
    
    prompt = f"""
    당신은 감성 식단 추천 AI입니다.
    아래 조건을 기반으로 메뉴를 추천하고, 정확히 아래 JSON 형식으로만 응답해주세요.
    다른 말은 하지 말고 오직 JSON 형식으로만 응답하세요.

    조건:
    - 기분: {mood}
    - 먹고 싶은 것: {food_type}
    - 식사 시간대: {time_slot}
    - 예산: {budget}
    - 함께 먹는 사람: {companion}
    - 피하고 싶은 음식: {avoid_foods_text}

    응답 형식:
    {{
      "menu": "구체적인 메뉴명을 입력하세요",
      "comment": "기분과 상황에 맞는 재치있는 한 줄 코멘트",
      "place": "추천하는 식당/장소 유형 (예: 포장마차, 프랑스 레스토랑, 동네 맛집 등)"
    }}

    주의사항:
    1. 반드시 위의 JSON 형식으로만 응답하세요
    2. 다른 설명이나 텍스트를 추가하지 마세요
    3. 메뉴는 구체적으로 작성해주세요 (예: "얼큰한 순대국밥 + 김치")
    4. place는 메뉴와 상황에 어울리는 장소를 추천해주세요
    """
    
    try:
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        
        # JSON 시작과 끝 부분 찾기
        start_idx = response_text.find('{')
        end_idx = response_text.rfind('}') + 1
        
        if start_idx != -1 and end_idx != -1:
            json_str = response_text[start_idx:end_idx]
            result = json.loads(json_str)
            
            # 필수 키 확인
            if all(key in result for key in ['menu', 'comment', 'place']):
                return result
        
        # 검증 실패시 기본 응답
        return {
            "menu": "얼큰한 순대국밥 + 김치",
            "comment": "메뉴 추천 중 오류가 발생했어요. 대신 든든한 국밥 한 그릇 어떠세요?",
            "place": "24시간 운영하는 따뜻한 국밥집"
        }
    except Exception as e:
        st.error(f"메뉴 추천 중 오류가 발생했습니다: {str(e)}")
        return {
            "menu": "얼큰한 순대국밥 + 김치",
            "comment": "메뉴 추천 중 오류가 발생했어요. 대신 든든한 국밥 한 그릇 어떠세요?",
            "place": "24시간 운영하는 따뜻한 국밥집"
        }

def main():
    st.title("🍜 기분의 한 끼 메뉴판")
    
    if 'step' not in st.session_state:
        st.session_state.step = 'home'
    
    if st.session_state.step == 'home':
        st.markdown("### 오늘의 기분을 한 끼로 표현해볼까? 🤔")
        if st.button("오늘의 메뉴 뽑기 🎲"):
            st.session_state.step = 'select'
            st.rerun()
    
    elif st.session_state.step == 'select':
        with st.container():
            st.markdown("### 당신의 기분과 취향을 선택해주세요 ✨")
            
            col1, col2 = st.columns(2)
            with col1:
                mood = st.selectbox(
                    "🧠 지금 기분은?",
                    MOODS
                )
                
                food_type = st.selectbox(
                    "🍽 먹고 싶은 건?",
                    FOOD_TYPES
                )
                
                time_slot = st.selectbox(
                    "🕒 식사 시간대는?",
                    TIME_SLOTS
                )
            
            with col2:
                budget = st.selectbox(
                    "💸 예산은?",
                    BUDGETS
                )
                
                companion = st.selectbox(
                    "👥 누구와 함께 먹나요?",
                    COMPANIONS
                )
                
                avoid_foods = st.multiselect(
                    "🚫 피하고 싶은 음식 (여러 개 선택 가능)",
                    AVOID_FOODS
                )
            
            if st.button("메뉴 추천 받기"):
                st.session_state.selections = {
                    'mood': mood,
                    'food_type': food_type,
                    'time_slot': time_slot,
                    'budget': budget,
                    'companion': companion,
                    'avoid_foods': avoid_foods
                }
                st.session_state.step = 'result'
                st.rerun()
    
    elif st.session_state.step == 'result':
        selections = st.session_state.selections
        result = get_menu_recommendation(
            selections['mood'],
            selections['food_type'],
            selections['time_slot'],
            selections['budget'],
            selections['companion'],
            selections['avoid_foods']
        )
        
        with st.container():
            st.markdown("### 🎉 오늘의 추천 메뉴")
            
            # 메뉴 카드 (큰 글씨로 표시)
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                        color: white; 
                        padding: 2rem; 
                        border-radius: 15px; 
                        text-align: center;
                        margin-bottom: 1.5rem;">
                <h2 style="margin: 0; font-size: 2rem; margin-bottom: 1rem;">🍽 {result['menu']}</h2>
                <div style="background: rgba(255,255,255,0.2); 
                            display: inline-block; 
                            padding: 0.5rem 1.5rem; 
                            border-radius: 25px; 
                            font-size: 1.1rem;">
                    📍 {result['place']}
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # 선택 정보를 컬럼으로 표시
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("##### 🧠 기분")
                st.info(selections['mood'])
                st.markdown("##### 🕒 시간대")
                st.info(selections['time_slot'])
            with col2:
                st.markdown("##### 🍽 음식 종류")
                st.info(selections['food_type'])
                st.markdown("##### 💸 예산")
                st.info(selections['budget'])
            
            # 추가 정보를 컬럼으로 표시
            col3, col4 = st.columns(2)
            with col3:
                st.markdown("##### 👥 함께하는 사람")
                st.info(selections['companion'])
            with col4:
                st.markdown("##### 🚫 제외 음식")
                avoid_foods_text = ", ".join(selections['avoid_foods']) if selections['avoid_foods'] else "✅ 없음"
                st.info(avoid_foods_text)
            
            # 코멘트 표시
            st.markdown("---")
            st.markdown(f"""
            <div style="background-color: white;
                        padding: 1.2rem;
                        border-radius: 10px;
                        text-align: center;
                        font-style: italic;
                        color: #4a4a4a;
                        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);">
                💬 {result['comment']}
            </div>
            """, unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("다시 추천받기"):
                    st.rerun()
            with col2:
                if st.button("처음으로"):
                    st.session_state.step = 'home'
                    st.rerun()
        
        # 기록 저장
        if st.button("오늘의 기분 저장하기"):
            st.session_state.history.append({
                'date': datetime.now().strftime("%Y-%m-%d %H:%M"),
                'selections': selections,
                'result': result
            })
            st.success("저장되었습니다! 👍")
        
        # 저장된 기록 표시
        if st.session_state.history:
            st.markdown("### 📝 저장된 기록")
            for record in st.session_state.history:
                st.markdown(f"""
                <div class="mood-card">
                    <p><strong>{record['date']}</strong></p>
                    <p>기분: {record['selections']['mood']}</p>
                    <p>메뉴: {record['result']['menu']}</p>
                    <p class="comment">{record['result']['comment']}</p>
                </div>
                """, unsafe_allow_html=True)

if __name__ == "__main__":
    main() 
