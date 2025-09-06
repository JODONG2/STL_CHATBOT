import os
from dotenv import load_dotenv
from typing import TypedDict, List, Any

load_dotenv()

# Azure OpenAI 설정
AZURE_OPENAI_API_KEY = os.getenv('AZURE_OPENAI_API_KEY')
AZURE_OPENAI_ENDPOINT = os.getenv('AZURE_OPENAI_ENDPOINT')
AZURE_OPENAI_CHAT_MODEL = os.getenv('AZURE_OPENAI_CHAT_MODEL', 'gpt-4-1106-preview')
AZURE_OPENAI_EMBEDDING_MODEL = os.getenv('AZURE_OPENAI_EMBEDDING_MODEL', 'text-embedding-3-large')
OPENAI_API_VERSION = os.getenv('OPENAI_API_VERSION', '2023-12-01-preview')

# 문서 디렉토리 설정
LEGAL_DOCS_DIR = "legal_docs"
STL_DOCS_DIR = "stl_docs"

# Confluence 데이터 파일 경로
CONFLUENCE_LEGAL_DATA_FILE = "confluence_data.json"
CONFLUENCE_SETTLEMENT_DATA_FILE = "stl_docs/confluence_data.json"

# ChromaDB 설정
CHROMA_PERSIST_DIR = "chroma_db"
CHROMA_LEGAL_PERSIST_DIR = "chroma_db/legal"
CHROMA_SETTLEMENT_PERSIST_DIR = "chroma_db/settlement"

# Confluence 설정
CONFLUENCE_BASE_URL = os.getenv('CONFLUENCE_BASE_URL', 'https://confluence.tde.sktelecom.com')
CONFLUENCE_TARGET_URL = os.getenv('CONFLUENCE_TARGET_URL', 'https://confluence.tde.sktelecom.com/spaces/SSPVTWO/pages/223745736')

class LegalAgentState(TypedDict):
    messages: List[Any]
    rag_docs: List[Any]
    remaining_steps: int  # ← 필수! 