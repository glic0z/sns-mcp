@echo off
echo ==========================================
echo       SNS MCP Server - Windows Launcher
echo ==========================================

IF NOT EXIST ".venv" (
    echo [INFO] Creating Python virtual environment...
    python -m venv .venv
    echo [INFO] Installing dependencies...
    .venv\Scripts\python.exe -m pip install -e .
)

echo [INFO] Launching SNS MCP Server...
.venv\Scripts\sns-mcp.exe %*
