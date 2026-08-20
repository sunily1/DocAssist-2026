# DocAssist 2026

DocAssist는 보고서, 공지, 회의록, 계약서 등 업무 문서의 어려운 표현을 쉬운 업무 표현으로 바꾸고, 원문 위치와 요약·할 일을 함께 보여주는 문서 이해 보조 서비스입니다.

## 주요 기능

- 텍스트 직접 입력 및 PDF·DOCX·TXT 업로드
- 살짝·쉽게·아주 쉽게의 세 단계 변환
- 원문 서식을 유지한 PDF 보기와 변경 위치 강조
- 원문·쉬운말 비교, 문단 요약, 날짜·금액·담당자 추출
- 선택 문서 기반 Q&A와 일반 Q&A
- 온용어 검색, 개인 용어장, 문서함, DOCX 다운로드
- 글자 크기·다크 모드·프로필·관리자 실제 통계

## 구성

```text
Browser (Vue 3 + TypeScript + Vite)
  └─ /api 프록시
      └─ FastAPI
          ├─ PostgreSQL + pgvector
          ├─ PDF.js / PyMuPDF / docx-preview
          ├─ OpenAI 호환 LLM API
          └─ 국립국어원 온용어 API
```

- `frontend/`: 사용자 화면과 PDF·DOCX 뷰어
- `backend/`: API, 인증, 문서 처리, RAG, 관리자 통계
- `backend/app/data/nikl_term_frequency.json`: 로컬에서만 생성하는 말뭉치 집계 빈도(Git 제외)
- `backend/scripts/build_corpus_frequency.py`: 국립국어원 ZIP에서 빈도를 다시 만드는 도구
- `e2e/`: Playwright 화면·기능 테스트

## 로컬 실행 (macOS)

필수 도구는 Python 3.12, Node.js 20 이상, Docker Desktop입니다.

```bash
cd backend
cp env.example .env
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
docker compose up -d db
alembic upgrade head

cd ../frontend
npm ci
cd ..
./dev.sh
```

- 프론트엔드: `http://localhost:3000`
- API 문서: `http://localhost:8000/docs`

`backend/.env`의 `SECRET_KEY`, 관리자 계정, LLM·온용어 설정은 실제 값으로 변경해야 합니다. API 키는 Git에 커밋하지 않습니다.
사용자가 업로드한 문서, 로컬 데이터베이스, 말뭉치 원본·집계 데이터도 Git에서 제외됩니다. CI의 저장소 위생 검사가 금지 파일과 일반적인 비밀키 형식을 자동으로 확인합니다.

## 말뭉치 난이도 재생성

저장소에는 국립국어원 원본 ZIP과 그 가공·집계 데이터를 포함하지 않습니다. 이용 허가를 받은 사용자가 형태 분석 말뭉치와 일상 대화 말뭉치를 로컬에 내려받은 뒤 다음 명령으로 집계 파일을 생성합니다. 생성된 JSON은 `.gitignore`로 Git에서 제외됩니다.

```bash
cd backend
venv/bin/python scripts/build_corpus_frequency.py \
  --morpheme /path/to/NIKL_MP_2025_v1.0.zip \
  --dialogue /path/to/NIKL_DIALOGUE_2025_v1.0.zip
```

단어 난이도는 말뭉치 사용 빈도를 주 기준으로 활용하고, 업무 전문용어 여부를 보조 기준으로 결합합니다. 원본 말뭉치의 이용 조건은 국립국어원 약정을 따릅니다.

## 테스트

```bash
# 백엔드: docassist_test DB가 필요합니다.
cd backend
TEST_DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5454/docassist_test \
  venv/bin/python -m pytest -q

# 프론트엔드
cd ../frontend
npm run build

# 개발 서버 실행 후 E2E
cd ..
npx playwright test
```

GitHub Actions는 프론트 빌드와 백엔드 테스트를 실행합니다. GitHub Pages는 정적 프론트만 제공해 FastAPI·PostgreSQL 기능이 동작하지 않으므로 운영 배포 대상으로 사용하지 않습니다.

## Docker 운영 배포

```bash
cp .env.example .env
# .env의 비밀번호, SECRET_KEY, API 설정 수정
docker compose -f docker-compose.prod.yml up -d --build
```

운영 환경에서는 HTTPS 역방향 프록시를 앞에 두고 `CORS_ORIGINS`를 실제 서비스 주소로 제한해야 합니다. 업로드와 DB 볼륨은 정기적으로 백업합니다.

## 보안·개인정보

- `.env`, 업로드 문서, 로그, 말뭉치 원본은 Git에서 제외합니다.
- 사용자는 본인 문서와 대화만 조회·삭제할 수 있습니다.
- 관리자 화면은 문서 내용이 아닌 운영 통계와 처리 상태를 중심으로 제공합니다.
- AI 변환 결과는 원문과 다를 수 있으므로 최종 업무 적용 전에 원문을 확인해야 합니다.
- 이미 외부에 노출한 API 키는 저장소에서 지우는 것만으로 충분하지 않으며 발급 기관에서 폐기·재발급해야 합니다.

## 현재 제한

- PDF 쉬운말 표시는 원본 좌표를 최대한 유지하지만, 대체 문장이 길면 줄바꿈과 배치가 완전히 같지 않을 수 있습니다.
- 스캔 PDF는 OCR 품질에 따라 텍스트 추출 정확도가 달라집니다.
- LLM 제공 서버의 모델·사용량·장애 상태에 따라 일반 Q&A 품질과 응답 시간이 달라질 수 있습니다.
