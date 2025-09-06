import json
import os
from typing import List, Dict, Any
from bs4 import BeautifulSoup
from langchain_core.documents import Document
import logging

logger = logging.getLogger(__name__)

class ConfluenceLoader:
    """Confluence JSON 데이터를 LangChain Document로 변환하는 로더"""
    
    def __init__(self, json_file_path: str):
        self.json_file_path = json_file_path
        
    def _clean_html_content(self, html_content: str) -> str:
        """HTML 내용을 텍스트로 변환"""
        if not html_content:
            return ""
        
        try:
            # BeautifulSoup을 사용하여 HTML 파싱
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # HTML 태그 제거하고 텍스트만 추출
            text = soup.get_text(separator=' ', strip=True)
            
            # 연속된 공백 정리
            text = ' '.join(text.split())
            
            return text
        except Exception as e:
            logger.error(f"HTML 파싱 실패: {e}")
            return html_content
    
    def _extract_page_content(self, page_data: Dict[str, Any]) -> List[Document]:
        """단일 페이지 데이터를 Document로 변환"""
        documents = []
        
        try:
            # 페이지 기본 정보
            page_id = page_data.get('id', '')
            title = page_data.get('title', '')
            page_type = page_data.get('type', '')
            status = page_data.get('status', '')
            url = page_data.get('url', '')
            
            # HTML 내용 추출 및 정리
            html_content = page_data.get('body', {}).get('storage', {}).get('value', '')
            clean_content = self._clean_html_content(html_content)
            
            # 내용이 있는 경우에만 Document 생성
            if clean_content.strip():
                # 메타데이터 구성
                metadata = {
                    'source': 'confluence',
                    'page_id': page_id,
                    'title': title,
                    'type': page_type,
                    'status': status,
                    'url': url,
                    'content_type': 'page'
                }
                
                # Document 생성
                doc = Document(
                    page_content=clean_content,
                    metadata=metadata
                )
                documents.append(doc)
                
                logger.info(f"페이지 로드 완료: {title} (ID: {page_id})")
            else:
                logger.warning(f"빈 내용 페이지: {title} (ID: {page_id})")
            
            # 하위 페이지들 재귀적으로 처리
            children = page_data.get('children', [])
            for child in children:
                child_docs = self._extract_page_content(child)
                documents.extend(child_docs)
                
        except Exception as e:
            logger.error(f"페이지 처리 실패 (ID: {page_data.get('id', 'unknown')}): {e}")
        
        return documents
    
    def load(self) -> List[Document]:
        """JSON 파일을 로드하여 Document 리스트로 변환"""
        try:
            logger.info(f"Confluence 데이터 로드 시작: {self.json_file_path}")
            
            # JSON 파일 읽기
            with open(self.json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 페이지 데이터를 Document로 변환
            documents = self._extract_page_content(data)
            
            logger.info(f"Confluence 데이터 로드 완료: {len(documents)}개 문서")
            return documents
            
        except FileNotFoundError:
            logger.error(f"파일을 찾을 수 없습니다: {self.json_file_path}")
            return []
        except json.JSONDecodeError as e:
            logger.error(f"JSON 파싱 실패: {e}")
            return []
        except Exception as e:
            logger.error(f"데이터 로드 실패: {e}")
            return []

def load_confluence_documents(json_file_path: str) -> List[Document]:
    """Confluence JSON 파일을 로드하는 편의 함수"""
    loader = ConfluenceLoader(json_file_path)
    return loader.load()

def load_legal_confluence_documents() -> List[Document]:
    """법률 관련 Confluence 문서 로드"""
    json_file_path = "confluence_data.json"
    if os.path.exists(json_file_path):
        return load_confluence_documents(json_file_path)
    else:
        logger.warning(f"법률 Confluence 파일이 없습니다: {json_file_path}")
        return []

def load_settlement_confluence_documents() -> List[Document]:
    """정산 관련 Confluence 문서 로드"""
    json_file_path = "stl_docs/confluence_data.json"
    if os.path.exists(json_file_path):
        return load_confluence_documents(json_file_path)
    else:
        logger.warning(f"정산 Confluence 파일이 없습니다: {json_file_path}")
        return [] 