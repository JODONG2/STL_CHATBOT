import os
from glob import glob
from typing import List, Literal
import time
import logging
from config import (
    LEGAL_DOCS_DIR, STL_DOCS_DIR,
    CHROMA_PERSIST_DIR, CHROMA_LEGAL_PERSIST_DIR, CHROMA_SETTLEMENT_PERSIST_DIR,
    AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_EMBEDDING_MODEL,
    OPENAI_API_VERSION,
)

from langchain_community.document_loaders import PyPDFLoader, PyMuPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import AzureOpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document

logger = logging.getLogger(__name__)

# PDF 파일 로딩 함수

def load_pdf_documents(
    folder: str = LEGAL_DOCS_DIR,
    loader_type: Literal["pypdf", "pymupdf"] = "pypdf"
) -> List:
    """
    지정 폴더 내 모든 PDF 파일을 로딩하여 LangChain Document 리스트로 반환
    loader_type: 'pypdf' 또는 'pymupdf'
    """
    pdf_files = glob(os.path.join(folder, "*.pdf"))
    docs = []
    for file in pdf_files:
        if loader_type == "pypdf":
            loader = PyPDFLoader(file)
        else:
            loader = PyMuPDFLoader(file)
        docs.extend(loader.load())
    return docs

# TXT 파일 로딩 함수 (정산용)

def load_text_documents(folder: str) -> List[Document]:
    """폴더 내 모든 .txt 파일을 읽어 LangChain Document 리스트로 반환"""
    if not os.path.isdir(folder):
        logger.warning(f"Text folder not found: {folder}")
        return []
    paths = sorted(glob(os.path.join(folder, "*.txt")))
    documents: List[Document] = []
    for path in paths:
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            if not content or len(content.strip()) == 0:
                continue
            title = os.path.splitext(os.path.basename(path))[0]
            metadata = {
                "source": "stl_txt",
                "path": path,
                "title": title,
            }
            documents.append(Document(page_content=content, metadata=metadata))
        except Exception as e:
            logger.error(f"Failed to read {path}: {e}")
    return documents

# 문서 로딩 함수

def load_legal_documents() -> List:
    """법률 관련 문서 로드 (PDF만 사용)"""
    docs = []
    # PDF 문서만 로드
    pdf_docs = load_pdf_documents(LEGAL_DOCS_DIR)
    docs.extend(pdf_docs)
    return docs

def load_settlement_documents() -> List:
    """정산 관련 문서 로드 (TXT 변환본 사용)"""
    # 권장: json_to_txt.py 실행 후 생성된 stl_docs/txt/*.txt 사용
    txt_folder = os.path.join(STL_DOCS_DIR, "txt")
    docs = load_text_documents(txt_folder)
    return docs

# 텍스트 청킹 및 필터링 함수

def chunk_documents(
    docs: List,
    chunk_size: int = 2000,
    chunk_overlap: int = 100
) -> List:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
    chunks = splitter.split_documents(docs)
    # 너무 짧은 청크 제거 (임베딩 호출 수 절감)
    filtered = [d for d in chunks if d.page_content and len(d.page_content.strip()) >= 50]
    if len(filtered) < len(chunks):
        logger.info(f"Filtered out {len(chunks) - len(filtered)} short chunks (<50 chars)")
    return filtered

# 임베딩 객체 생성 함수

def get_azure_embeddings():
    return AzureOpenAIEmbeddings(
        azure_endpoint=AZURE_OPENAI_ENDPOINT,
        api_key=AZURE_OPENAI_API_KEY,
        model=AZURE_OPENAI_EMBEDDING_MODEL,
        openai_api_version=OPENAI_API_VERSION,
    )

# ChromaDB 벡터스토어 생성 및 저장 함수 (배치 + 백오프)

def build_chroma_vectorstore(
    chunks: List,
    persist_directory: str = CHROMA_PERSIST_DIR,
    batch_size: int = 64,
    sleep_seconds_between_batches: float = 0.3,
    max_retries: int = 3,
):
    embeddings = get_azure_embeddings()
    vectorstore = Chroma(
        embedding_function=embeddings,
        persist_directory=persist_directory
    )

    total = len(chunks)
    logger.info(f"Adding {total} chunks to vectorstore in batches of {batch_size}...")

    for start in range(0, total, batch_size):
        end = min(start + batch_size, total)
        batch = chunks[start:end]
        attempt = 0
        while True:
            try:
                vectorstore.add_documents(batch)
                break
            except Exception as e:
                attempt += 1
                if attempt > max_retries:
                    logger.error(f"Failed to add batch {start}-{end}: {e}")
                    raise
                backoff = min(2 ** (attempt - 1), 8)
                logger.warning(f"Error on batch {start}-{end}, retrying in {backoff}s (attempt {attempt}/{max_retries})...")
                time.sleep(backoff)
        # 레이트 리밋 완화용 간격
        if end < total:
            time.sleep(sleep_seconds_between_batches)

    # langchain-chroma는 persist_directory 사용 시 자동 영속화됩니다.
    logger.info("Vectorstore build complete (auto-persisted).")
    return vectorstore


def build_legal_vectorstore():
    """법률 관련 벡터스토어 생성 (PDF만 사용)"""
    docs = load_legal_documents()
    chunks = chunk_documents(docs)
    return build_chroma_vectorstore(chunks, CHROMA_LEGAL_PERSIST_DIR)


def build_settlement_vectorstore():
    """정산 관련 벡터스토어 생성 (TXT 변환본 사용)"""
    docs = load_settlement_documents()
    chunks = chunk_documents(docs)
    return build_chroma_vectorstore(chunks, CHROMA_SETTLEMENT_PERSIST_DIR)

# ChromaDB 벡터스토어 로드 함수

def load_chroma_vectorstore(
    persist_directory: str = CHROMA_PERSIST_DIR
):
    embeddings = get_azure_embeddings()
    return Chroma(
        embedding_function=embeddings,
        persist_directory=persist_directory
    )


def load_legal_vectorstore():
    """법률 관련 벡터스토어 로드"""
    return load_chroma_vectorstore(CHROMA_LEGAL_PERSIST_DIR)


def load_settlement_vectorstore():
    """정산 관련 벡터스토어 로드"""
    return load_chroma_vectorstore(CHROMA_SETTLEMENT_PERSIST_DIR)

# 리트리버 생성 함수

def get_retriever(
    vectorstore,
    top_k: int = 5,
    score_threshold: float = 0.7
):
    return vectorstore.as_retriever(
        search_kwargs={"k": top_k} # , "score_threshold": score_threshold}
    )


def get_legal_retriever():
    """법률 관련 리트리버 생성"""
    vectorstore = load_legal_vectorstore()
    return get_retriever(vectorstore)


def get_settlement_retriever():
    """정산 관련 리트리버 생성"""
    vectorstore = load_settlement_vectorstore()
    return get_retriever(vectorstore, top_k=5, score_threshold=0.3) 