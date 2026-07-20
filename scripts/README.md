# 📅 포트폴리오 데일리 브리핑 자동화 스크립트

자동화된 포트폴리오 브리핑 시스템의 Python 스크립트 모음입니다.

---

## 📋 스크립트 목록

### 1. `daily_briefing.py` (GitHub Actions 자동 실행)
**실행 시간**: 매일 오전 8시 (월-금)

**기능**:
- Notion에서 포트폴리오 데이터 조회
- 매일 브리핑 생성
- Notion 데이터베이스에 저장
- Slack DM 발송
- 이메일 발송

**수동 실행**:
```bash
python scripts/daily_briefing.py
```

---

### 2. `weekly_summary_to_nlm.py` (GitHub Actions 자동 실행)
**실행 시간**: 매주 일요일 오전 8시

**기능**:
- Notion에서 지난주 월-금 브리핑 조회
- 통계 계산 (완료율, 항목수 등)
- 주간 요약 생성
- Notion에 주간 요약 저장

**수동 실행**:
```bash
python scripts/weekly_summary_to_nlm.py
```

---

### 3. `sync_weekly_summary_to_nlm.py` (로컬 실행)
**실행 시간**: 필요할 때 수동 실행

**기능**:
- Notion에서 최신 주간 요약 조회
- NLM 형식으로 변환
- 사용자 화면에 표시
- 클립보드에 복사 (macOS)
- 수동 저장 안내

**사용 방법** (로컬 환경):
```bash
# 환경 변수 설정
export NOTION_TOKEN='your_token_here'
export NOTION_BRIEFING_DB_ID='your_db_id_here'

# 실행
python scripts/sync_weekly_summary_to_nlm.py
```

또는 Claude Code에서:
```
@Claude sync_weekly_summary_to_nlm.py 실행해줘
```

---

## 🔧 환경 설정

### 필수 환경 변수

```bash
# Notion API
export NOTION_TOKEN='ntn_...'
export NOTION_DATABASE_ID='...'           # 포트폴리오 데이터 조회용
export NOTION_BRIEFING_DB_ID='...'        # 브리핑 저장용

# Slack
export SLACK_BOT_TOKEN='xoxb-...'
export SLACK_CHANNEL_ID='C0B8HCXAD7V'

# Gmail (발송)
export SMTP_EMAIL='roy.t@hyochang.com'
export SMTP_PASSWORD='16자_앱_비밀번호'
export RECIPIENT_EMAIL='roy.t@hyochang.com'

# NLM (향후 자동화용)
export NLM_NOTEBOOK_ID='...'
```

### .env 파일 (로컬만 사용)
```
# .env 파일 생성 (커밋하지 말 것!)
NOTION_TOKEN=ntn_...
NOTION_DATABASE_ID=...
NOTION_BRIEFING_DB_ID=...
SLACK_BOT_TOKEN=xoxb-...
SLACK_CHANNEL_ID=C0B8HCXAD7V
SMTP_EMAIL=roy.t@hyochang.com
SMTP_PASSWORD=16자_앱_비밀번호
RECIPIENT_EMAIL=roy.t@hyochang.com
```

로드 방법:
```python
from dotenv import load_dotenv
load_dotenv()
```

---

## 📊 실행 흐름

### GitHub Actions (자동)
```
1️⃣ 매일 08:00 KST
   ↓
2️⃣ daily_briefing.py 실행
   ├─ Notion 데이터 조회
   ├─ 브리핑 생성
   ├─ Notion 저장
   ├─ Slack 발송
   └─ 이메일 발송
   
3️⃣ 매주 일요일 08:00 KST
   ↓
4️⃣ weekly_summary_to_nlm.py 실행
   ├─ 지난주 데이터 조회
   ├─ 요약 생성
   └─ Notion 저장
```

### 로컬 (수동)
```
1️⃣ sync_weekly_summary_to_nlm.py 실행
   ↓
2️⃣ Notion에서 최신 요약 조회
   ↓
3️⃣ 클립보드에 복사
   ↓
4️⃣ NLM 노트북에 수동 붙여넣기
```

---

## 📝 Notion 데이터베이스 필드

### 포트폴리오 DB (조회용)
| 필드명 | 타입 | 설명 |
|--------|------|------|
| Name | Title | 작업 제목 |
| 상태 | Select | COMPLETED / PENDING / IN_PROGRESS |
| 우선순위 | Select | HIGH / MEDIUM / LOW |
| 생성일 | Date | 작업 생성 일자 |
| 태그 | Multi-select | TODAY / UUUUP / 등 |

### 브리핑 DB (저장용)
| 필드명 | 타입 | 설명 |
|--------|------|------|
| 제목 | Title | 브리핑 날짜 (자동) |
| 날짜 | Date | 브리핑 생성 날짜 |
| 완료항목 | Number | 어제 완료 항목 수 |
| 계획항목 | Number | 오늘 계획 항목 수 |
| 미실행항목 | Number | 미실행 항목 수 |
| 내용 | Rich Text | 브리핑 전문 |

---

## 🐛 문제 해결

### 1. "모듈을 찾을 수 없음" 오류
```bash
pip install -r requirements.txt
```

### 2. Notion 401 오류
- NOTION_TOKEN이 올바른지 확인
- 토큰이 만료되었을 수 있음 → 재발급

### 3. 이메일 발송 실패
- Gmail 2단계 인증 확인
- 앱 비밀번호가 정확한지 확인 (공백 제거)

### 4. Slack 메시지 미발송
- SLACK_BOT_TOKEN 확인
- 봇이 채널에 초대되었는지 확인

---

## 📊 로그

### GitHub Actions 로그
```
https://github.com/uuuup-wonjin/portfolio-daily-briefing
→ Actions 탭
→ 워크플로우 선택
→ 실행 로그 확인
```

### 로컬 로그
```bash
python scripts/daily_briefing.py 2>&1 | tee briefing.log
```

---

## 🔐 보안

- ⚠️ `.env` 파일을 `.gitignore`에 추가
- ⚠️ 토큰을 GitHub에 커밋하지 말 것
- ✅ GitHub Secrets에서만 관리
- ✅ 정기적으로 토큰 갱신 (3개월마다)

---

## 🚀 다음 단계

1. GitHub Secrets 설정
2. 첫 테스트 실행 (수동)
3. 내일 아침 8시 자동 실행 모니터링
4. Notion에서 저장된 브리핑 확인

---

## 📞 지원

- GitHub Issues: 버그 보고
- GitHub Discussions: 기능 요청
- Email: roytae@gmail.com

---

생성: 2026-07-21
