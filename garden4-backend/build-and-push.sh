#!/bin/bash

# Docker Hub 사용자명
DOCKER_USER="junho85"
IMAGE_NAME="garden4"

# 스크립트가 있는 디렉토리를 기준으로 설정
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 현재 날짜/시간으로 태그 생성
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# 색상 코드
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Docker Hub 로그인 확인
echo "Checking Docker Hub authentication..."
if ! docker pull hello-world:latest > /dev/null 2>&1; then
    echo -e "${YELLOW}Warning: Not logged in to Docker Hub or network issue${NC}"
    echo "Please run 'docker login' first"
    exit 1
fi
echo -e "${GREEN}✓ Docker Hub authentication OK${NC}"

echo ""
echo "Building multi-platform Docker image..."
echo "Build directory: $SCRIPT_DIR"
echo "Platforms: linux/amd64, linux/arm64"
echo "Tags: latest, $TIMESTAMP"
echo ""

# buildx 빌더 생성 (이미 있으면 무시)
docker buildx create --name multiplatform --use 2>/dev/null || true

# 멀티 플랫폼 빌드 및 푸시
if docker buildx build \
  --platform linux/amd64,linux/arm64 \
  --tag $DOCKER_USER/$IMAGE_NAME:latest \
  --tag $DOCKER_USER/$IMAGE_NAME:$TIMESTAMP \
  --push \
  "$SCRIPT_DIR"; then
    
    echo ""
    echo -e "${GREEN}✓ Build and push completed successfully!${NC}"
    echo "Images pushed:"
    echo "  $DOCKER_USER/$IMAGE_NAME:latest"
    echo "  $DOCKER_USER/$IMAGE_NAME:$TIMESTAMP"
else
    echo ""
    echo -e "${RED}✗ Build or push failed!${NC}"
    echo "Please check the error message above."
    echo ""
    echo "Common issues:"
    echo "1. Not logged in to Docker Hub: run 'docker login'"
    echo "2. Repository doesn't exist: create it at https://hub.docker.com/"
    echo "3. No push permissions: check your Docker Hub access"
    exit 1
fi