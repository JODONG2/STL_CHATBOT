# db_manager.py
"""
ChromaDB 등 DB 관리 및 초기화 함수 정의
"""

import os
import glob
from typing import List, Dict, Optional
from rag_utils import get_vectorstore, load_and_split_pdf

LEGAL_DOCS_DIR = "legal_docs"

class LegalDocDBManager:
    def __init__(self, persist_directory: str = "chroma_db"):
        self.persist_directory = persist_directory
        self.vectorstore = get_vectorstore(persist_directory=self.persist_directory)

    def list_documents(self) -> List[Dict]:
        """벡터스토어에 저장된 모든 문서의 메타데이터 리스트 반환"""
        return [doc.metadata for doc in self.vectorstore.get()['documents']]

    def add_document(self, pdf_path: str) -> None:
        """PDF 파일을 벡터스토어에 추가 및 임베딩"""
        docs = load_and_split_pdf(pdf_path)
        self.vectorstore.add_documents(docs)
        self.vectorstore.persist()

    def remove_document(self, doc_id: str) -> None:
        """문서 ID로 벡터스토어에서 삭제"""
        self.vectorstore.delete([doc_id])
        self.vectorstore.persist()

    def sync_documents(self) -> None:
        """legal_docs 폴더 내 PDF 파일과 벡터스토어 동기화 (새 파일 자동 임베딩)"""
        pdf_files = glob.glob(os.path.join(LEGAL_DOCS_DIR, "*.pdf"))
        existing_docs = set([meta.get('source') for meta in self.list_documents()])
        for pdf_path in pdf_files:
            if pdf_path not in existing_docs:
                self.add_document(pdf_path)

    def get_document_by_name(self, filename: str) -> Optional[Dict]:
        """파일명으로 문서 메타데이터 검색"""
        for meta in self.list_documents():
            if meta.get('source', '').endswith(filename):
                return meta
        return None

# 사용 예시 (직접 실행 시)
if __name__ == "__main__":
    db = LegalDocDBManager()
    db.sync_documents()
    print(db.list_documents()) 