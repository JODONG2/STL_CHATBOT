import os
from dotenv import load_dotenv
from typing import TypedDict, List, Any

load_dotenv()

AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_CHAT_MODEL = os.getenv("AZURE_OPENAI_CHAT_MODEL")
AZURE_OPENAI_EMBEDDING_MODEL = os.getenv("AZURE_OPENAI_EMBEDDING_MODEL")
OPENAI_API_VERSION = os.getenv("OPENAI_API_VERSION")

CHROMA_PERSIST_DIR = "./chroma_db"
LEGAL_DOCS_DIR = "./legal_docs"

class LegalAgentState(TypedDict):
    messages: List[Any]
    rag_docs: List[Any]
    remaining_steps: int  # ← 필수! 