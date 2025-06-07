#!/bin/bash

# PickEm Pro API Testing Script
echo "=== PickEm Pro API Testing ==="
echo "Testing backend API endpoints..."

BASE_URL="http://localhost:5000"

# Test health endpoint
echo -e "\n1. Testing Health Endpoint:"
curl -s -X GET "$BASE_URL/api/health" | python3 -m json.tool

# Test matches endpoint
echo -e "\n2. Testing Matches Endpoint:"
curl -s -X GET "$BASE_URL/api/matches" | python3 -m json.tool | head -20

# Test optimization status
echo -e "\n3. Testing Optimization Status:"
curl -s -X GET "$BASE_URL/api/optimization/status" | python3 -m json.tool

# Test authentication endpoints
echo -e "\n4. Testing Auth Status:"
curl -s -X GET "$BASE_URL/api/auth/steam/status" | python3 -m json.tool

# Test picks endpoint
echo -e "\n5. Testing Picks Endpoint:"
curl -s -X GET "$BASE_URL/api/picks" | python3 -m json.tool

echo -e "\n=== API Testing Complete ==="

