import requests
import streamlit as st


API_URL = "http://localhost:8000/analyze"
DEFAULT_MODEL = "gemma3:4b"
DEFAULT_SUMMARY_PROMPT = (
    "Write a clear, concise summary of the message in 1 to 2 sentences. "
    "Preserve the original meaning, mention the main request or point, and do not add new information."
)


st.set_page_config(page_title="Message Analyzer", layout="centered")

st.title("Message Analyzer")
st.caption("Analyze a message for summary, tone, and intent using the Ollama API with FastAPI.")

message = st.text_area(
    "Enter your message",
    height=220,
    placeholder="Paste or type the message you want to analyze...",
)

summary_prompt = st.text_area(
    "Customize the summary instructions",
    value=DEFAULT_SUMMARY_PROMPT,
    height=120,
    help="Control how the summary should be written.",
)

model_name = st.text_input("Ollama model", value=DEFAULT_MODEL)


def analyze(message_text: str, summary_instruction: str, model: str) -> dict:
    payload = {
        "message": message_text,
        "summary_prompt": summary_instruction,
        "model": model,
    }
    response = requests.post(API_URL, json=payload, timeout=90)
    response.raise_for_status()
    return response.json()


if st.button("Analyze Message", type="primary"):
    if not message.strip():
        st.warning("Please enter a message to analyze.")
    elif not summary_prompt.strip():
        st.warning("Please provide summary instructions.")
    elif not model_name.strip():
        st.warning("Please provide an Ollama model name.")
    else:
        with st.spinner("Analyzing message..."):
            try:
                result = analyze(message.strip(), summary_prompt.strip(), model_name.strip())
            except requests.exceptions.ConnectionError:
                st.error("Could not connect to the FastAPI backend. Make sure it is running on port 8000.")
            except requests.exceptions.HTTPError as exc:
                detail = "Request failed."
                try:
                    detail = exc.response.json().get("detail", detail)
                except ValueError:
                    pass
                st.error(detail)
            except requests.exceptions.RequestException as exc:
                st.error(f"Unexpected request error: {exc}")
            else:
                st.subheader("Results")
                st.write(f"**Model:** {result['model']}")
                st.write("**Summary**")
                st.write(result["summary"])
                st.write("**Tone**")
                st.write(result["tone"])
                st.write("**Intent**")
                st.write(result["intent"])
