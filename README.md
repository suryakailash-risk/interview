# Message Analyzer App

This project includes:

- A `FastAPI` backend that sends messages to the `Ollama API`
- A `Streamlit` frontend for entering a message and viewing the analysis
- Support for a user-customizable summary prompt

The app returns:

- Summary
- Tone
- Intent

Default model:

- `gemma3:4b`

## 1. Create a virtual environment

```powershell
python -m venv .venv
```

## 2. Install dependencies

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## 3. Choose Ollama local or hosted

### Local Ollama

Start Ollama locally, then pull the model if needed:

```powershell
ollama pull gemma3:4b
```

### Hosted Ollama API

If you want to use Ollama's hosted API instead of the local app, set `OLLAMA_API_KEY` before starting the backend. When this variable is present, the backend uses `https://ollama.com/api`.

```powershell
$env:OLLAMA_API_KEY="your_api_key"
```

## 4. Start the FastAPI backend

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload
```

The backend will run at:

- `http://localhost:8000`

## 5. Start the Streamlit frontend

Open a new terminal and run:

```powershell
.\.venv\Scripts\python.exe -m streamlit run frontend/app.py
```

The frontend will usually open at:

- `http://localhost:8501`

## Quick Start Scripts

You can also use the included PowerShell scripts:

```powershell
.\run_backend.ps1
.\run_frontend.ps1
```

Or launch both in separate terminal windows:

```powershell
.\run_app.ps1
```

If you prefer the batch launcher, set `OLLAMA_API_KEY` first and then run:

```powershell
$env:OLLAMA_API_KEY="your_api_key"
.\run_app.bat
```

## API Endpoints

### `GET /health`

Returns a simple health response.

### `POST /analyze`

Example request body:

```json
{
  "message": "Can we move tomorrow's meeting to the afternoon? I have a conflict in the morning.",
  "summary_prompt": "Summarize the message in one sentence.",
  "model": "gemma3:4b"
}
```

Example response:

```json
{
  "summary": "The sender wants to reschedule tomorrow's meeting to the afternoon because of a morning conflict.",
  "tone": "polite and practical",
  "intent": "requesting a meeting reschedule",
  "model": "gemma3:4b"
}
```

## Notes

- Without `OLLAMA_API_KEY`, the backend uses local Ollama at `http://127.0.0.1:11434/api`
- With `OLLAMA_API_KEY`, the backend uses hosted Ollama at `https://ollama.com/api`
- The app asks Ollama to return JSON only
- If the model is unavailable, the frontend will show an error message
