### Task: Core Chat Application
Build the foundational ChatGPT-style app in four progressive stages. Complete each part before moving to the next — each part extends the previous one.

**Prompt:** 
Now we will build the founbdational chatgpt stype app for this deployment. First use st.set_page_config(page_title="My AI Chat", layout="wide").
Load your Hugging Face token using st.secrets["HF_TOKEN"]. The token must never be hardcoded in app.py.
If the token is missing or empty, display a clear error message in the app. The app must not crash.
Send a single hardcoded test message (e.g. "Hello!") to the Hugging Face API using the loaded token and display the model’s response in the main area.
Handle API errors gracefully (missing token, invalid token, rate limit, network failure) with a user-visible message rather than a crash.
Commit to gitcommit
**AI Suggestion:** 
AI checked multiple times that the token is in the right place and not in app.py directly. It simplified the app behavior to match the task part A exactly: send one hardcoded "Hello!" test request with the loaded token and show the response in the main area, while keeping all failures user-visible and non-crashing.
**My Modifications & Reflections:** [Did the code work? Did you adapt anything to fit the assignment?]






### Task: [Task Name]
**Prompt:** "[Paste your prompt here or summarize if too long]"
**AI Suggestion:** [Brief summary of what the AI suggested]
**My Modifications & Reflections:** [Did the code work? Did you adapt anything to fit the assignment?]