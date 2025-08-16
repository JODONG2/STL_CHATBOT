# LegalTech AI 법률 상담사 프로젝트

## 1. 과제 개요 - 프로젝트 기획 배경 및 핵심 내용

### 프로젝트를 기획한 이유

현대 사회에서 법률 정보에 대한 접근성은 매우 중요하지만, 일반인이 신뢰할 수 있는 법률 상담을 받기에는 시간적·경제적 제약이 큽니다. 본 프로젝트는 최신 AI 기술을 활용하여 누구나 쉽고 빠르게 법률 정보를 얻을 수 있는 서비스를 제공하고자 기획되었습니다.

### 해결하고자 하는 문제

- 법률 문서(법령, 판례 등)의 방대한 양과 복잡성으로 인해 비전문가가 필요한 정보를 찾기 어려움
- 기존 법률 상담 서비스의 높은 비용과 접근성 한계
- 최신 법률 정보 및 판례 반영의 어려움

### AI Agent의 핵심 기능

- 사용자의 질문을 받아 LangGraph 기반 상태 관리(StateGraph)로 대화 흐름을 제어
- 법률 PDF 문서에서 텍스트를 추출·청킹하고, Azure OpenAI 임베딩을 통해 ChromaDB 벡터스토어에 저장
- RAG Tool(search_law)을 통해 사용자의 질문과 유사한 법률 조항/판례를 벡터DB에서 검색
- 검색된 법률 조항을 답변에 명확히 인용하여 신뢰성 있는 결과 제공
- 전문 법률 상담사 프롬프트와 Tool Agent(create_react_agent)로 논리적·근거 중심의 답변 생성
- Streamlit UI와 연동하여 대화 기록, 참조 문서, 진행상태 등 실시간 피드백 제공

### 기대하는 사용자 경험 및 주요 특징

- 누구나 쉽고 빠르게 법률 상담 가능 (24/7)
- 답변마다 관련 법률 조항/출처를 명확히 인용하여 신뢰성 제공
- 최신 법률 PDF 파일을 손쉽게 갱신/추가 가능
- 대화 기록, 참조 문서, 토큰 사용량 등 실전 서비스 수준의 운영/관리 기능

---

## 2. 기술 구성 - 프로젝트에 포함된 주요 기술 스택

### 1) Prompt Engineering

- 전문 법률 상담사 역할, 사고과정, 인용 방식 등 프롬프트 설계
- 사용자의 질문을 분석하고, RAG Tool을 통해 관련 법률 조항을 검색하도록 유도
- 답변 생성 시 법률적 근거(조문, 판례 등) 명확히 인용

### 2) Azure OpenAI 활용

- Azure OpenAI의 GPT-4/3.5 등 LLM API를 활용한 자연어 이해 및 생성
- Azure OpenAI Embedding API로 법률 문서 임베딩 및 벡터화
- API Key, Endpoint, Model Name 등 환경변수 기반 안전한 연동

### 3) RAG (Retrieval-Augmented Generation)

- PyPDFLoader, PyMuPDFLoader로 PDF 텍스트 추출 및 청킹
- Azure OpenAI 임베딩 → ChromaDB 벡터스토어 저장/검색
- 유사도 기반 리트리버(get_retriever)로 관련 법률 조항 검색
- RAG Tool을 통해 LLM 답변 생성 시 근거 문서 자동 인용

### 4) Streamlit 및 서비스 개발/패키징

- Streamlit 기반 대화형 챗봇 UI 구현 (st.chat_input, st.chat_message 등)
- 대화 기록, 참조 문서, 진행상태 표시, sidebar 정보 등 UX 고도화
- @st.cache_resource로 에이전트 그래프 캐싱, 운영 효율화
- requirements.txt, .env, 모듈화된 코드 구조로 실전 서비스 배포/운영 용이

---

## 6. 추가 구현 사항 및 개선 아이디어 (선택)

과제를 수행하며 향후 추가로 구현해 보고 싶은 내용, 개선 아이디어를 아래와 같이 제안합니다.

- **유저별 맞춤 데이터 저장 및 개인화**
  - 사용자별 상담 이력, 즐겨찾기, 맞춤형 법률 정보 제공
  - 예시: ![유저별 대시보드 예시](https://user-images.githubusercontent.com/your-dashboard-example.png)

- **실시간 법률/판례 데이터 연동**
  - 최신 법률 개정, 판례, 뉴스 등 외부 데이터 API 실시간 연동
  - 예시: ![실시간 법률 데이터 연동](https://user-images.githubusercontent.com/your-law-api-example.png)

- **AI 성능 최적화 및 피드백 루프**
  - 사용자 피드백 기반 답변 품질 개선, 토큰/비용 최적화, 프롬프트 튜닝

- **이미지/영상 등 멀티모달 입력 지원**
  - 계약서, 판결문 등 이미지 업로드 → OCR/LLM 분석
  - 법률 관련 동영상(예: 판례 해설) 첨부 및 요약
  - 예시: ![이미지 업로드 예시](https://user-images.githubusercontent.com/your-image-upload-example.png)

- **모바일/앱 서비스 확장**
  - 모바일 웹/앱, 카카오톡 챗봇 등 다양한 채널로 서비스 확장

- **보안 및 개인정보 보호 강화**
  - 민감 정보 마스킹, 접근 권한 관리, 데이터 암호화 등

- **운영/모니터링/로깅 고도화**
  - 대시보드, 토큰 사용량/비용 모니터링, 에러/사용자 행동 로깅

- **다국어/글로벌 서비스 확장**
  - 영어, 중국어 등 다국어 법률 상담 지원

---

## 7. 프로젝트 피드백 및 한 줄 소감

### 한 줄 소감

- 이번 프로젝트를 통해 RAG, LangGraph Agent, Azure OpenAI 등 최신 AI 기술을 처음 접해보았고, 실제 서비스 수준의 챗봇을 직접 구현해보며 AI 서비스의 구조와 동작 원리를 깊이 이해할 수 있었습니다.
- 처음에는 생소하고 어렵게 느껴졌지만, 단계별로 직접 구현하고 실습하면서 AI가 어떻게 외부 지식(RAG)과 결합해 더 신뢰성 있는 답변을 만드는지 체감할 수 있었습니다.
- 실제 법률 PDF를 다루고, 프롬프트 엔지니어링, 벡터DB, 상태관리 등 다양한 기술이 유기적으로 연결되는 경험이 매우 인상적이었습니다.

### 피드백 및 요청

- RAG, Agent, LangGraph 등 핵심 개념에 대한 시각적 다이어그램/예시 코드가 더 많았으면 이해에 도움이 될 것 같습니다.
- 실습 단계별로 예상 결과 화면, 주요 에러/트러블슈팅 팁이 함께 제공되면 초심자에게 더 친절할 것 같습니다.
- 실제 서비스 배포(예: Azure, AWS, Docker 등)와 관련된 실전 가이드가 추가된다면 더욱 실용적일 것 같습니다.
- 다양한 도메인(법률 외 의료, 교육 등)으로 확장하는 예시도 있으면 좋겠습니다.

---

## Confluence 크롤러 사용법

### 1. 환경 설정

FIDO 인증이 필요한 Confluence 환경에서는 세션 쿠키를 사용해야 합니다.

#### 1-1. 세션 쿠키 획득 방법

1. 브라우저에서 Confluence에 FIDO 인증으로 로그인
2. 개발자 도구(F12) → Application/Storage → Cookies → confluence.tde.sktelecom.com
3. 다음 쿠키 값들을 복사:
   - `ajs_anonymous_id`
   - `ajs_user_id`
   - `CONF-SESSIONID`
   - `JSESSIONID`

#### 1-2. .env 파일 설정

```env
# Confluence 세션 쿠키 (FIDO 인증 후 브라우저에서 복사)
AJS_ANONYMOUS_ID=your_ajs_anonymous_id_here
AJS_USER_ID=your_ajs_user_id_here
CONF_SESSIONID=your_conf_sessionid_here
JSESSIONID=your_jsessionid_here
```

### 2. 의존성 설치

```bash
pip install -r requirements.txt
```

### 3. 크롤링 실행

```bash
python get_confl.py
```

### 4. 주요 기능

- **FIDO 인증 지원**: 세션 쿠키를 통한 인증으로 FIDO 환경에서도 작동
- **요청 제한 관리**: 초당 5회 제한을 고려하여 2번 요청 후 1초 대기
- **재귀적 크롤링**: 지정된 페이지와 모든 하위 페이지를 자동으로 크롤링
- **JSON 저장**: 크롤링한 데이터를 `confluence_data.json` 파일로 저장
- **로깅**: 진행 상황과 오류를 상세히 로깅

### 5. 출력 파일

크롤링이 완료되면 `confluence_data.json` 파일이 생성되며, 다음과 같은 구조로 데이터가 저장됩니다:

```json
{
  "id": "페이지ID",
  "title": "페이지 제목",
  "type": "page",
  "status": "current",
  "version": {
    "number": 1,
    "message": "버전 메시지",
    "minorEdit": false
  },
  "body": {
    "storage": {
      "value": "페이지 내용 (HTML)",
      "representation": "storage"
    }
  },
  "children": [
    // 하위 페이지들...
  ],
  "created": "생성일시",
  "lastModified": "수정일시",
  "url": "페이지 URL"
}
```

### 6. 주의사항

- **세션 쿠키 유효성**: 세션 쿠키는 일정 시간 후 만료되므로 주기적으로 갱신 필요
- **권한 확인**: 해당 페이지에 접근 권한이 있는 계정으로 로그인해야 함
- **대용량 문서**: 대용량 문서의 경우 크롤링 시간이 오래 걸릴 수 있음
- **API 요청 제한**: API 요청 제한으로 인해 적절한 대기 시간이 자동으로 적용됨 