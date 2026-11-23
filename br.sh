#!/usr/bin/env bash
set -e

docker stop $(docker ps -q --filter "ancestor=malayalam-game-novnc") 2>/dev/null || true

docker build -t malayalam-game-novnc .

docker run --rm \
  -p 127.0.0.1:6080:6080 \
  -p 127.0.0.1:8090:8090 \
  -v "$(pwd)":/app \
  malayalam-game-novnc