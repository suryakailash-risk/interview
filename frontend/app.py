import json
import os
from typing import Any

import requests
import streamlit as st


DEFAULT_MODEL = "gemma3:4b"
DEFAULT_SUMMARY_PROMPT = (
    "Write a clear, concise summary of the message in 1 to 2 sentences. "
    "Preserve the original meaning, mention the main request or point, and do not add new information."
)
DEFAULT_OLLAMA_BASE_URL = (
    "https://ollama.com/api"
    if os.getenv("OLLAMA_API_KEY", "").strip()
    else "http://127.0.0.1:11434/api"
)


st.set_page_config(page_title="Message Analyzer", layout="centered")


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
            return json.loads(raw_text[start : end + 1])
        raise ValueError("Model returned an unreadable response.")


def analyze_message(
    message_text: str,
    summary_instruction: str,
    model: str,
    ollama_base_url: str,
    ollama_api_key: str,
) -> dict[str, str]:
    url = f"{ollama_base_url.rstrip('/')}/generate"
    headers: dict[str, str] = {}

    if ollama_api_key.strip():
        headers["Authorization"] = f"Bearer {ollama_api_key.strip()}"

    payload = {
        "model": model,
        "prompt": build_prompt(message_text, summary_instruction),
        "stream": False,
        "format": "json",
    }

    response = requests.post(url, json=payload, headers=headers, timeout=120)
    response.raise_for_status()

    response_data = response.json()
    parsed = parse_json_response(str(response_data.get("response", "")))

    summary = str(parsed.get("summary", "")).strip()
    tone = str(parsed.get("tone", "")).strip()
    intent = str(parsed.get("intent", "")).strip()

    if not summary or not tone or not intent:
        raise ValueError("Model response is missing summary, tone, or intent.")

    return {
        "summary": summary,
        "tone": tone,
        "intent": intent,
        "model": model,
        "url": url,
    }


st.title("Message Analyzer")
st.caption("Analyze a message for summary, tone, and intent directly from Streamlit using the Ollama API.")

with st.sidebar:
    st.subheader("Ollama Settings")
    ollama_base_url = st.text_input("Ollama API base URL", value=DEFAULT_OLLAMA_BASE_URL)
    ollama_api_key = st.text_input(
        "Ollama API key",
        value=os.getenv("OLLAMA_API_KEY", ""),
        type="password",
        help="Leave blank for local Ollama. Set this for hosted Ollama at https://ollama.com/api.",
    )
    model_name = st.text_input("Ollama model", value=DEFAULT_MODEL)

message_header_col, message_info_col = st.columns([12, 1])

with message_header_col:
    st.markdown("**Enter your message**")

with message_info_col:
    show_architecture_note = st.button("i", key="architecture_note_button", help="Why this app uses a direct Ollama call")

if show_architecture_note:
    st.info(
        "FastAPI will not work reliably for this GitHub-based setup, so the app now uses a direct "
        "Streamlit-to-Ollama API call to get the result."
    )

message = st.text_area(
    "Message",
    label_visibility="collapsed",
    height=220,
    placeholder="Paste or type the message you want to analyze...",
)

summary_prompt = st.text_area(
    "Customize the summary instructions",
    value=DEFAULT_SUMMARY_PROMPT,
    height=120,
    help="Control how the summary should be written.",
)

if st.button("Analyze Message", type="primary"):
    if not message.strip():
        st.warning("Please enter a message to analyze.")
    elif not summary_prompt.strip():
        st.warning("Please provide summary instructions.")
    elif not model_name.strip():
        st.warning("Please provide an Ollama model name.")
    elif not ollama_base_url.strip():
        st.warning("Please provide an Ollama API base URL.")
    else:
        with st.spinner("Analyzing message..."):
            try:
                result = analyze_message(
                    message_text=message.strip(),
                    summary_instruction=summary_prompt.strip(),
                    model=model_name.strip(),
                    ollama_base_url=ollama_base_url.strip(),
                    ollama_api_key=ollama_api_key,
                )
            except requests.exceptions.ConnectionError:
                st.error("Could not connect to the Ollama API. Check the base URL and API key.")
            except requests.exceptions.HTTPError as exc:
                detail = f"Ollama request failed with status {exc.response.status_code}."
                try:
                    response_json = exc.response.json()
                    if "error" in response_json:
                        detail = str(response_json["error"])
                except ValueError:
                    pass
                st.error(detail)
            except ValueError as exc:
                st.error(str(exc))
            except requests.exceptions.RequestException as exc:
                st.error(f"Unexpected request error: {exc}")
            else:
                st.subheader("Results")
                st.write(f"**Model:** {result['model']}")
                st.write(f"**API Endpoint:** {result['url']}")
                st.write("**Summary**")
                st.write(result["summary"])
                st.write("**Tone**")
                st.write(result["tone"])
                st.write("**Intent**")
                st.write(result["intent"])
