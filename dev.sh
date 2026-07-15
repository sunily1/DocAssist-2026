#!/bin/bash

# 스크립트를 어느 위치에서 실행해도 프로젝트 루트를 기준으로 동작합니다.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR" || exit 1

# 색상 정의
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}DocAssist 개발 서버를 시작합니다...${NC}"

# 종료 시 프로세스 정리 함수
cleanup() {
    echo -e "\n${BLUE}서버를 종료합니다...${NC}"
    if [ -n "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null
    fi
    if [ -n "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null
    fi
    exit
}

# Ctrl+C 시그널 캡처
trap cleanup SIGINT SIGTERM

# 백엔드 시작
echo -e "${GREEN}[Backend] 시작 중... (Port: 8000)${NC}"
cd backend
if [ -d "venv" ]; then
    source venv/bin/activate
    if ! command -v uvicorn >/dev/null 2>&1; then
        echo "오류: uvicorn이 설치되어 있지 않습니다. (backend/requirements.txt 설치 필요)"
        exit 1
    fi
    WATCHFILES_FORCE_POLLING=1 uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 > ../backend.log 2>&1 &
    BACKEND_PID=$!
    echo -e "${GREEN}[Backend] PID: $BACKEND_PID${NC}"
else
    echo "오류: backend/venv 가상환경을 찾을 수 없습니다."
    exit 1
fi
cd ..

# 프론트엔드 시작
echo -e "${GREEN}[Frontend] 시작 중... (Port: 3000)${NC}"
cd frontend
if [ ! -d "node_modules" ]; then
    echo "의존성 설치 중... (frontend/node_modules 없음)"
    npm install
fi
npm run dev -- --port 3000 > ../frontend.log 2>&1 &
FRONTEND_PID=$!
echo -e "${GREEN}[Frontend] PID: $FRONTEND_PID${NC}"
cd ..

echo -e "${BLUE}모든 서버가 실행되었습니다.${NC}"
echo -e "Backend: http://localhost:8000/docs"
echo -e "Frontend: http://localhost:3000"
echo -e "종료하려면 Ctrl+C를 누르세요."

# 자식 프로세스 대기
wait
