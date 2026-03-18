import requests
import streamlit as st


API_URL = "https://router.huggingface.co/v1/chat/completions"
MODEL_NAME = "meta-llama/Llama-3.2-1B-Instruct"

st.set_page_config(page_title="My AI Chat", layout="wide")

try:
    hf_token = st.secrets["HF_TOKEN"].strip()
except Exception:
    hf_token = ""


def request_hf_chat(token: str, messages: list[dict[str, str]]) -> str:
    response = requests.post(
        API_URL,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        json={
            "model": MODEL_NAME,
            "messages": messages,
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


if "messages" not in st.session_state:
    st.session_state.messages = []


st.title("My AI Chat")
st.caption("Part B: multi-turn chat using native Streamlit chat components and full conversation history.")

st.write(f"Model: `{MODEL_NAME}`")

if not hf_token:
    st.error("Missing `HF_TOKEN` in Streamlit secrets. Add it in deployment settings or `.streamlit/secrets.toml`.")
else:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    prompt = st.chat_input("Send a message")

    if prompt:
        user_message = {"role": "user", "content": prompt}
        st.session_state.messages.append(user_message)

        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            try:
                with st.spinner("Thinking..."):
                    assistant_reply = request_hf_chat(hf_token, st.session_state.messages)
                st.markdown(assistant_reply)
            except ValueError as exc:
                assistant_reply = f"Error: {exc}"
                st.error(str(exc))
            except requests.RequestException:
                assistant_reply = "Error: Network failure while contacting the Hugging Face API. Check your connection and try again."
                st.error("Network failure while contacting the Hugging Face API. Check your connection and try again.")
            except Exception as exc:
                assistant_reply = f"Error: Unexpected error: {exc}"
                st.error(f"Unexpected error: {exc}")

        st.session_state.messages.append({"role": "assistant", "content": assistant_reply})
