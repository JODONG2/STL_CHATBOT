# agent_flow.py
"""
LangGraph 기반 AI Agent 논리 흐름 및 상태 관리
"""

from typing import TypedDict, List, Any
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.checkpoint.memory import InMemorySaver
from langchain_openai import AzureChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.prebuilt import create_react_agent
from langchain_core.tools import tool
from rag_utils import get_legal_retriever, get_settlement_retriever, get_retriever
from config import AZURE_OPENAI_CHAT_MODEL, LegalAgentState

# 1. State 정의 (MessagesState + RAG 검색 결과)
class LegalAgentState(MessagesState):
    rag_docs: List[Any]  # RAG 검색 결과(참조 문서)
    remaining_steps: int  # ReAct Agent 필수 필드
    input: str  # ChatPromptTemplate 필수 입력

# 2. RAG Tool 정의 (리트리버 래핑)
@tool
def search_law(query: str) -> str:
    """
    법률 질문에 대해 관련 법률 조항을 검색합니다.
    """
    retriever = get_legal_retriever()
    docs = retriever.invoke(query)
    # 간단 요약(실제 서비스에서는 더 정교하게)
    if not docs:
        return "관련 법률 조항을 찾지 못했습니다."
    result = "\n\n".join([f"[출처: {d.metadata.get('title', '')} - {d.metadata.get('source', '')}]\n{d.page_content[:500]}..." for d in docs])
    return result

@tool
def search_settlement_info(query: str) -> str:
    """
    정산 관련 질문에 대해 관련 업무 지식을 검색합니다.
    """
    retriever = get_settlement_retriever()
    docs = retriever.invoke(query)
    # 간단 요약(실제 서비스에서는 더 정교하게)
    if not docs:
        return "관련 정산 업무 정보를 찾지 못했습니다."
    result = "\n\n".join([f"[출처: {d.metadata.get('title', '')} - {d.metadata.get('source', '')}]\n{d.page_content[:500]}..." for d in docs])
    return result

# 3. 프롬프트 템플릿 (역할/사고과정/법률적 인용)
legal_system_prompt = (
    "당신은 전문적이고 신뢰할 수 있는 AI 법률 상담사입니다.\n"
    "사용자의 법률 질문에 대해 관련 법률 조항을 바탕으로 정확하고 이해하기 쉬운 답변을 제공합니다.\n"
    "답변은 법률적 근거(예: 개인정보 보호법 제XX조)를 명확히 인용하며, 필요한 경우 최신 판례나 해석을 덧붙입니다.\n"
    "모호하거나 불확실한 정보는 제공하지 않으며, 정보가 부족하다면 추가 질문을 요청하세요.\n"
    "\n"
    "사고 과정:\n"
    "1. 사용자의 질문을 분석하여 핵심 쟁점을 파악하세요.\n"
    "2. RAG Tool을 통해 관련 법률 조항을 검색하세요.\n"
    "3. 검색된 정보를 바탕으로 논리적 흐름을 구성하고, 필요한 법률 조항을 명확히 인용하며 답변을 생성하세요.\n"
    "4. 답변 후, 사용자가 더 궁금해할 만한 추가 질문을 제안하세요."
)

settlement_system_prompt = (
    "당신은 전문적이고 신뢰할 수 있는 AI 정산 업무 전문가입니다.\n"
    "사용자의 정산 관련 질문에 대해 관련 업무 지식을 바탕으로 정확하고 이해하기 쉬운 답변을 제공합니다.\n"
    "답변은 정산 업무의 근거와 절차를 명확히 설명하며, 필요한 경우 관련 문서나 가이드를 인용합니다.\n"
    "모호하거나 불확실한 정보는 제공하지 않으며, 정보가 부족하다면 추가 질문을 요청하세요.\n"
    "\n"
    "사고 과정:\n"
    "1. 사용자의 질문을 분석하여 핵심 쟁점을 파악하세요.\n"
    "2. RAG Tool을 통해 관련 정산 업무 정보를 검색하세요.\n"
    "3. 검색된 정보를 바탕으로 논리적 흐름을 구성하고, 필요한 업무 절차나 가이드를 명확히 인용하며 답변을 생성하세요.\n"
    "4. 답변 후, 사용자가 더 궁금해할 만한 추가 질문을 제안하세요.\n"
    "또한, 최종 답변의 마지막에 아래 형식으로 반드시 출처를 포함하세요.\n"
    "[출처: {{문서제목}} - {{source 또는 URL}}] 여러 개일 경우 줄바꿈으로 나열."
)

# 4. LLM/Tool Agent 생성 (ReAct)
llm = AzureChatOpenAI(model=AZURE_OPENAI_CHAT_MODEL, temperature=0)

# 법률 상담용 에이전트
legal_tools = [search_law]
legal_prompt = ChatPromptTemplate.from_messages([
    ("system", legal_system_prompt),
    MessagesPlaceholder(variable_name="messages"),
    ("human", "{input}")
])
legal_agent = create_react_agent(llm, legal_tools, prompt=legal_prompt, state_schema=LegalAgentState)

# 정산 업무용 에이전트
settlement_tools = [search_settlement_info]
settlement_prompt = ChatPromptTemplate.from_messages([
    ("system", settlement_system_prompt),
    MessagesPlaceholder(variable_name="messages"),
    ("human", "{input}")
])
settlement_agent = create_react_agent(llm, settlement_tools, prompt=settlement_prompt, state_schema=LegalAgentState)

# 5. StateGraph 설계 (질문→RAG검색→답변생성)
def create_legal_graph():
    """법률 상담용 그래프 생성"""
    builder = StateGraph(LegalAgentState)
    builder.add_node("agent", legal_agent)
    builder.add_edge(START, "agent")
    builder.add_edge("agent", END)
    return builder.compile(checkpointer=InMemorySaver())

def create_settlement_graph():
    """정산 업무용 그래프 생성"""
    builder = StateGraph(LegalAgentState)
    builder.add_node("agent", settlement_agent)
    builder.add_edge(START, "agent")
    builder.add_edge("agent", END)
    return builder.compile(checkpointer=InMemorySaver())

# 6. 외부에서 사용할 수 있도록 graph 객체 export
def get_legal_agent_graph():
    return create_legal_graph()

def get_settlement_agent_graph():
    return create_settlement_graph() 