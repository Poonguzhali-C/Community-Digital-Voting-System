@echo off
REM Requires: Java 11+, Node.js, and the backend running on http://localhost:8000
call npm install -g @openapitools/openapi-generator-cli
call openapi-generator-cli generate -i http://localhost:8000/openapi.json -g python -o voting_sdk
echo SDK generated in voting_sdk
