#!/usr/bin/env python3
"""
벡터스토어 생성 스크립트
법률과 정산 관련 문서를 각각의 벡터스토어에 저장합니다.
"""

import logging
from rag_utils import build_legal_vectorstore, build_settlement_vectorstore

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """메인 실행 함수"""
    try:
        logger.info("벡터스토어 생성 시작...")
        
        # 1. 법률 관련 벡터스토어 생성
        logger.info("법률 관련 벡터스토어 생성 중...")
        legal_vectorstore = build_legal_vectorstore()
        logger.info("법률 관련 벡터스토어 생성 완료!")
        
        # 2. 정산 관련 벡터스토어 생성
        logger.info("정산 관련 벡터스토어 생성 중...")
        settlement_vectorstore = build_settlement_vectorstore()
        logger.info("정산 관련 벡터스토어 생성 완료!")
        
        logger.info("모든 벡터스토어 생성이 완료되었습니다!")
        
    except Exception as e:
        logger.error(f"벡터스토어 생성 중 오류 발생: {e}")
        raise

if __name__ == "__main__":
    main() 