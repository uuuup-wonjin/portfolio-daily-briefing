#!/usr/bin/env python3
"""
포트폴리오 프로젝트 데일리 브리핑 자동화
- Notion에서 데이터 조회
- 브리핑 생성 후 Notion에 저장
- Slack과 이메일로 발송
"""

import os
import json
import smtplib
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import requests
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError


class DailyBriefing:
    def __init__(self):
        self.notion_token = os.getenv('NOTION_TOKEN')
        self.notion_db_id = os.getenv('NOTION_DATABASE_ID')
        self.briefing_db_id = os.getenv('NOTION_BRIEFING_DB_ID')  # 브리핑 저장용
        self.slack_token = os.getenv('SLACK_BOT_TOKEN')
        self.slack_channel = os.getenv('SLACK_CHANNEL_ID')
        self.smtp_email = os.getenv('SMTP_EMAIL')
        self.smtp_password = os.getenv('SMTP_PASSWORD')
        self.recipient_email = os.getenv('RECIPIENT_EMAIL')

        self.slack_client = WebClient(token=self.slack_token)
        self.notion_headers = {
            'Authorization': f'Bearer {self.notion_token}',
            'Notion-Version': '2022-06-28',
            'Content-Type': 'application/json'
        }

    def get_notion_data(self):
        """Notion 데이터베이스에서 오늘/어제 항목 조회"""
        try:
            url = f'https://api.notion.com/v1/databases/{self.notion_db_id}/query'

            # 쿼리: 최근 30일 데이터
            payload = {
                "filter": {
                    "property": "생성일",
                    "date": {
                        "past_week": {}
                    }
                },
                "sorts": [
                    {
                        "property": "생성일",
                        "direction": "descending"
                    }
                ]
            }

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

    def send_slack(self, message):
        """Slack으로 메시지 발송"""
        try:
            self.slack_client.chat_postMessage(
                channel=self.slack_channel,
                text=message
            )
            print("✅ Slack 발송 완료")
        except SlackApiError as e:
            print(f"❌ Slack 발송 실패: {e}")

    def save_to_notion(self, briefing_text, data):
        """생성된 브리핑을 Notion 데이터베이스에 저장"""
        try:
            url = 'https://api.notion.com/v1/pages'

            # 브리핑 날짜
            briefing_date = datetime.now().strftime('%Y-%m-%d')

            payload = {
                'parent': {
                    'database_id': self.briefing_db_id
                },
                'properties': {
                    '제목': {
                        'title': [
                            {
                                'text': {
                                    'content': f'📅 데일리 브리핑 - {briefing_date}'
                                }
                            }
                        ]
                    },
                    '날짜': {
                        'date': {
                            'start': briefing_date
                        }
                    },
                    '완료항목': {
                        'number': len(data.get('yesterday', []))
                    },
                    '계획항목': {
                        'number': len(data.get('today', []))
                    },
                    '미실행항목': {
                        'number': len(data.get('pending', []))
                    },
                    '내용': {
                        'rich_text': [
                            {
                                'text': {
                                    'content': briefing_text
                                }
                            }
                        ]
                    }
                }
            }

            response = requests.post(url, json=payload, headers=self.notion_headers)
            response.raise_for_status()

            print("✅ Notion에 브리핑 저장 완료")
            return True

        except Exception as e:
            print(f"❌ Notion 저장 실패: {e}")
            return False

    def send_email(self, message):
        """이메일로 발송"""
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"📅 데일리 브리핑 - {datetime.now().strftime('%Y-%m-%d')}"
            msg['From'] = self.smtp_email
            msg['To'] = self.recipient_email

            # HTML 버전 생성
            html = f"""
            <html>
              <body style="font-family: Arial; line-height: 1.6;">
                <h2>📅 포트폴리오 프로젝트 데일리 브리핑</h2>
                <pre style="background: #f5f5f5; padding: 15px; border-radius: 5px;">
{message}
                </pre>
                <hr>
                <small>이 메일은 자동으로 생성되었습니다. Notion에도 저장됩니다.</small>
              </body>
            </html>
            """

            part = MIMEText(html, 'html')
            msg.attach(part)

            # SMTP 발송
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                server.login(self.smtp_email, self.smtp_password)
                server.send_message(msg)

            print("✅ 이메일 발송 완료")

        except Exception as e:
            print(f"❌ 이메일 발송 실패: {e}")

    def run(self):
        """전체 브리핑 프로세스 실행"""
        print("🚀 데일리 브리핑 자동화 시작...")

        # 1. Notion 데이터 조회
        print("📊 Notion 데이터 조회 중...")
        data = self.get_notion_data()

        # 2. 브리핑 생성
        print("📝 브리핑 생성 중...")
        briefing = self.generate_briefing(data)

        # 3. Notion에 저장
        print("💾 Notion에 저장 중...")
        self.save_to_notion(briefing, data)

        # 4. 발송
        print("📤 Slack/이메일 발송 중...")
        self.send_slack(briefing)
        self.send_email(briefing)

        print("✅ 데일리 브리핑 완료!")


if __name__ == '__main__':
    briefing = DailyBriefing()
    briefing.run()
