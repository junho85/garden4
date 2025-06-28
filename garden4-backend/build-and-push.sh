#!/bin/bash

# Docker Hub 사용자명
DOCKER_USER="junho85"
IMAGE_NAME="garden4"

# 스크립트가 있는 디렉토리를 기준으로 설정
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 현재 날짜/시간으로 태그 생성
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "Building multi-platform Docker image..."
echo "Build directory: $SCRIPT_DIR"
echo "Platforms: linux/amd64, linux/arm64"
echo "Tags: latest, $TIMESTAMP"

# buildx 빌더 생성 (이미 있으면 무시)
docker buildx create --name multiplatform --use 2>/dev/null || true

# 멀티 플랫폼 빌드 및 푸시
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  --tag $DOCKER_USER/$IMAGE_NAME:latest \
  --tag $DOCKER_USER/$IMAGE_NAME:$TIMESTAMP \
  --push \
  "$SCRIPT_DIR"

echo "Build and push completed!"
echo "Images pushed:"
echo "  $DOCKER_USER/$IMAGE_NAME:latest"
echo "  $DOCKER_USER/$IMAGE_NAME:$TIMESTAMP"