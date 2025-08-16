import requests
import json
import time
import os
from typing import Dict, List, Optional
from dotenv import load_dotenv
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ConfluenceCrawler:
    def __init__(self):
        load_dotenv()
        
        # Confluence API 설정 (환경변수에서 가져오기)
        self.base_url = os.getenv('CONFLUENCE_BASE_URL', 'https://confluence.tde.sktelecom.com')
        self.api_url = f"{self.base_url}/rest/api"
        
        # 세션 쿠키 설정 (FIDO 인증 후 브라우저에서 복사)
        self.ajs_anonymous_id = os.getenv('AJS_ANONYMOUS_ID', 'your_ajs_anonymous_id_here')
        self.ajs_user_id = os.getenv('AJS_USER_ID', 'your_ajs_user_id_here')
        self.conf_sessionid = os.getenv('CONF_SESSIONID', 'your_conf_sessionid_here')
        self.jsessionid = os.getenv('JSESSIONID', 'your_jsessionid_here')
        
        # 요청 제한 설정 (초당 5회 제한)
        self.request_count = 0
        self.last_request_time = 0
        self.max_requests_per_second = 5
        
        # 세션 설정 (세션 쿠키 사용)
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # 세션 쿠키 설정
        self.session.cookies.set('ajs_anonymous_id', self.ajs_anonymous_id, domain='confluence.tde.sktelecom.com')
        self.session.cookies.set('ajs_user_id', self.ajs_user_id, domain='confluence.tde.sktelecom.com')
        self.session.cookies.set('CONF-SESSIONID', self.conf_sessionid, domain='confluence.tde.sktelecom.com')
        self.session.cookies.set('JSESSIONID', self.jsessionid, domain='confluence.tde.sktelecom.com')
        
        logger.info("세션 쿠키가 설정되었습니다.")
    
    def _rate_limit(self):
        """요청 제한을 위한 대기 로직"""
        current_time = time.time()
        
        # 1초가 지났으면 카운터 리셋
        if current_time - self.last_request_time >= 1:
            self.request_count = 0
            self.last_request_time = current_time
        
        # 2번 요청 후 1초 대기
        if self.request_count >= 2:
            logger.info("Rate limit reached. Waiting 1 second...")
            time.sleep(1)
            self.request_count = 0
            self.last_request_time = time.time()
        
        self.request_count += 1
    
    def _make_request(self, url: str, params: Optional[Dict] = None) -> Dict:
        """API 요청을 수행하는 메서드"""
        self._rate_limit()
        
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"API 요청 실패: {e}")
            logger.error(f"응답 상태 코드: {response.status_code if 'response' in locals() else 'N/A'}")
            logger.error(f"응답 내용: {response.text if 'response' in locals() else 'N/A'}")
            raise
    
    def get_page_info(self, page_id: str) -> Dict:
        """특정 페이지의 정보를 가져오는 메서드"""
        url = f"{self.api_url}/content/{page_id}"
        params = {
            'expand': 'body.storage,children.page,children.attachment,version'
        }
        
        logger.info(f"페이지 정보 가져오기: {page_id}")
        return self._make_request(url, params)
    
    def get_child_pages(self, page_id: str) -> List[Dict]:
        """특정 페이지의 하위 페이지들을 가져오는 메서드"""
        url = f"{self.api_url}/content/{page_id}/child/page"
        params = {
            'limit': 100,
            'expand': 'body.storage,version'
        }
        
        logger.info(f"하위 페이지 가져오기: {page_id}")
        return self._make_request(url, params)
    
    def get_space_pages(self, space_key: str) -> List[Dict]:
        """특정 스페이스의 모든 페이지를 가져오는 메서드"""
        url = f"{self.api_url}/content"
        params = {
            'spaceKey': space_key,
            'type': 'page',
            'limit': 100,
            'expand': 'body.storage,version,children.page'
        }
        
        logger.info(f"스페이스 페이지 가져오기: {space_key}")
        return self._make_request(url, params)
    
    def crawl_page_hierarchy(self, page_id: str) -> Dict:
        """페이지와 그 하위 페이지들을 재귀적으로 크롤링하는 메서드"""
        try:
            # 현재 페이지 정보 가져오기
            page_info = self.get_page_info(page_id)
            
            # 하위 페이지들 가져오기
            children_response = self.get_child_pages(page_id)
            children = children_response.get('results', [])
            
            # 하위 페이지들을 재귀적으로 크롤링
            child_pages = []
            for child in children:
                child_id = child['id']
                child_hierarchy = self.crawl_page_hierarchy(child_id)
                child_pages.append(child_hierarchy)
            
            # 결과 구성
            result = {
                'id': page_info['id'],
                'title': page_info['title'],
                'type': page_info['type'],
                'status': page_info['status'],
                'version': {
                    'number': page_info['version']['number'],
                    'message': page_info['version'].get('message', ''),
                    'minorEdit': page_info['version'].get('minorEdit', False)
                },
                'body': {
                    'storage': {
                        'value': page_info['body']['storage']['value'],
                        'representation': page_info['body']['storage']['representation']
                    }
                },
                'children': child_pages,
                'created': page_info.get('created', ''),
                'lastModified': page_info.get('lastModified', ''),
                'url': f"{self.base_url}{page_info['_links']['webui']}"
            }
            
            return result
            
        except Exception as e:
            logger.error(f"페이지 크롤링 실패 (ID: {page_id}): {e}")
            return {
                'id': page_id,
                'error': str(e),
                'children': []
            }
    
    def crawl_from_url(self, url: str) -> Dict:
        """URL에서 페이지 ID를 추출하고 크롤링을 시작하는 메서드"""
        # URL에서 페이지 ID 추출
        # 예: https://confluence.tde.sktelecom.com/spaces/SSPVTWO/pages/223745736
        try:
            page_id = url.split('/')[-1]
            logger.info(f"URL에서 페이지 ID 추출: {page_id}")
            
            # 페이지 계층 구조 크롤링
            result = self.crawl_page_hierarchy(page_id)
            return result
            
        except Exception as e:
            logger.error(f"URL 처리 실패: {e}")
            raise
    
    def save_to_json(self, data: Dict, filename: str = 'confluence_data.json'):
        """크롤링한 데이터를 JSON 파일로 저장하는 메서드"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"데이터가 {filename}에 저장되었습니다.")
        except Exception as e:
            logger.error(f"파일 저장 실패: {e}")
            raise

def main():
    """메인 실행 함수"""
    # Confluence 크롤러 초기화
    crawler = ConfluenceCrawler()
    
    # 대상 URL (환경변수에서 가져오기)
    target_url = os.getenv('CONFLUENCE_TARGET_URL', 'https://confluence.tde.sktelecom.com/spaces/SSPVTWO/pages/223745736')
    
    try:
        logger.info("Confluence 크롤링 시작...")
        logger.info(f"대상 URL: {target_url}")
        
        # URL에서 크롤링 시작
        result = crawler.crawl_from_url(target_url)
        
        # 결과를 JSON 파일로 저장
        crawler.save_to_json(result, 'confluence_data.json')
        
        logger.info("크롤링 완료!")
        
        # 간단한 통계 출력
        def count_pages(data):
            count = 1  # 현재 페이지
            for child in data.get('children', []):
                count += count_pages(child)
            return count
        
        total_pages = count_pages(result)
        logger.info(f"총 {total_pages}개의 페이지가 크롤링되었습니다.")
        
    except Exception as e:
        logger.error(f"크롤링 중 오류 발생: {e}")

if __name__ == "__main__":
    main()
