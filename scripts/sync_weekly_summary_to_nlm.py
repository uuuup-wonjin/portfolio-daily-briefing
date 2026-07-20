#!/usr/bin/env python3
"""
주간 요약을 Notion에서 읽어서 NLM 노트북에 저장
로컬 Claude Code 세션에서 실행 (GitHub Actions X)

사용 방법:
  python scripts/sync_weekly_summary_to_nlm.py

또는 Claude Code에서:
  /비용분석_자동화_스크립트 sync_to_nlm
"""

import os
import sys
from datetime import datetime, timedelta
import requests


class NotionNLMSync:
    def __init__(self):
        self.notion_token = os.getenv('NOTION_TOKEN')
        self.briefing_db_id = os.getenv('NOTION_BRIEFING_DB_ID')

        if not self.notion_token or not self.briefing_db_id:
            print("❌ 환경 변수 설정 필요:")
            print("  export NOTION_TOKEN='...'")
            print("  export NOTION_BRIEFING_DB_ID='...'")
            sys.exit(1)

        self.notion_headers = {
            'Authorization': f'Bearer {self.notion_token}',
            'Notion-Version': '2022-06-28',
            'Content-Type': 'application/json'
        }

    def get_latest_weekly_summary(self):
        """최신 주간 요약 조회"""
        try:
            url = f'https://api.notion.com/v1/databases/{self.briefing_db_id}/query'

            # 최근 데이터베이스 검색
            payload = {
                "filter": {
                    "property": "제목",
                    "title": {
                        "contains": "주간 요약"
                    }
                },
                "sorts": [
                    {
                        "property": "날짜",
                        "direction": "descending"
                    }
                ],
                "page_size": 1
            }

            response = requests.post(url, json=payload, headers=self.notion_headers)
            response.raise_for_status()

            results = response.json().get('results', [])

            if not results:
                print("❌ Notion에서 주간 요약을 찾을 수 없습니다")
                return None

            page = results[0]
            props = page.get('properties', {})

            # 필드 추출
            title = self._extract_text(props.get('제목'))
            date = self._extract_date(props.get('날짜'))
            content = self._extract_text(props.get('내용'))

            if not content:
                print("❌ 주간 요약 내용이 비어있습니다")
                return None

            return {
                'title': title,
                'date': date,
                'content': content
            }

        except Exception as e:
            print(f"❌ Notion 조회 실패: {e}")
            return None

    def _extract_text(self, prop):
        """텍스트 필드 추출"""
        if not prop:
            return None
        if prop.get('title'):
            return prop['title'][0]['text']['content'] if prop['title'] else None
        if prop.get('rich_text'):
            return prop['rich_text'][0]['text']['content'] if prop['rich_text'] else None
        return None

    def _extract_date(self, prop):
        """날짜 필드 추출"""
        if not prop or not prop.get('date'):
            return None
        return prop['date']['start']

    def format_for_nlm(self, summary):
        """NLM 형식으로 포맷팅"""
        formatted = f"""# {summary['title']}

📅 생성일: {summary['date']}

---

{summary['content']}

---

**이 요약은 GitHub Actions에서 자동 생성되었습니다.**
- 데이터 소스: Notion 포트폴리오 프로젝트
- 자동화: GitHub Actions (매주 일요일 8시)
- 생성 도구: Python 스크립트
"""
        return formatted

    def save_to_nlm_manual(self, content):
        """NLM에 저장하는 안내 (수동)"""
        print("\n" + "="*60)
        print("📝 NLM 노트북에 저장하는 방법")
        print("="*60)
        print("\n다음 내용을 복사하여 NLM 노트북에 새 노트로 생성하세요:\n")
        print("-" * 60)
        print(content)
        print("-" * 60)
        print("\n📌 NLM 저장 단계:")
        print("1. NotebookLM 열기")
        print("2. 'Cowork 세션 기록: uuuup-daily-briefing' 노트북 선택")
        print("3. '+ 새 노트' 클릭")
        print("4. 제목 입력: '📊 주간 요약 - YYYY-WXX'")
        print("5. 위 내용 붙여넣기")
        print("6. 저장")
        print("\n✅ 완료!")

    def run(self):
        """주간 요약 동기화 실행"""
        print("🚀 주간 요약 → NLM 동기화 시작...\n")

        # 1. Notion에서 최신 주간 요약 조회
        print("📊 Notion에서 최신 주간 요약 조회 중...")
        summary = self.get_latest_weekly_summary()

        if not summary:
            print("❌ 프로세스 중단")
            return False

        print(f"✅ 조회 완료: {summary['title']}")

        # 2. NLM 형식으로 포맷팅
        print("\n📝 NLM 형식으로 변환 중...")
        formatted_content = self.format_for_nlm(summary)

        # 3. 저장 안내
        print("\n💾 NLM 저장 안내...")
        self.save_to_nlm_manual(formatted_content)

        # 4. 클립보드에 복사 (macOS)
        try:
            import subprocess
            process = subprocess.Popen(['pbcopy'], stdin=subprocess.PIPE)
            process.communicate(formatted_content.encode('utf-8'))
            print("\n📋 내용이 클립보드에 복사되었습니다!")
            print("   (Cmd+V로 바로 붙여넣을 수 있습니다)")
        except Exception:
            print("\n💡 클립보드 복사 실패 (macOS 전용)")
            print("   위 내용을 수동으로 복사해주세요")

        return True


if __name__ == '__main__':
    sync = NotionNLMSync()
    sync.run()
