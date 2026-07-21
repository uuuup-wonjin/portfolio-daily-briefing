# 📅 포트폴리오 데일리 브리핑 자동화 스크립트

Notion 데이터를 조회하여 Google Docs에 자동으로 브리핑을 작성합니다.

---

## 📋 스크립트 목록

### 1. `daily_briefing.py` (GitHub Actions 자동 실행)
**실행 시간**: 매일 오전 8시 (월-금)

**기능**:
- Notion에서 포트폴리오 데이터 조회
- 매일 브리핑 자동 생성
- Google Docs에 저장 및 공유 링크 생성

**수동 실행**:
```bash
python scripts/daily_briefing.py
```

**출력**:
```
✅ Google Docs 생성 완료
📎 링크: https://docs.google.com/document/d/{doc_id}/edit?usp=sharing
```

---

## 🔧 환경 설정

### 필수 환경 변수

#### Notion API
```bash
export NOTION_TOKEN='ntn_...'
export NOTION_DATABASE_ID='...'  # 포트폴리오 데이터 조회용
```

#### Google Docs API
```bash
export GOOGLE_SERVICE_ACCOUNT_JSON='{"type":"service_account",...}'
export GOOGLE_DOCS_FOLDER_ID='...'  # (선택) Google Drive 폴더 ID
```

### 환경 변수 설정 방법

#### Step 1: Google Cloud 프로젝트 설정
1. [Google Cloud Console](https://console.cloud.google.com/) 열기
2. 새 프로젝트 생성: "Portfolio Daily Briefing"
3. Google Docs API 활성화
4. Google Drive API 활성화

#### Step 2: 서비스 계정 키 생성
1. "서비스 계정" → "서비스 계정 만들기"
2. 이름: "portfolio-daily-briefing"
3. "키 추가" → "새 키 생성" (JSON 형식)
4. 다운로드된 JSON 파일 내용을 `GOOGLE_SERVICE_ACCOUNT_JSON`으로 설정

#### Step 3: GitHub Secrets 설정
```
NOTION_TOKEN: 노션 토큰
NOTION_DATABASE_ID: 데이터베이스 ID
GOOGLE_SERVICE_ACCOUNT_JSON: 서비스 계정 JSON (전체 내용)
GOOGLE_DOCS_FOLDER_ID: (선택) Google Drive 폴더 ID
```

### .env 파일 (로컬만 사용)
```
NOTION_TOKEN=ntn_...
NOTION_DATABASE_ID=...
GOOGLE_SERVICE_ACCOUNT_JSON={"type":"service_account",...}
GOOGLE_DOCS_FOLDER_ID=...
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
   └─ Google Docs 저장 (공유 링크 생성)
```

### 로컬 (수동)
```bash
# 환경 변수 설정
export NOTION_TOKEN='...'
export NOTION_DATABASE_ID='...'
export GOOGLE_SERVICE_ACCOUNT_JSON='...'

# 실행
python scripts/daily_briefing.py
```

---

## 📝 Notion 포트폴리오 DB 필드

| 필드명 | 타입 | 설명 |
|--------|------|------|
| Name | Title | 작업 제목 |
| 상태 | Select | COMPLETED / PENDING / IN_PROGRESS |
| 우선순위 | Select | HIGH / MEDIUM / LOW |
| 생성일 | Date | 작업 생성 일자 |
| 태그 | Multi-select | TODAY / UUUUP / 등 |

---

## 🐛 문제 해결

### 1. "모듈을 찾을 수 없음" 오류
```bash
pip install -r requirements.txt
```

### 2. Notion 401 오류
- NOTION_TOKEN이 올바른지 확인
- 토큰이 만료되었을 수 있음 → 재발급

### 3. Google Docs API 오류
- `GOOGLE_SERVICE_ACCOUNT_JSON` 형식 확인
- Google Docs/Drive API 활성화 확인

### 4. "Google Docs API 사용 불가" 오류
- GitHub Secrets에서 `GOOGLE_SERVICE_ACCOUNT_JSON` 확인
- JSON 전체 내용이 저장되었는지 확인

---

## 📊 로그

### GitHub Actions 로그
```
https://github.com/uuuup-wonjin/portfolio-daily-briefing
→ Actions 탭
→ 📅 데일리 브리핑 자동화 선택
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
- ✅ 서비스 계정 키 정기적으로 갱신

---

## 📞 지원

- GitHub Issues: 버그 보고
- Email: roytae@gmail.com

---

업데이트: 2026-07-22 (Google Docs API로 변경)
