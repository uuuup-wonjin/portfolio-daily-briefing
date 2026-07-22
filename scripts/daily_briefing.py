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
from googleapiclient.http import MediaInMemoryUpload


class DailyBriefing:
    def __init__(self):
        self.notion_token = os.getenv('NOTION_TOKEN')
        self.notion_db_id = os.getenv('NOTION_DATABASE_ID')
        self.google_docs_folder_id = os.getenv('GOOGLE_DOCS_FOLDER_ID')
        self.google_sheets_id = os.getenv('GOOGLE_SHEETS_ID')

        self.notion_headers = {
            'Authorization': f'Bearer {self.notion_token}',
            'Notion-Version': '2022-06-28',
            'Content-Type': 'application/json'
        }

        # Google API 인증
        self.docs_service = self._init_google_docs()
        self.sheets_service = self._init_google_sheets()
        self.drive_service = self._init_google_drive()

    def get_notion_data(self):
        """Notion 데이터베이스에서 모든 항목 조회 (필터 완화)"""
        try:
            url = f'https://api.notion.com/v1/databases/{self.notion_db_id}/query'

            # 쿼리: 최근 데이터 (빈 payload - 모든 데이터 조회)
            payload = {}

            response = requests.post(url, json=payload, headers=self.notion_headers)
            response.raise_for_status()

            data = response.json()
            results = data.get('results', [])

            # 단순 분류: 모든 항목 수집 (필터 완화)
            today = datetime.now().date()
            yesterday = today - timedelta(days=1)

            today_items = []
            yesterday_items = []
            pending_items = []
            all_items = []

            for item in results:
                props = item.get('properties', {})

                # 필요한 필드 추출
                title = self._extract_text(props.get('Name'))
                status = self._extract_select(props.get('상태'))
                created = self._extract_date(props.get('생성일'))
                priority = self._extract_select(props.get('우선순위'))

                if not title:
                    continue

                item_data = {
                    'title': title,
                    'status': status if status else '미정',
                    'priority': priority if priority else '없음',
                    'created': created if created else '미정'
                }

                # 우선순위: 완료(어제) > 미실행(PENDING) > 계획(오늘) > 전체
                if status == 'COMPLETED' and created == str(yesterday):
                    yesterday_items.append(item_data)
                elif status == 'PENDING' or priority == 'HIGH':
                    pending_items.append(item_data)
                elif created == str(today):
                    today_items.append(item_data)

                all_items.append(item_data)

            # 우선순위 순으로 반환
            return {
                'today': today_items[:5] if today_items else all_items[:3],
                'yesterday': yesterday_items[:5] if yesterday_items else [],
                'pending': pending_items[:3] if pending_items else all_items[3:6]
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
        """Google Drive API 초기화 (문서 생성용)"""
        try:
            service_account_json = os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON')
            if not service_account_json:
                print("❌ GOOGLE_SERVICE_ACCOUNT_JSON 환경 변수 없음")
                return None

            service_account_info = json.loads(service_account_json)
            credentials = Credentials.from_service_account_info(
                service_account_info,
                scopes=['https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/spreadsheets']
            )

            self.credentials = credentials
            service = build('drive', 'v3', credentials=credentials)
            return service

        except Exception as e:
            print(f"❌ Google Drive API 초기화 실패: {e}")
            return None

    def _init_google_sheets(self):
        """Google Sheets API 초기화"""
        try:
            if not hasattr(self, 'credentials'):
                return None
            service = build('sheets', 'v4', credentials=self.credentials)
            return service
        except Exception as e:
            print(f"❌ Google Sheets API 초기화 실패: {e}")
            return None

    def _init_google_drive(self):
        """Google Drive API 초기화"""
        try:
            if not hasattr(self, 'credentials'):
                return None
            service = build('drive', 'v3', credentials=self.credentials)
            return service
        except Exception as e:
            print(f"❌ Google Drive API 초기화 실패: {e}")
            return None

    def create_google_sheets(self):
        """Google Sheets 자동 생성"""
        try:
            if not self.sheets_service:
                print("❌ Google Sheets API 사용 불가")
                return None

            # 새로운 Spreadsheet 생성
            spreadsheet = {
                'properties': {
                    'title': '📅 포트폴리오 데일리 브리핑'
                }
            }

            result = self.sheets_service.spreadsheets().create(
                body=spreadsheet,
                fields='spreadsheetId'
            ).execute()

            sheet_id = result.get('spreadsheetId')

            # 첫 번째 행에 헤더 추가
            values = [['날짜', '브리핑 내용']]
            body = {'values': values}

            self.sheets_service.spreadsheets().values().update(
                spreadsheetId=sheet_id,
                range='A1',
                valueInputOption='RAW',
                body=body
            ).execute()

            print(f"✅ Google Sheets 생성 완료")
            print(f"📝 Sheet ID: {sheet_id}")
            print(f"📎 링크: https://docs.google.com/spreadsheets/d/{sheet_id}/edit")

            # Sheet ID를 파일에 저장
            with open('.sheets_id', 'w') as f:
                f.write(sheet_id)

            return sheet_id

        except Exception as e:
            print(f"❌ Google Sheets 생성 실패: {e}")
            return None

    def generate_briefing(self, data):
        """UUUUP 규칙 적용 브리핑 생성"""
        today = datetime.now()
        date_str = today.strftime('%Y년 %m월 %d일')
        day_name = ['월', '화', '수', '목', '금', '토', '일'][today.weekday()]
        time_str = today.strftime('%H:%M')

        message = f"""# 포트폴리오 프로젝트 데일리 브리핑 — {date_str} ({day_name})

**작성일**: {date_str} | **분석 기간**: {today.strftime('%Y-%m-%d')} ({day_name})

---

## 1. 핵심 요약

"""

        # 핵심 요약 (최대 3줄)
        summary_items = []
        if data['yesterday']:
            summary_items.append(f"✅ 어제 {len(data['yesterday'])}건 완료")
        if data['today']:
            summary_items.append(f"🎯 오늘 {len(data['today'])}건 계획")
        if data['pending']:
            summary_items.append(f"⚠️ 미실행 {len(data['pending'])}건 대기 중")

        if summary_items:
            for item in summary_items[:3]:
                message += f"- {item}\n"
        else:
            message += "- 진행 중인 업무 없음\n"

        message += """
---

## 2. 주요 업무 현황

### 어제 완료 항목
"""

        # 어제 완료 항목
        if data['yesterday']:
            message += "| 항목 | 우선순위 |\n"
            message += "|------|----------|\n"
            for item in data['yesterday']:
                priority = item.get('priority', '없음')
                message += f"| {item['title']} | {priority} |\n"
        else:
            message += "(완료 항목 없음)\n"

        message += """
### 오늘 계획
"""

        # 오늘 계획
        if data['today']:
            message += "| 항목 | 우선순위 | 상태 |\n"
            message += "|------|----------|------|\n"
            for item in data['today']:
                priority = item.get('priority', '없음')
                status = item.get('status', '미정')
                message += f"| {item['title']} | {priority} | {status} |\n"
        else:
            message += "(등록된 계획 없음)\n"

        message += """
### 미실행 항목
"""

        # 미실행 항목
        if data['pending']:
            message += "| 항목 | 상태 | 우선순위 |\n"
            message += "|------|------|----------|\n"
            for item in data['pending']:
                status = item.get('status', '대기')
                priority = item.get('priority', '없음')
                message += f"| {item['title']} | {status} | {priority} |\n"
        else:
            message += "(미실행 항목 없음)\n"

        message += """
---

## 3. 주의사항

- Notion 데이터 필터: 상태(COMPLETED/PENDING) 및 우선순위(HIGH) 기준
- 미등록 항목은 "미정"으로 표기

---

"""
        message += f"**생성**: {date_str} {time_str} KST | 자동화 시스템"

        return message

    def save_to_google_docs(self, briefing_text):
        """생성된 브리핑을 GitHub에 저장"""
        try:
            import os

            briefing_date = datetime.now().strftime('%Y-%m-%d')

            # briefings 폴더 생성 (없으면)
            if not os.path.exists('briefings'):
                os.makedirs('briefings')

            # 파일 저장
            filename = f'briefings/{briefing_date}.txt'
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(briefing_text)

            print(f"✅ 브리핑 생성 완료")
            print(f"📝 파일: {filename}")
            print(f"📎 GitHub 저장소에 저장됨")

            return filename

        except Exception as e:
            print(f"❌ 브리핑 저장 실패: {e}")
            return None

    def save_to_google_sheets(self, briefing_text):
        """생성된 브리핑을 Google Sheets에 추가"""
        try:
            if not self.sheets_service or not self.google_sheets_id:
                print("⏭️  Google Sheets 저장 건너뜀 (설정 없음)")
                return None

            briefing_date = datetime.now().strftime('%Y-%m-%d')

            # Sheet에 행 추가
            values = [[briefing_date, briefing_text]]
            body = {'values': values}

            self.sheets_service.spreadsheets().values().append(
                spreadsheetId=self.google_sheets_id,
                range='A:B',
                valueInputOption='RAW',
                body=body
            ).execute()

            print(f"✅ Google Sheets에 추가 완료")
            print(f"📎 링크: https://docs.google.com/spreadsheets/d/{self.google_sheets_id}/edit")

            return self.google_sheets_id

        except Exception as e:
            print(f"⚠️  Google Sheets 저장 실패: {e}")
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

        # 3. GitHub에 저장
        print("📤 GitHub에 저장 중...")
        github_link = self.save_to_google_docs(briefing)

        # 4. Google Sheets에 추가
        print("📊 Google Sheets에 추가 중...")
        sheets_link = self.save_to_google_sheets(briefing)

        if github_link or sheets_link:
            print(f"\n✅ 데일리 브리핑이 생성되었습니다!")
            if github_link:
                print(f"📎 GitHub: https://github.com/uuuup-wonjin/portfolio-daily-briefing/tree/main/briefings")
            if sheets_link:
                print(f"📊 Google Sheets: https://docs.google.com/spreadsheets/d/{sheets_link}/edit")
        else:
            print("⚠️  브리핑 생성은 완료했으나 저장 실패")


if __name__ == '__main__':
    briefing = DailyBriefing()
    briefing.run()
