from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import requests
import streamlit as st


APP_DIR = Path(__file__).parent
MEMORY_PATH = APP_DIR / "memory.json"
LOG_PATH = APP_DIR / "ai_interaction_log.md"
CHATS_DIR = APP_DIR / "chats"
API_URL = "https://router.huggingface.co/v1/chat/completions"
MODEL_NAME = "meta-llama/Llama-3.2-1B-Instruct"


st.set_page_config(page_title="Week 10 Chat", page_icon="💬", layout="wide")


def read_text_file(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8").strip()


def load_memory() -> list[dict[str, Any]]:
    if not MEMORY_PATH.exists():
        return []

    raw = MEMORY_PATH.read_text(encoding="utf-8").strip()
    if not raw:
        return []

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return []

    return data if isinstance(data, list) else []


def save_memory(memory_items: list[dict[str, Any]]) -> None:
    MEMORY_PATH.write_text(json.dumps(memory_items, indent=2), encoding="utf-8")


def append_memory(role: str, content: str) -> None:
    trimmed = content.strip()
    if not trimmed:
        return

    memory_items = load_memory()
    memory_items.append(
        {
            "role": role,
            "content": trimmed,
            "timestamp": datetime.now().isoformat(timespec="seconds"),
        }
    )
    save_memory(memory_items[-12:])


def save_chat_snapshot(messages: list[dict[str, str]]) -> None:
    CHATS_DIR.mkdir(exist_ok=True)
    filename = datetime.now().strftime("%Y%m%d_%H%M%S.json")
    payload = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "messages": messages,
    }
    (CHATS_DIR / filename).write_text(json.dumps(payload, indent=2), encoding="utf-8")


def build_messages_for_api(prompt: str, memory_items: list[dict[str, Any]]) -> list[dict[str, str]]:
    system_parts = [
        "You are a helpful assistant inside a Streamlit app.",
        "Answer clearly and concisely.",
    ]

    if memory_items:
        recent_memory = "\n".join(
            f'- {item.get("role", "note")}: {item.get("content", "")}'
            for item in memory_items[-6:]
        )
        system_parts.append(f"Recent saved memory:\n{recent_memory}")

    messages = [{"role": "system", "content": "\n\n".join(system_parts)}]
    messages.extend(st.session_state.messages)
    messages.append({"role": "user", "content": prompt})
    return messages


def request_hf_chat(prompt: str, token: str, memory_items: list[dict[str, Any]]) -> str:
    payload = {
        "model": MODEL_NAME,
        "messages": build_messages_for_api(prompt, memory_items),
        "temperature": 0.7,
        "max_tokens": 500,
    }

    response = requests.post(
        API_URL,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=60,
    )
    response.raise_for_status()
    data = response.json()
    return data["choices"][0]["message"]["content"]


if "messages" not in st.session_state:
    st.session_state.messages = []

hf_token = st.secrets.get("HF_TOKEN", "").strip()
memory_items = load_memory()
log_text = read_text_file(LOG_PATH)

st.title("Week 10 Chat")
st.caption("Streamlit chat app using the Hugging Face Inference Router.")

col1, col2, col3 = st.columns(3)
col1.metric("Hugging Face token configured", "Yes" if hf_token else "No")
col2.metric("Saved memory items", str(len(memory_items)))
col3.metric("Saved chat files", str(len(list(CHATS_DIR.glob("*.json")))) if CHATS_DIR.exists() else "0")

with st.sidebar:
    st.subheader("App Status")
    st.write(f"Model: `{MODEL_NAME}`")
    st.write(f"Endpoint: `{API_URL}`")

    if not hf_token:
        st.error("Missing `HF_TOKEN` in Streamlit secrets. Add it in deployment settings or `.streamlit/secrets.toml`.")
    else:
        st.success("Hugging Face token detected.")

    if memory_items:
        st.subheader("Recent Memory")
        for item in memory_items[-5:]:
            st.write(f'- {item.get("role", "note")}: {item.get("content", "")}')
    else:
        st.info("memory.json is empty. Chat messages will start filling it once you use the app.")

    if log_text:
        st.subheader("Interaction Log")
        st.markdown(log_text)
    else:
        st.info("ai_interaction_log.md is empty.")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

prompt = st.chat_input("Ask something...")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    append_memory("user", prompt)

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        if not hf_token:
            assistant_reply = "I can't contact Hugging Face yet because `HF_TOKEN` is missing from Streamlit secrets."
            st.error(assistant_reply)
        else:
            try:
                with st.spinner("Thinking..."):
                    assistant_reply = request_hf_chat(prompt, hf_token, memory_items)
                st.markdown(assistant_reply)
            except requests.RequestException as exc:
                assistant_reply = f"Request failed: {exc}"
                st.error(assistant_reply)

    st.session_state.messages.append({"role": "assistant", "content": assistant_reply})
    append_memory("assistant", assistant_reply)
    save_chat_snapshot(st.session_state.messages)
