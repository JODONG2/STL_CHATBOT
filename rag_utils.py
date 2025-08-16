import os
from glob import glob
from typing import List, Literal
from config import LEGAL_DOCS_DIR, CHROMA_PERSIST_DIR, AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_EMBEDDING_MODEL

from langchain_community.document_loaders import PyPDFLoader, PyMuPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import AzureOpenAIEmbeddings
from langchain_chroma import Chroma

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

# 텍스트 청킹 함수

def chunk_documents(
    docs: List,
    chunk_size: int = 1000,
    chunk_overlap: int = 200
) -> List:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
    return splitter.split_documents(docs)

# 임베딩 객체 생성 함수

def get_azure_embeddings():
    return AzureOpenAIEmbeddings(
        azure_endpoint=AZURE_OPENAI_ENDPOINT,
        api_key=AZURE_OPENAI_API_KEY,
        model=AZURE_OPENAI_EMBEDDING_MODEL,
    )

# ChromaDB 벡터스토어 생성 및 저장 함수

def build_chroma_vectorstore(
    chunks: List,
    persist_directory: str = CHROMA_PERSIST_DIR
):
    embeddings = get_azure_embeddings()
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=persist_directory
    )
    vectorstore.persist()
    return vectorstore

# ChromaDB 벡터스토어 로드 함수

def load_chroma_vectorstore(
    persist_directory: str = CHROMA_PERSIST_DIR
):
    embeddings = get_azure_embeddings()
    return Chroma(
        embedding_function=embeddings,
        persist_directory=persist_directory
    )

# 리트리버 생성 함수

def get_retriever(
    vectorstore,
    top_k: int = 5,
    score_threshold: float = 0.7
):
    return vectorstore.as_retriever(
        search_kwargs={"k": top_k, "score_threshold": score_threshold}
    ) 