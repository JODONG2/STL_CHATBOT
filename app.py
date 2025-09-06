import streamlit as st
import uuid
from config import AZURE_OPENAI_CHAT_MODEL
from agent_flow import get_legal_agent_graph, get_settlement_agent_graph

st.set_page_config(page_title="AI 법률 상담사 & 정산 전문가", layout="wide")
st.title("AI 법률 상담사 & 정산 전문가")

st.sidebar.header("설정")
st.sidebar.write(f"사용 모델: {AZURE_OPENAI_CHAT_MODEL}")

# 질문 유형 선택
question_type = st.sidebar.selectbox(
    "질문 유형 선택",
    ["법률 상담", "정산 업무"],
    help="질문의 유형을 선택하세요"
)

# 1. 에이전트 그래프 캐싱 (초기화 비용 절감)
@st.cache_resource
def load_legal_agent():
    return get_legal_agent_graph()

@st.cache_resource
def load_settlement_agent():
    return get_settlement_agent_graph()

# 선택된 유형에 따라 에이전트 로드
if question_type == "법률 상담":
    graph = load_legal_agent()
    st.sidebar.success("법률 상담 모드")
else:
    graph = load_settlement_agent()
    st.sidebar.success("정산 업무 모드")

# 2. 세션 상태 초기화 (대화 기록, 참조 문서)
if "messages" not in st.session_state:
    st.session_state["messages"] = []  # {"role": "user"|"ai", "content": str}
if "docs" not in st.session_state:
    st.session_state["docs"] = []      # 최근 참조 문서(법률 조항 등)
if "thread_id" not in st.session_state:
    st.session_state["thread_id"] = str(uuid.uuid4())

# 3. 기존 대화 메시지 출력
for msg in st.session_state["messages"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        # AI 답변에 참조 문서가 있으면 expander로 표시
        if msg["role"] == "ai" and msg.get("refs"):
            with st.expander("참조 문서/출처 보기"):
                for ref in msg["refs"]:
                    st.markdown(ref)

# 4. 사용자 입력 받기
if question_type == "법률 상담":
    placeholder_text = "법률 질문을 입력하세요 (예: 개인정보 유출시 책임은?)"
else:
    placeholder_text = "정산 관련 질문을 입력하세요 (예: 쿠폰 정산 절차는?)"

if prompt := st.chat_input(placeholder_text):
    # 사용자 메시지 추가
    st.session_state["messages"].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # AI 답변 생성
    with st.chat_message("ai"):
        with st.spinner(f"{question_type} 정보 검색 및 답변 생성 중..."):
            # LangGraph agent 호출 (대화 기록 전달)
            # messages: [{"role": "user"|"ai", "content": ...}]
            input_state = {
                "messages": st.session_state["messages"],
                "input": prompt  # ← 반드시 추가!
            }
            result = graph.invoke(input_state, config={"thread_id": st.session_state["thread_id"]})
            ai_msg = result["messages"][-1].content if result["messages"] else "답변 생성 실패"
            # 참조 문서(법률 조항) 추출: search_law tool의 결과가 답변 내에 포함됨
            refs = []
            if "[출처:" in ai_msg:
                # 여러 개일 수 있으므로 분리
                refs = [chunk for chunk in ai_msg.split("[출처:") if chunk.strip()]
                refs = ["[출처:" + r for r in refs]
            st.markdown(ai_msg)
            if refs:
                with st.expander("참조 문서/출처 보기"):
                    for ref in refs:
                        st.markdown(ref)
            # 대화 기록/참조 문서 세션에 저장
            st.session_state["messages"].append({"role": "ai", "content": ai_msg, "refs": refs}) 