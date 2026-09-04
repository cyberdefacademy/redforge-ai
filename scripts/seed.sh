#!/bin/bash
set -e
curl -s http://localhost:8000/api/v1/health | jq .
echo "Seeding via API — login first"
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login -H "Content-Type: application/json" -d '{"email":"admin@redforge.local","password":"RedForge!2026"}' | jq -r .access_token)
echo "Token: ${TOKEN:0:20}..."
curl -s http://localhost:8000/api/v1/engagements -H "Authorization: Bearer $TOKEN" | jq .
