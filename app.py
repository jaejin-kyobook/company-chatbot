import streamlit as st
import pandas as pd
import gspread
from google import genai
from google.oauth2.service_account import Credentials
from datetime import datetime

# ── Google Sheets 연결 ────────────────────────────────────────────────────────
@st.cache_resource
def get_sheet():
    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets"]
        creds = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"], scopes=scopes
        )
        gc = gspread.authorize(creds)
        sh = gc.open_by_url(st.secrets["sheets"]["url"])
        worksheet = sh.sheet1
        # 헤더가 없으면 추가
        if worksheet.row_count == 0 or worksheet.cell(1, 1).value != "번호":
            worksheet.append_row(["번호", "질문", "매칭여부", "카테고리", "일시"])
        return worksheet
    except Exception as e:
        return None

def log_question(question: str, matched: bool, category: str):
    try:
        ws = get_sheet()
        if ws is None:
            return
        rows = ws.get_all_values()
        no = len(rows)  # 헤더 포함
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ws.append_row([no, question, "✅ 매칭" if matched else "❌ 미매칭", category, now])
    except Exception:
        pass

# ── 페이지 설정 ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="스마트 사내 지원 챗봇",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={}
)

# ── 카카오톡 스타일 CSS ───────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700&display=swap');
    * { font-family: 'Noto Sans KR', sans-serif !important; }

    /* 툴바/메뉴 숨기기 */
    #MainMenu { display: none !important; }
    footer { display: none !important; }
    [data-testid="stToolbar"] { display: none !important; }

    /* ── 전체 배경 (카카오 채팅방 배경색) ── */
    .stApp { background-color: #b2c7d9 !important; }
    .block-container { padding: 1rem 2rem 5rem 2rem !important; max-width: 780px !important; }

    /* ── 상단 채팅방 헤더 느낌 ── */
    h1 {
        color: #1a1a1a !important;
        font-size: 1.1rem !important;
        font-weight: 700 !important;
        text-align: center;
        background: #9ab0c4;
        padding: 12px !important;
        border-radius: 0 !important;
        margin: -1rem -2rem 1rem -2rem !important;
    }

    /* ── 사이드바 ── */
    [data-testid="stSidebar"] {
        background: #f9f9f9 !important;
        border-right: 1px solid #e0e0e0 !important;
    }
    [data-testid="stSidebar"] * { color: #333333 !important; }
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 { color: #111111 !important; font-size: 14px !important; }

    /* ── 사이드바 버튼 ── */
    [data-testid="stSidebar"] .stButton button {
        background: #ffffff !important;
        border: 1px solid #e0e0e0 !important;
        color: #333 !important;
        border-radius: 8px !important;
        font-size: 12px !important;
        text-align: left !important;
        transition: all 0.15s ease !important;
    }
    [data-testid="stSidebar"] .stButton button:hover {
        background: #FFF9C4 !important;
        border-color: #FAE100 !important;
        color: #111 !important;
    }

    /* ── 봇 말풍선 (흰색, 왼쪽) ── */
    [data-testid="stChatMessage"] {
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        padding: 4px 0 !important;
        margin-bottom: 4px !important;
    }
    [data-testid="stChatMessageContent"] {
        background: #ffffff !important;
        border-radius: 0px 12px 12px 12px !important;
        padding: 10px 14px !important;
        box-shadow: 0 1px 2px rgba(0,0,0,0.12) !important;
        max-width: 75% !important;
        display: inline-block !important;
    }
    [data-testid="stChatMessage"] p,
    [data-testid="stChatMessage"] li { color: #1a1a1a !important; font-size: 14px !important; line-height: 1.6 !important; }
    [data-testid="stChatMessage"] strong { color: #3c1e1e !important; }
    [data-testid="stChatMessage"] blockquote {
        border-left: 3px solid #FAE100 !important;
        background: #fffde7 !important;
        border-radius: 0 6px 6px 0 !important;
        padding: 6px 10px !important;
        margin: 6px 0 !important;
    }
    [data-testid="stChatMessage"] blockquote p { color: #555 !important; font-size: 13px !important; }
    [data-testid="stChatMessage"] th {
        background: #FFF9C4 !important;
        color: #333 !important;
        padding: 5px 10px !important;
        border: 1px solid #e0e0e0 !important;
        font-size: 13px !important;
    }
    [data-testid="stChatMessage"] td {
        padding: 5px 10px !important;
        border: 1px solid #e0e0e0 !important;
        font-size: 13px !important;
        color: #333 !important;
    }

    /* ── 채팅 입력창 (카카오 스타일) ── */
    [data-testid="stChatInput"] {
        background: #ffffff !important;
        border: 1.5px solid #d0d0d0 !important;
        border-radius: 22px !important;
        box-shadow: 0 1px 4px rgba(0,0,0,0.08) !important;
    }
    [data-testid="stChatInput"]:focus-within {
        border-color: #FAE100 !important;
        box-shadow: 0 0 0 2px rgba(250,225,0,0.25) !important;
    }
    [data-testid="stChatInput"] textarea { color: #1a1a1a !important; font-size: 14px !important; }

    /* ── 카테고리 태그 ── */
    .cat-tag {
        display: inline-block;
        background: #FAE100;
        color: #3c1e1e;
        border-radius: 20px;
        padding: 2px 12px;
        font-size: 12px;
        font-weight: 700;
    }

    /* ── 서브타이틀 ── */
    .subtitle { color: #4a4a4a; font-size: 13px; margin-bottom: 0.8rem; text-align: center; }

    /* ── 구분선 ── */
    hr { border-color: rgba(0,0,0,0.1) !important; margin: 8px 0 !important; }

    /* ── 스크롤바 ── */
    ::-webkit-scrollbar { width: 4px; }
    ::-webkit-scrollbar-track { background: #b2c7d9; }
    ::-webkit-scrollbar-thumb { background: rgba(0,0,0,0.2); border-radius: 2px; }
</style>
""", unsafe_allow_html=True)

# ── 엑셀 데이터 로드 ──────────────────────────────────────────────────────────
EXCEL_PATH = "FAQ 데이터.xlsx"

@st.cache_data
def load_faq():
    try:
        df = pd.read_excel(EXCEL_PATH)
        df.columns = ["No", "카테고리", "키워드", "질문", "답변", "담당부서"]
        df = df[df["질문"].notna()].reset_index(drop=True)
        df["카테고리"] = df["카테고리"].ffill()
        df["키워드"] = df["키워드"].fillna("")
        df["답변"] = df["답변"].fillna("")
        df["담당부서"] = df["담당부서"].fillna("")
        return df
    except Exception as e:
        st.error(f"❌ 엑셀 파일을 불러오지 못했습니다: {e}")
        return pd.DataFrame(columns=["No", "카테고리", "키워드", "질문", "답변", "담당부서"])

df_faq = load_faq()
categories = ["전체"] + sorted(df_faq["카테고리"].dropna().unique().tolist())

# ── 검색 로직 ─────────────────────────────────────────────────────────────────
def find_answer(query: str, category: str) -> str:
    query_lower = query.lower().strip()
    pool = df_faq if category == "전체" else df_faq[df_faq["카테고리"] == category]

    best_row, best_score = None, 0
    for _, row in pool.iterrows():
        score = 0
        keywords = [k.strip().lower() for k in str(row["키워드"]).replace("\n", ",").split(",") if k.strip()]
        score += sum(2 for kw in keywords if kw and kw in query_lower)
        q_words = str(row["질문"]).lower().split()
        score += sum(1 for w in q_words if len(w) > 1 and w in query_lower)
        if score > best_score:
            best_score, best_row = score, row

    if best_row is not None and best_score >= 2:
        answer = best_row["답변"]
        dept = best_row["담당부서"]
        log_question(query, True, category)
        if answer and str(answer).strip():
            result = f"**📋 {best_row['질문']}**\n\n{answer}"
            if dept:
                result += f"\n\n> 📌 담당부서: **{dept}**"
            return result
        else:
            dept_msg = f" ({dept})" if dept else ""
            return (
                f"**📋 {best_row['질문']}**\n\n"
                f"해당 질문에 대한 답변을 준비 중입니다.\n\n"
                f"> 📞 담당부서{dept_msg}로 직접 문의해 주세요."
            )

    log_question(query, False, category)
    return get_gemini_answer(query)

def get_gemini_answer(query: str) -> str:
    try:
        client = genai.Client(api_key=st.secrets["gemini"]["api_key"])
        prompt = (
            f"당신은 친절한 사내 지원 챗봇입니다. "
            f"사내 FAQ에 없는 질문이 들어왔습니다. "
            f"일반적인 지식을 바탕으로 친절하고 간결하게 한국어로 답변해 주세요. "
            f"답변 마지막에 '더 정확한 안내가 필요하시면 담당 부서에 문의해 주세요.' 라고 덧붙여 주세요.\n\n"
            f"질문: {query}"
        )
        response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
        return f"💡 **AI 답변**\n\n{response.text}"
    except Exception as e:
        return (
            "죄송해요, 등록된 답변을 찾지 못했어요. 😢\n\n"
            "**담당 부서로 문의해 주세요:**\n"
            "- 총무팀 내선 **202**\n"
            "- 인사팀 내선 **101**\n"
            "- IT팀 내선 **303**"
        )

# ── 세션 상태 초기화 ──────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": (
                "안녕하세요! 👋 **스마트 사내 지원 챗봇**입니다.\n\n"
                "궁금한 내용을 아래 입력창에 입력해 주세요.\n"
                "왼쪽 사이드바에서 카테고리를 선택하면 더 정확한 답변을 드릴 수 있어요! 😊"
            ),
        }
    ]

# ── 사이드바 ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🏢 사내 지원 챗봇")
    st.markdown("---")

    st.markdown("**📂 카테고리**")
    category = st.selectbox("", options=categories, label_visibility="collapsed")

    st.markdown("---")
    st.markdown("**💡 자주 찾는 질문**")

    quick_pool = df_faq if category == "전체" else df_faq[df_faq["카테고리"] == category]
    for _, row in quick_pool.head(6).iterrows():
        q = str(row["질문"])
        short_q = q[:22] + "..." if len(q) > 22 else q
        if st.button(f"  {short_q}", key=f"quick_{row['No']}", use_container_width=True):
            st.session_state.messages.append({"role": "user", "content": q})
            st.session_state.messages.append({"role": "assistant", "content": find_answer(q, category)})
            st.rerun()

    st.markdown("---")
    if st.button("🗑️ 대화 초기화", use_container_width=True):
        st.session_state.messages = [
            {"role": "assistant", "content": "대화가 초기화되었습니다. 무엇이든 물어보세요! 😊"}
        ]
        st.rerun()

    st.markdown("---")
    total = len(df_faq)
    done = int((df_faq["답변"] != "").sum())
    st.markdown(
        f"""<div style='background:rgba(99,179,237,0.08);border:1px solid rgba(99,179,237,0.2);
        border-radius:10px;padding:12px;margin-top:4px;'>
        <div style='color:#90cdf4;font-size:12px;font-weight:600;margin-bottom:6px;'>📊 FAQ 현황</div>
        <div style='color:#cbd5e0;font-size:12px;'>등록 질문: <b style='color:#63b3ed'>{total}건</b></div>
        <div style='color:#cbd5e0;font-size:12px;margin-top:4px;'>답변 완료: <b style='color:#68d391'>{done}건</b></div>
        </div>""",
        unsafe_allow_html=True,
    )

# ── 말풍선 렌더 함수 ──────────────────────────────────────────────────────────
import re

def render_bubble(role: str, content: str):
    # 마크다운 간단 변환
    content_html = content
    content_html = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', content_html)
    content_html = re.sub(r'\n', '<br>', content_html)
    content_html = re.sub(r'> (.+?)(<br>|$)', r'<div style="border-left:3px solid #FAE100;background:#fffde7;padding:6px 10px;border-radius:0 6px 6px 0;margin:4px 0;font-size:13px;color:#555;">\1</div>', content_html)
    content_html = re.sub(r'- (.+?)(<br>|$)', r'• \1<br>', content_html)

    if role == "assistant":
        st.markdown(f"""
        <div style="display:flex;align-items:flex-start;margin:8px 0;justify-content:flex-start;">
            <div style="font-size:28px;margin-right:8px;margin-top:2px;">🤖</div>
            <div>
                <div style="font-size:11px;color:#555;margin-bottom:3px;">사내 지원 챗봇</div>
                <div style="background:#ffffff;border-radius:0 14px 14px 14px;padding:10px 14px;
                            max-width:480px;box-shadow:0 1px 3px rgba(0,0,0,0.12);
                            font-size:14px;color:#1a1a1a;line-height:1.7;display:inline-block;">
                    {content_html}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style="display:flex;align-items:flex-start;margin:8px 0;justify-content:flex-end;">
            <div style="text-align:right;">
                <div style="background:#FAE100;border-radius:14px 0 14px 14px;padding:10px 14px;
                            max-width:480px;box-shadow:0 1px 3px rgba(0,0,0,0.12);
                            font-size:14px;color:#1a1a1a;line-height:1.7;display:inline-block;text-align:left;">
                    {content_html}
                </div>
            </div>
            <div style="font-size:28px;margin-left:8px;margin-top:2px;">🙋</div>
        </div>
        """, unsafe_allow_html=True)


# ── 메인 화면 ─────────────────────────────────────────────────────────────────
st.title("🏢 스마트 사내 지원 챗봇")
st.markdown(
    f"<div class='subtitle'>카테고리: <span class='cat-tag'>📂 {category}</span> &nbsp;·&nbsp; 무엇이든 질문해 보세요</div>",
    unsafe_allow_html=True,
)

# 대화 기록 렌더링
for msg in st.session_state.messages:
    render_bubble(msg["role"], msg["content"])

# 사용자 입력
if prompt := st.chat_input("💬  질문을 입력하세요  (예: 출입카드 문제, 명함 발급)"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    render_bubble("user", prompt)

    answer = find_answer(prompt, category)
    st.session_state.messages.append({"role": "assistant", "content": answer})
    render_bubble("assistant", answer)
