@echo off
setlocal

cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo Virtual environment not found at .venv\Scripts\python.exe
  echo Run: python -m venv .venv
  echo Then: .\.venv\Scripts\python.exe -m pip install -r requirements.txt
  exit /b 1
)

if defined OLLAMA_API_KEY (
  echo Using hosted Ollama API with OLLAMA_API_KEY.
) else (
  echo OLLAMA_API_KEY not set. Backend will use local Ollama at http://127.0.0.1:11434/api
)

start "FastAPI Backend" cmd /k ".venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000"
start "Streamlit Frontend" cmd /k ".venv\Scripts\python.exe -m streamlit run frontend/app.py --server.port 8501 --server.fileWatcherType none"

echo Backend starting at http://127.0.0.1:8000
echo Frontend starting at http://127.0.0.1:8501

endlocal
