#!/bin/bash

set -e

# Defaults
IMAGE_NAME="resume-analyzer-api"
TAG="latest"
PORT_MAPPING="9000:8080"

# Help
show_help() {
  echo "Usage: ./run_image.sh [--image <image_name>] [--tag <tag>] [--port <host:container>]"
  echo
  echo "Options:"
  echo "  --image <name>       Docker image name (default: resume-analyzer-api)"
  echo "  --tag <tag>          Docker image tag (default: latest)"
  echo "  --port <mapping>     Port mapping as host:container (default: 9000:8080)"
  echo "  --help               Show this help message"
  exit 0
}

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --image) IMAGE_NAME="$2"; shift ;;
    --tag) TAG="$2"; shift ;;
    --port) PORT_MAPPING="$2"; shift ;;
    --help) show_help ;;
    *) echo "Unknown option: $1"; show_help ;;
  esac
  shift
done

echo "🚀 Running Docker image: $IMAGE_NAME:$TAG"
echo "🔌 Port mapping: $PORT_MAPPING"

docker run -p "$PORT_MAPPING" "$IMAGE_NAME:$TAG"
