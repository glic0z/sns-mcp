#!/bin/bash

echo "=========================================="
echo "      SNS MCP Server - Unix Launcher      "
echo "=========================================="

if [ ! -d ".venv" ]; then
    echo "[INFO] Creating Python virtual environment..."
    python3 -m venv .venv
    echo "[INFO] Installing dependencies..."
    .venv/bin/python -m pip install -e .
fi

echo "[INFO] Launching SNS MCP Server..."
.venv/bin/sns-mcp "$@"
