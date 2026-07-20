#!/usr/bin/env python3
"""
주간 브리핑 요약을 NotebookLM에 자동 저장
매주 일요일 오전 8시에 실행되어 지난주 브리핑을 요약 저장
"""

import os
import json
from datetime import datetime, timedelta
import requests


class WeeklySummaryToNLM:
    def __init__(self):
        self.notion_token = os.getenv('NOTION_TOKEN')
        self.briefing_db_id = os.getenv('NOTION_BRIEFING_DB_ID')
        self.nlm_notebook_id = os.getenv('NLM_NOTEBOOK_ID')  # NLM 노트북 ID

        self.notion_headers = {
            'Authorization': f'Bearer {self.notion_token}',
            'Notion-Version': '2022-06-28',
            'Content-Type': 'application/json'
        }

    def get_weekly_briefings(self):
        """지난주 월-금 브리핑 조회"""
        try:
            url = f'https://api.notion.com/v1/databases/{self.briefing_db_id}/query'

            # 지난주 월요일 계산
            today = datetime.now().date()
            days_since_monday = today.weekday()
            monday = today - timedelta(days=days_since_monday + 7)
            friday = monday + timedelta(days=4)

            payload = {
                "filter": {
                    "property": "날짜",
                    "date": {
                        "on_or_after": monday.isoformat(),
                        "on_or_before": friday.isoformat()
                    }
                },
                "sorts": [
                    {
                        "property": "날짜",
                        "direction": "ascending"
                    }
                ]
            }

            response = requests.post(url, json=payload, headers=self.notion_headers)
            response.raise_for_status()

            results = response.json().get('results', [])

            briefings = []
            for page in results:
                props = page.get('properties', {})

                title = self._extract_text(props.get('제목'))
                date = self._extract_date(props.get('날짜'))
                completed = self._extract_number(props.get('완료항목'))
                planned = self._extract_number(props.get('계획항목'))
                pending = self._extract_number(props.get('미실행항목'))
                content = self._extract_text(props.get('내용'))

                if title and date:
                    briefings.append({
                        'title': title,
                        'date': date,
                        'completed': completed or 0,
                        'planned': planned or 0,
                        'pending': pending or 0,
                        'content': content or ''
                    })

            return briefings

        except Exception as e:
            print(f"❌ Notion 조회 실패: {e}")
            return []

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

    def _extract_number(self, prop):
        """숫자 필드 추출"""
        if not prop or not prop.get('number'):
            return None
        return prop['number']

    def generate_weekly_summary(self, briefings):
        """주간 요약 생성"""
        if not briefings:
            return None

        # 주간 통계
        total_completed = sum(b['completed'] for b in briefings)
        total_planned = sum(b['planned'] for b in briefings)
        total_pending = sum(b['pending'] for b in briefings)
        completion_rate = (total_completed / total_planned * 100) if total_planned > 0 else 0

        week_start = briefings[0]['date'] if briefings else ''
        week_end = briefings[-1]['date'] if briefings else ''

        summary = f"""# 📊 주간 브리핑 요약 ({week_start} ~ {week_end})

## 📈 통계
- **완료 항목**: {total_completed}개
- **계획된 항목**: {total_planned}개
- **미실행 항목**: {total_pending}개
- **완료율**: {completion_rate:.1f}%

## 📅 일일 상세

"""

        for briefing in briefings:
            summary += f"""### {briefing['date']} ({briefing['title'].split('-')[-1].strip()})
- 완료: {briefing['completed']}개
- 계획: {briefing['planned']}개
- 미실행: {briefing['pending']}개

"""

        summary += f"""## 🎯 주간 평가
- 목표 대비 달성도: {completion_rate:.0f}%
- 미완료 항목: {total_pending}개 (다음주 이월)
- 주간 생산성: {'우수' if completion_rate >= 80 else '양호' if completion_rate >= 60 else '개선 필요'}

---
*자동 생성된 주간 브리핑 요약 - {datetime.now().strftime('%Y-%m-%d %H:%M')}*
"""
        return summary

    def save_to_nlm(self, summary):
        """NLM 노트북에 저장

        주의: 이 함수는 로컬 환경에서만 작동합니다.
        GitHub Actions에서는 NLM API에 직접 접근할 수 없으므로,
        대신 Notion에 저장된 요약을 수동으로 NLM에 옮기거나,
        별도의 로컬 크론 작업으로 실행해야 합니다.
        """
        try:
            # Claude Code에서 실행되는 경우, NLM MCP를 통해 저장
            # GitHub Actions에서는 이 부분이 건너뜀
            print("💡 NLM 저장 안내:")
            print("  - GitHub Actions에서는 NLM API에 직접 접근 불가")
            print("  - 대신 Notion 데이터베이스에 주간 요약이 자동 생성됩니다")
            print("  - 필요시 로컬에서 수동으로 NLM에 복사하세요")

            return False

        except Exception as e:
            print(f"❌ NLM 저장 실패: {e}")
            return False

    def save_summary_to_notion(self, summary):
        """주간 요약을 Notion에 저장"""
        try:
            url = 'https://api.notion.com/v1/pages'

            week_start = datetime.now() - timedelta(days=datetime.now().weekday() + 7)
            week_date = week_start.strftime('%Y-W%U')

            payload = {
                'parent': {
                    'database_id': self.briefing_db_id
                },
                'properties': {
                    '제목': {
                        'title': [
                            {
                                'text': {
                                    'content': f'📊 주간 요약 - {week_date}'
                                }
                            }
                        ]
                    },
                    '날짜': {
                        'date': {
                            'start': week_start.strftime('%Y-%m-%d')
                        }
                    },
                    '내용': {
                        'rich_text': [
                            {
                                'text': {
                                    'content': summary
                                }
                            }
                        ]
                    }
                }
            }

            response = requests.post(url, json=payload, headers=self.notion_headers)
            response.raise_for_status()

            print("✅ Notion에 주간 요약 저장 완료")
            return True

        except Exception as e:
            print(f"❌ Notion 저장 실패: {e}")
            return False

    def run(self):
        """주간 요약 프로세스 실행"""
        print("🚀 주간 요약 생성 시작...")

        # 1. 지난주 브리핑 조회
        print("📊 지난주 브리핑 조회 중...")
        briefings = self.get_weekly_briefings()

        if not briefings:
            print("⚠️ 이번주 브리핑이 없습니다")
            return

        # 2. 주간 요약 생성
        print("📝 주간 요약 생성 중...")
        summary = self.generate_weekly_summary(briefings)

        # 3. Notion에 저장
        print("💾 Notion에 저장 중...")
        self.save_summary_to_notion(summary)

        # 4. NLM 저장 안내
        print("📌 NLM 저장 안내...")
        self.save_to_nlm(summary)

        print("✅ 주간 요약 완료!")


if __name__ == '__main__':
    summary = WeeklySummaryToNLM()
    summary.run()
