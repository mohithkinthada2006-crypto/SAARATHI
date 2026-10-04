#!/usr/bin/env bash
set -e
docker-compose up -d --build
sleep 10
curl -s http://localhost:8000/health
echo ""
