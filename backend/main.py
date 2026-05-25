import json
import os
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field


OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY", "").strip()
DEFAULT_OLLAMA_BASE_URL = (
    "https://ollama.com/api" if OLLAMA_API_KEY else "http://127.0.0.1:11434/api"
)
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", DEFAULT_OLLAMA_BASE_URL).rstrip("/")
OLLAMA_URL = os.getenv("OLLAMA_URL", f"{OLLAMA_BASE_URL}/generate")
OLLAMA_MODEL = "gemma3:4b"
DEFAULT_SUMMARY_PROMPT = (
    "Write a concise summary of the message in 2 to 3 sentences. "
    "Keep the meaning intact and avoid adding new information."
)


app = FastAPI(title="Message Analyzer API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AnalyzeRequest(BaseModel):
    message: str = Field(..., min_length=1, description="Message to analyze")
    summary_prompt: str = Field(
        default=DEFAULT_SUMMARY_PROMPT,
        min_length=1,
        description="Custom instruction for how the summary should be written",
    )
    model: str = Field(
        default=OLLAMA_MODEL,
        min_length=1,
        description="Ollama model name",
    )


class AnalyzeResponse(BaseModel):
    summary: str
    tone: str
    intent: str
    model: str


def build_prompt(message: str, summary_prompt: str) -> str:
    return f"""
You are an assistant that analyzes user messages.

Tasks:
1. Create a summary using this instruction: "{summary_prompt}"
2. Identify the tone of the message in a short phrase.
3. Identify the intent of the message in a short phrase.

Return valid JSON only with this exact schema:
{{
  "summary": "string",
  "tone": "string",
  "intent": "string"
}}

Message:
\"\"\"
{message}
\"\"\"
""".strip()


def parse_json_response(raw_text: str) -> dict[str, Any]:
    raw_text = raw_text.strip()

    try:
        return json.loads(raw_text)
    except json.JSONDecodeError:
        start = raw_text.find("{")
        end = raw_text.rfind("}")
        if start != -1 and end != -1 and start < end:
            try:
                return json.loads(raw_text[start : end + 1])
            except json.JSONDecodeError as exc:
                raise HTTPException(
                    status_code=502,
                    detail="Model returned invalid JSON.",
                ) from exc
        raise HTTPException(
            status_code=502,
            detail="Model returned an unreadable response.",
        )


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze_message(payload: AnalyzeRequest) -> AnalyzeResponse:
    prompt = build_prompt(payload.message.strip(), payload.summary_prompt.strip())
    headers: dict[str, str] = {}

    if OLLAMA_API_KEY:
        headers["Authorization"] = f"Bearer {OLLAMA_API_KEY}"

    request_body = {
        "model": payload.model.strip(),
        "prompt": prompt,
        "stream": False,
        "format": "json",
    }

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(OLLAMA_URL, json=request_body, headers=headers)
            response.raise_for_status()
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Could not connect to Ollama at {OLLAMA_URL}.",
        ) from exc
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Ollama request failed with status {exc.response.status_code}.",
        ) from exc

    response_data = response.json()
    model_output = response_data.get("response", "")
    parsed = parse_json_response(model_output)

    summary = str(parsed.get("summary", "")).strip()
    tone = str(parsed.get("tone", "")).strip()
    intent = str(parsed.get("intent", "")).strip()

    if not summary or not tone or not intent:
        raise HTTPException(
            status_code=502,
            detail="Model response is missing one or more required fields.",
        )

    return AnalyzeResponse(
        summary=summary,
        tone=tone,
        intent=intent,
        model=payload.model.strip(),
    )
