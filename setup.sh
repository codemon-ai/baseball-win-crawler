#!/bin/bash

# Baseball Win Crawler Setup Script
# 가상환경 설정 및 의존성 설치 스크립트

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 기본 가상환경 이름
DEFAULT_VENV_NAME="venv"

# 가상환경 이름 설정 (인자가 있으면 사용, 없으면 기본값 또는 입력받기)
if [ "$1" ]; then
    VENV_NAME="$1"
else
    echo -e "${YELLOW}가상환경 이름을 입력하세요 (엔터를 누르면 기본값: $DEFAULT_VENV_NAME):${NC}"
    read USER_VENV_NAME
    VENV_NAME="${USER_VENV_NAME:-$DEFAULT_VENV_NAME}"
fi

echo -e "${GREEN}=== Baseball Win Crawler 환경 설정 시작 ===${NC}"
echo -e "${GREEN}가상환경 이름: $VENV_NAME${NC}"

# Python 버전 확인
echo -e "\n${YELLOW}Python 버전 확인 중...${NC}"
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
    PYTHON_VERSION=$($PYTHON_CMD --version)
    echo -e "${GREEN}✓ $PYTHON_VERSION${NC}"
else
    echo -e "${RED}✗ Python3가 설치되어 있지 않습니다.${NC}"
    exit 1
fi

# 가상환경 생성
echo -e "\n${YELLOW}가상환경 생성 중...${NC}"
if [ -d "$VENV_NAME" ]; then
    echo -e "${YELLOW}기존 가상환경이 존재합니다. 삭제하고 새로 생성하시겠습니까? (y/N)${NC}"
    read -r response
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        rm -rf "$VENV_NAME"
        $PYTHON_CMD -m venv "$VENV_NAME"
        echo -e "${GREEN}✓ 가상환경이 재생성되었습니다.${NC}"
    else
        echo -e "${YELLOW}기존 가상환경을 유지합니다.${NC}"
    fi
else
    $PYTHON_CMD -m venv "$VENV_NAME"
    echo -e "${GREEN}✓ 가상환경이 생성되었습니다.${NC}"
fi

# 가상환경 활성화
echo -e "\n${YELLOW}가상환경 활성화 중...${NC}"
if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
    # Windows
    source "$VENV_NAME/Scripts/activate"
else
    # macOS, Linux
    source "$VENV_NAME/bin/activate"
fi
echo -e "${GREEN}✓ 가상환경이 활성화되었습니다.${NC}"

# pip 업그레이드
echo -e "\n${YELLOW}pip 업그레이드 중...${NC}"
pip install --upgrade pip
echo -e "${GREEN}✓ pip가 업그레이드되었습니다.${NC}"

# 의존성 설치
echo -e "\n${YELLOW}의존성 패키지 설치 중...${NC}"
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    echo -e "${GREEN}✓ 모든 의존성이 설치되었습니다.${NC}"
else
    echo -e "${RED}✗ requirements.txt 파일을 찾을 수 없습니다.${NC}"
    exit 1
fi

# 필요한 디렉토리 생성
echo -e "\n${YELLOW}필요한 디렉토리 생성 중...${NC}"
mkdir -p data logs
echo -e "${GREEN}✓ data, logs 디렉토리가 생성되었습니다.${NC}"

# .gitignore에 가상환경 추가
echo -e "\n${YELLOW}.gitignore 설정 중...${NC}"
if [ -f ".gitignore" ]; then
    if ! grep -q "^$VENV_NAME/" .gitignore 2>/dev/null && [ "$VENV_NAME" != "venv" ]; then
        echo "$VENV_NAME/" >> .gitignore
        echo -e "${GREEN}✓ .gitignore에 $VENV_NAME/이 추가되었습니다.${NC}"
    fi
else
    cat > .gitignore << EOF
# Virtual Environment
venv/
$VENV_NAME/
.env

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python

# Data and Logs
data/
logs/
*.log

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Testing
.pytest_cache/
.coverage
htmlcov/
EOF
    echo -e "${GREEN}✓ .gitignore 파일이 생성되었습니다.${NC}"
fi

# 환경 설정 완료 메시지
echo -e "\n${GREEN}=== 환경 설정 완료! ===${NC}"
echo -e "${YELLOW}다음 명령어로 가상환경을 활성화하세요:${NC}"
if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
    echo -e "${GREEN}source $VENV_NAME/Scripts/activate${NC}"
else
    echo -e "${GREEN}source $VENV_NAME/bin/activate${NC}"
fi
echo -e "\n${YELLOW}프로젝트 실행:${NC}"
echo -e "${GREEN}python main.py --help${NC}"