#!/usr/bin/env python3
"""
포트폴리오 프로젝트 데일리 브리핑 자동화
- Notion에서 데이터 조회
- 브리핑 생성 후 Google Docs에 저장
"""

import os
import json
from datetime import datetime, timedelta

import requests
from google.auth.transport.requests import Request
from google.oauth2.service_account import Credentials
from google.api_core.exceptions import GoogleAPIError
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


class DailyBriefing:
    def __init__(self):
        self.notion_token = os.getenv('NOTION_TOKEN')
        self.notion_db_id = os.getenv('NOTION_DATABASE_ID')
        self.google_docs_folder_id = os.getenv('GOOGLE_DOCS_FOLDER_ID')  # Google Drive 폴더 ID

        self.notion_headers = {
            'Authorization': f'Bearer {self.notion_token}',
            'Notion-Version': '2022-06-28',
            'Content-Type': 'application/json'
        }

        # Google Docs API 인증
        self.docs_service = self._init_google_docs()

    def get_notion_data(self):
        """Notion 데이터베이스에서 오늘/어제 항목 조회"""
        try:
            url = f'https://api.notion.com/v1/databases/{self.notion_db_id}/query'

            # 쿼리: 최근 데이터 (빈 payload - 모든 데이터 조회)
            payload = {}

            response = requests.post(url, json=payload, headers=self.notion_headers)
            response.raise_for_status()

            data = response.json()
            results = data.get('results', [])

            # 오늘/어제 데이터 분류
            today = datetime.now().date()
            yesterday = today - timedelta(days=1)

            today_items = []
            yesterday_items = []
            pending_items = []

            for item in results:
                props = item.get('properties', {})

                # 필요한 필드 추출
                title = self._extract_text(props.get('Name'))
                status = self._extract_select(props.get('상태'))
                created = self._extract_date(props.get('생성일'))
                priority = self._extract_select(props.get('우선순위'))

                if not title:
                    continue

                # 상태별 분류
                if status == 'COMPLETED':
                    if created == str(yesterday):
                        yesterday_items.append({
                            'title': title,
                            'status': status,
                            'priority': priority
                        })
                elif status == 'PENDING' or priority == 'HIGH':
                    pending_items.append({
                        'title': title,
                        'status': status,
                        'priority': priority
                    })
                elif created == str(today):
                    today_items.append({
                        'title': title,
                        'status': status,
                        'priority': priority
                    })

            return {
                'today': today_items[:5],
                'yesterday': yesterday_items[:5],
                'pending': pending_items[:3]
            }

        except Exception as e:
            print(f"❌ Notion 데이터 조회 실패: {e}")
            return {'today': [], 'yesterday': [], 'pending': []}

    def _extract_text(self, prop):
        """Notion 텍스트 필드 추출"""
        if not prop or not prop.get('title'):
            return None
        return prop['title'][0]['text']['content'] if prop['title'] else None

    def _extract_select(self, prop):
        """Notion 선택지 필드 추출"""
        if not prop or not prop.get('select'):
            return None
        return prop['select']['name'] if prop['select'] else None

    def _extract_date(self, prop):
        """Notion 날짜 필드 추출"""
        if not prop or not prop.get('date'):
            return None
        return prop['date']['start'] if prop['date'] else None

    def _init_google_docs(self):
        """Google Docs API 초기화"""
        try:
            service_account_json = os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON')
            if not service_account_json:
                print("❌ GOOGLE_SERVICE_ACCOUNT_JSON 환경 변수 없음")
                return None

            service_account_info = json.loads(service_account_json)
            credentials = Credentials.from_service_account_info(
                service_account_info,
                scopes=['https://www.googleapis.com/auth/documents',
                        'https://www.googleapis.com/auth/drive']
            )

            service = build('docs', 'v1', credentials=credentials)
            return service

        except Exception as e:
            print(f"❌ Google Docs API 초기화 실패: {e}")
            return None

    def generate_briefing(self, data):
        """브리핑 메시지 생성"""
        today = datetime.now().strftime('%Y년 %m월 %d일 (%A)')

        message = f"""
📅 **포트폴리오 프로젝트 데일리 브리핑**

*{today}*

---

"""

        # 어제 완료 항목
        if data['yesterday']:
            message += "✅ **어제 완료 항목**\n"
            for i, item in enumerate(data['yesterday'], 1):
                message += f"  {i}. {item['title']}\n"
            message += "\n"

        # 오늘 예정 항목
        if data['today']:
            message += "🎯 **오늘 계획**\n"
            for i, item in enumerate(data['today'], 1):
                priority_mark = "🔴" if item.get('priority') == 'HIGH' else "🟡"
                message += f"  {i}. {priority_mark} {item['title']}\n"
            message += "\n"

        # 미실행 항목
        if data['pending']:
            message += "⚠️ **미실행 항목 (우선순위)**\n"
            for i, item in enumerate(data['pending'], 1):
                message += f"  {i}. {item['title']} (상태: {item.get('status', '미정')})\n"
            message += "\n"

        message += "---\n"
        message += f"생성: {datetime.now().strftime('%H:%M:%S')} | 자동화 시스템"

        return message

    def save_to_google_docs(self, briefing_text):
        """생성된 브리핑을 Google Docs에 저장"""
        try:
            if not self.docs_service:
                print("❌ Google Docs API 사용 불가")
                return None

            # Google Docs 문서 생성
            briefing_date = datetime.now().strftime('%Y-%m-%d')
            title = f'📅 데일리 브리핑 - {briefing_date}'

            document = {
                'title': title
            }

            doc = self.docs_service.documents().create(body=document).execute()
            doc_id = doc.get('documentId')

            # 문서에 내용 추가
            requests_list = [
                {
                    'insertText': {
                        'text': briefing_text,
                        'location': {
                            'index': 1
                        }
                    }
                }
            ]

            self.docs_service.documents().batchUpdate(
                documentId=doc_id,
                body={'requests': requests_list}
            ).execute()

            # 공유 링크 생성 (Google Drive API 필요)
            drive_service = build('drive', 'v3', credentials=self.docs_service._http.request)

            # 문서를 폴더에 이동 (선택)
            if self.google_docs_folder_id:
                drive_service.files().update(
                    fileId=doc_id,
                    addParents=self.google_docs_folder_id,
                    removeParents='root'
                ).execute()

            # 모두가 볼 수 있도록 공유
            drive_service.permissions().create(
                fileId=doc_id,
                body={
                    'kind': 'drive#permission',
                    'role': 'reader',
                    'type': 'anyone'
                }
            ).execute()

            # 공유 링크
            share_link = f'https://docs.google.com/document/d/{doc_id}/edit?usp=sharing'

            print(f"✅ Google Docs 생성 완료")
            print(f"📎 링크: {share_link}")
            return share_link

        except Exception as e:
            print(f"❌ Google Docs 저장 실패: {e}")
            return None

    def run(self):
        """전체 브리핑 프로세스 실행"""
        print("🚀 데일리 브리핑 자동화 시작...")

        # 1. Notion 데이터 조회
        print("📊 Notion 데이터 조회 중...")
        data = self.get_notion_data()

        # 2. 브리핑 생성
        print("📝 브리핑 생성 중...")
        briefing = self.generate_briefing(data)

        # 3. Google Docs에 저장
        print("💾 Google Docs에 저장 중...")
        share_link = self.save_to_google_docs(briefing)

        if share_link:
            print(f"\n✅ 데일리 브리핑이 생성되었습니다!")
            print(f"📄 Google Docs 링크: {share_link}")
        else:
            print("❌ Google Docs 저장 실패")


if __name__ == '__main__':
    briefing = DailyBriefing()
    briefing.run()
