"""Calls the Groq API (OpenAI-compatible). Needs GROQ_API_KEY set as an environment variable."""
import json, requests
from config import GROQ_API_KEY, GROQ_MODEL

URL = "https://api.groq.com/openai/v1/chat/completions"

def call_llm(prompt, temperature=0):
    if not GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY is not set. In Command Prompt: set GROQ_API_KEY=gsk_xxx")
    r = requests.post(URL,
        headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
        json={"model": GROQ_MODEL, "temperature": temperature,
              "messages": [{"role": "user", "content": prompt}]},
        timeout=30)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]
