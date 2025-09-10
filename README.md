# STL_CHATBOT

## 개요
- AI 법률 상담 + 정산 업무 지식 챗봇
- 법률(RAG): `legal_docs/*.pdf`
- 정산(RAG): Confluence JSON을 텍스트로 변환한 `stl_docs/txt/*.txt`
- 임베딩: Azure OpenAI Embeddings + Chroma(Vector DB)
- UI: Streamlit (법률/정산 모드 전환)

## 주요 기능
- 법률 상담: 법률 PDF 기반 검색 후 인용 포함 답변
- 정산 업무: Confluence 문서(텍스트 변환본) 기반 검색 후 인용 포함 답변
- 모델/리트리버 최적화: 배치 임베딩, 백오프, 최소 청크 길이 필터, k/임계값 설정
- FIDO 환경 Confluence 크롤링: 브라우저 세션 쿠키로 REST API 접근(2회 요청 후 1초 슬립)

## 디렉터리 구조(핵심)
```
legal_docs/                 # 법률 PDF 자료
stl_docs/
  ├─ confluence_data.json   # 크롤링 산출 JSON (원천)
  ├─ txt/                   # JSON→TXT 변환본(임베딩 대상)
  └─ combined_confluence.txt
chroma_db/
  ├─ legal/                 # 법률 벡터스토어
  └─ settlement/            # 정산 벡터스토어
app.py                      # Streamlit 앱 (모드 선택)
agent_flow.py               # ReAct agent: search_law / search_settlement_info
rag_utils.py                # 로더/청킹/임베딩/벡터스토어/리트리버 유틸
get_confl.py                # Confluence 크롤러(세션 쿠키 기반)
json_to_txt.py              # Confluence JSON → TXT 변환 스크립트
build_vectorstores.py       # 두 벡터스토어 생성 스크립트
config.py                   # 설정/환경변수 로드
```

## 환경 변수(.env)
```env
# Azure OpenAI
AZURE_OPENAI_API_KEY=...
AZURE_OPENAI_ENDPOINT=https://<your-resource>.openai.azure.com/
AZURE_OPENAI_CHAT_MODEL=gpt-4-1106-preview
AZURE_OPENAI_EMBEDDING_MODEL=text-embedding-3-large
OPENAI_API_VERSION=2023-12-01-preview

# Confluence
CONFLUENCE_BASE_URL=https://confluence.tde.sktelecom.com
CONFLUENCE_TARGET_URL=https://confluence.tde.sktelecom.com/spaces/SSPVTWO/pages/223745736
AJS_ANONYMOUS_ID=...
AJS_USER_ID=...
CONF_SESSIONID=...
JSESSIONID=...
```

## 설치
```bash
pip install -r requirements.txt
```

## 데이터 준비
### 1) Confluence 크롤링(get_confl.py)
- 사내 FIDO 인증 → 브라우저 개발자도구 → Cookies에서 아래 값 복사하여 .env 설정
  - `ajs_anonymous_id`, `ajs_user_id`, `CONF-SESSIONID`, `JSESSIONID`
- 속도 제한: 2회 요청 후 1초 대기(초당 5회 제한 대응)
- 실행
```bash
python get_confl.py   # 결과: confluence_data.json
```

### 2) JSON → TXT 변환(json_to_txt.py)
- 코드 블록/메타데이터 보존, 페이지별 텍스트 파일 생성
```bash
python json_to_txt.py \
  -i stl_docs/confluence_data.json \
  -o stl_docs/txt \
  -c stl_docs/combined_confluence.txt \
  --min-chars 200
```

## 벡터스토어 생성(build_vectorstores.py)
- 법률: `legal_docs/*.pdf`
- 정산: `stl_docs/txt/*.txt`
- 임베딩 최적화(코드 반영):
  - chunk_size=2000, chunk_overlap=100
  - 50자 미만 청크 제거
  - 배치 삽입(batch_size=64), 배치 간 sleep=0.3s
  - 실패 시 지수 백오프(최대 3회)
```bash
# 초기화(선택)
rm -rf chroma_db/legal chroma_db/settlement

# 빌드
python build_vectorstores.py
```

## 앱 실행(app.py)
```bash
streamlit run app.py
```
- 사이드바에서 모드 선택
  - 법률 상담: 법률 PDF 기반 RAG
  - 정산 업무: Confluence 텍스트 기반 RAG
- 정산 프롬프트는 답변 말미에 출처 표기를 강제하도록 설정됨

## 캐시 초기화
- UI: 오른쪽 상단 메뉴 → Clear cache → Rerun
- 코드:
```python
import streamlit as st
st.cache_resource.clear()
st.cache_data.clear()
```
- 사이드바 버튼 예시:
```python
if st.sidebar.button("캐시 초기화"):
    st.cache_resource.clear()
    st.cache_data.clear()
    st.rerun()
```

## 문제 해결 가이드
- 검색 결과가 없을 때
  - 모드 확인(정산 질문은 “정산 업무”)
  - `stl_docs/txt` 파일 생성 여부 확인(JSON→TXT 재실행)
  - 벡터스토어 재생성: `rm -rf chroma_db/settlement && python build_vectorstores.py`
  - 리트리버 임계값: 정산은 `score_threshold=0.3`, 필요 시 더 낮추거나 `k` 증가
- Azure 429(한도 초과)
  - 잠시 대기 후 재시도
  - 청크/배치 파라미터 조정, 불필요한 짧은 청크 제거
  - 쿼터 상향 신청
- Chroma 영속성
  - `persist_directory` 사용 중이며 자동 저장
  - 빌드/로드 경로가 동일한지 확인(프로젝트 루트에서 실행 추천)

## 유용한 커맨드 요약
```bash
# Confluence 크롤링
python get_confl.py

# JSON → TXT
python json_to_txt.py -i stl_docs/confluence_data.json -o stl_docs/txt -c stl_docs/combined_confluence.txt --min-chars 200

# 벡터스토어 생성(초기화 포함)
rm -rf chroma_db/legal chroma_db/settlement && python build_vectorstores.py

# 앱 실행
streamlit run app.py
```

## 참고
- 정산 답변은 프로젝트 문서(벡터스토어)만 근거로 생성되며, 외부(사전학습) 지식 사용을 회피하도록 프롬프트에서 출처 인용을 강제합니다.
- 법률과 정산은 서로 다른 벡터스토어로 분리되어 관리됩니다. 