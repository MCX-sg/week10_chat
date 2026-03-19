from __future__ import annotations

import json
import time
from datetime import datetime
from pathlib import Path
from uuid import uuid4

import requests
import streamlit as st


API_URL = "https://router.huggingface.co/v1/chat/completions"
MODEL_NAME = "meta-llama/Llama-3.2-1B-Instruct"
CHATS_DIR = Path(__file__).parent / "chats"

st.set_page_config(page_title="My AI Chat", layout="wide")

try:
    hf_token = st.secrets["HF_TOKEN"].strip()
except Exception:
    hf_token = ""


def request_hf_chat(token: str, messages: list[dict[str, str]]) -> str:
    def stream_chunks():
        with requests.post(
            API_URL,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            json={
                "model": MODEL_NAME,
                "messages": messages,
                "max_tokens": 512,
                "stream": True,
            },
            timeout=60,
            stream=True,
        ) as response:
            if response.status_code == 401:
                raise ValueError("Invalid Hugging Face token. Check your `HF_TOKEN` secret and try again.")
            if response.status_code == 429:
                raise ValueError("Rate limit reached. Wait a moment and try again.")
            if response.status_code >= 400:
                detail = response.text.strip() or f"HTTP {response.status_code}"
                raise ValueError(f"Hugging Face API error: {detail}")

            for raw_line in response.iter_lines(decode_unicode=True):
                if not raw_line:
                    continue
                if not raw_line.startswith("data:"):
                    continue

                data_str = raw_line[len("data:") :].strip()
                if data_str == "[DONE]":
                    break

                try:
                    event = json.loads(data_str)
                except json.JSONDecodeError:
                    continue

                choices = event.get("choices", [])
                if not choices:
                    continue

                delta = choices[0].get("delta", {})
                content = delta.get("content", "")
                if content:
                    yield content
                    time.sleep(0.02)

    return st.write_stream(stream_chunks())


def make_chat(title: str = "New Chat") -> dict:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return {
        "id": uuid4().hex,
        "title": title,
        "timestamp": timestamp,
        "messages": [],
    }


def chat_file_path(chat_id: str) -> Path:
    return CHATS_DIR / f"{chat_id}.json"


def save_chat(chat: dict) -> None:
    CHATS_DIR.mkdir(exist_ok=True)
    payload = {
        "id": chat["id"],
        "title": chat["title"],
        "timestamp": chat["timestamp"],
        "messages": chat["messages"],
    }
    chat_file_path(chat["id"]).write_text(json.dumps(payload, indent=2), encoding="utf-8")


def load_chats() -> list[dict]:
    CHATS_DIR.mkdir(exist_ok=True)
    loaded_chats = []

    for path in sorted(CHATS_DIR.glob("*.json")):
        try:
            chat = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue

        if not isinstance(chat, dict):
            continue

        chat_id = str(chat.get("id", "")).strip() or path.stem
        title = str(chat.get("title", "")).strip() or "New Chat"
        timestamp = str(chat.get("timestamp", "")).strip() or datetime.fromtimestamp(path.stat().st_mtime).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        messages = chat.get("messages", [])

        if not isinstance(messages, list):
            messages = []

        loaded_chats.append(
            {
                "id": chat_id,
                "title": title,
                "timestamp": timestamp,
                "messages": messages,
            }
        )

    loaded_chats.sort(key=lambda chat: chat["timestamp"], reverse=True)
    return loaded_chats


def ensure_chat_state() -> None:
    if "chats" not in st.session_state:
        loaded_chats = load_chats()
        if loaded_chats:
            st.session_state.chats = loaded_chats
            st.session_state.active_chat_id = loaded_chats[0]["id"]
        else:
            st.session_state.chats = []
            st.session_state.active_chat_id = None
    elif "active_chat_id" not in st.session_state:
        st.session_state.active_chat_id = st.session_state.chats[0]["id"] if st.session_state.chats else None


def get_active_chat() -> dict | None:
    active_chat_id = st.session_state.active_chat_id
    for chat in st.session_state.chats:
        if chat["id"] == active_chat_id:
            return chat
    return None


def create_new_chat() -> None:
    new_chat = make_chat()
    st.session_state.chats.insert(0, new_chat)
    st.session_state.active_chat_id = new_chat["id"]
    save_chat(new_chat)


def delete_chat(chat_id: str) -> None:
    chats = st.session_state.chats
    remaining = [chat for chat in chats if chat["id"] != chat_id]
    st.session_state.chats = remaining
    chat_path = chat_file_path(chat_id)
    if chat_path.exists():
        chat_path.unlink()

    if not remaining:
        st.session_state.active_chat_id = None
        return

    if st.session_state.active_chat_id == chat_id:
        st.session_state.active_chat_id = remaining[0]["id"]


def update_chat_title(chat: dict) -> None:
    if chat["messages"] and chat["title"] == "New Chat":
        first_user_message = next(
            (message["content"] for message in chat["messages"] if message["role"] == "user"),
            "New Chat",
        )
        chat["title"] = first_user_message[:30] or "New Chat"


def touch_chat(chat: dict) -> None:
    chat["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")


ensure_chat_state()
active_chat = get_active_chat()


st.title("My AI Chat")
st.caption("Part C: multi-chat sidebar navigation with native Streamlit chat components.")

st.write(f"Model: `{MODEL_NAME}`")

with st.sidebar:
    st.header("Chats")
    st.button("New Chat", on_click=create_new_chat, use_container_width=True)

    if st.session_state.chats:
        for chat in st.session_state.chats:
            is_active = chat["id"] == st.session_state.active_chat_id
            row_left, row_right = st.columns([5, 1])

            with row_left:
                label = f"{chat['title']}\n{chat['timestamp']}"
                if st.button(
                    label,
                    key=f"chat_select_{chat['id']}",
                    use_container_width=True,
                    type="primary" if is_active else "secondary",
                ):
                    st.session_state.active_chat_id = chat["id"]
                    st.rerun()

            with row_right:
                if st.button("✕", key=f"chat_delete_{chat['id']}", use_container_width=True):
                    delete_chat(chat["id"])
                    st.rerun()
    else:
        st.info("No chats yet. Create one to get started.")

active_chat = get_active_chat()

if not hf_token:
    st.error("Missing `HF_TOKEN` in Streamlit secrets. Add it in deployment settings or `.streamlit/secrets.toml`.")
else:
    if active_chat is None:
        st.info("No active chat selected. Create a new chat from the sidebar.")
    else:
        for message in active_chat["messages"]:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        prompt = st.chat_input("Send a message")

        if prompt:
            user_message = {"role": "user", "content": prompt}
            active_chat["messages"].append(user_message)
            update_chat_title(active_chat)
            touch_chat(active_chat)
            save_chat(active_chat)

            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                try:
                    assistant_reply = request_hf_chat(hf_token, active_chat["messages"])
                except ValueError as exc:
                    assistant_reply = f"Error: {exc}"
                    st.error(str(exc))
                except requests.RequestException:
                    assistant_reply = "Error: Network failure while contacting the Hugging Face API. Check your connection and try again."
                    st.error("Network failure while contacting the Hugging Face API. Check your connection and try again.")
                except Exception as exc:
                    assistant_reply = f"Error: Unexpected error: {exc}"
                    st.error(f"Unexpected error: {exc}")

            active_chat["messages"].append({"role": "assistant", "content": assistant_reply})
            save_chat(active_chat)
