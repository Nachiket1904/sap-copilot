"""Thin, provider-agnostic wrapper around the copilot's LLM layer.

Provider is chosen via the LLM_PROVIDER env var:
  - "groq"   (default) — an open model on Groq (default openai/gpt-oss-20b), fast + free tier
  - "gemini" — Google's Gemini flash models, fallback/alternate

Retrieval and data layers only ever call `ask()` — they never know which
provider is configured.
"""
import os

from dotenv import load_dotenv

load_dotenv()  # read GROQ_API_KEY / LLM_PROVIDER from a local .env (git-ignored)

GROQ_MODEL = os.environ.get("GROQ_MODEL", "openai/gpt-oss-20b")  # override in .env if your account lacks access
GEMINI_MODEL = "gemini-2.0-flash"


def _ask_groq(prompt: str, system: str | None) -> str:
    from groq import Groq

    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("Set GROQ_API_KEY before calling the LLM layer.")
    client = Groq(api_key=api_key)
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    # temperature 0: the same question should produce the same SQL every run
    response = client.chat.completions.create(model=GROQ_MODEL, messages=messages, temperature=0)
    return response.choices[0].message.content


def _ask_gemini(prompt: str, system: str | None) -> str:
    import google.generativeai as genai

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("Set GEMINI_API_KEY before calling the LLM layer.")
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(GEMINI_MODEL, system_instruction=system or None)
    response = model.generate_content(prompt)
    return response.text


def ask(prompt: str, system: str | None = None) -> str:
    """Send a single-turn prompt to the configured LLM provider and return the text response."""
    provider = os.environ.get("LLM_PROVIDER", "groq").lower()
    if provider == "groq":
        return _ask_groq(prompt, system)
    if provider == "gemini":
        return _ask_gemini(prompt, system)
    raise ValueError(f"Unknown LLM_PROVIDER: {provider!r} (expected 'groq' or 'gemini')")


if __name__ == "__main__":
    print(ask("Say hello in one short sentence."))
