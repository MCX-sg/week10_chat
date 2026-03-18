import requests
import streamlit as st


API_URL = "https://router.huggingface.co/v1/chat/completions"
MODEL_NAME = "meta-llama/Llama-3.2-1B-Instruct"
TEST_MESSAGE = "Hello!"

st.set_page_config(page_title="My AI Chat", layout="wide")

try:
    hf_token = st.secrets["HF_TOKEN"].strip()
except Exception:
    hf_token = ""


def request_hf_test_message(token: str) -> str:
    response = requests.post(
        API_URL,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        json={
            "model": MODEL_NAME,
            "messages": [{"role": "user", "content": TEST_MESSAGE}],
            "max_tokens": 512,
        },
        timeout=60,
    )

    if response.status_code == 401:
        raise ValueError("Invalid Hugging Face token. Check your `HF_TOKEN` secret and try again.")
    if response.status_code == 429:
        raise ValueError("Rate limit reached. Wait a moment and try again.")
    if response.status_code >= 400:
        detail = response.text.strip() or f"HTTP {response.status_code}"
        raise ValueError(f"Hugging Face API error: {detail}")

    data = response.json()
    return data["choices"][0]["message"]["content"]


st.title("My AI Chat")
st.caption("Foundational Part A: send one hardcoded test message to the Hugging Face Inference Router.")

st.write(f"Test message: `{TEST_MESSAGE}`")
st.write(f"Model: `{MODEL_NAME}`")

if not hf_token:
    st.error("Missing `HF_TOKEN` in Streamlit secrets. Add it in deployment settings or `.streamlit/secrets.toml`.")
else:
    try:
        with st.spinner("Sending test message..."):
            assistant_reply = request_hf_test_message(hf_token)
        st.subheader("Model Response")
        st.write(assistant_reply)
    except ValueError as exc:
        st.error(str(exc))
    except requests.RequestException:
        st.error("Network failure while contacting the Hugging Face API. Check your connection and try again.")
    except Exception as exc:
        st.error(f"Unexpected error: {exc}")
