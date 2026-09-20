"""Thin wrapper around the Anthropic API for the copilot's LLM layer."""
import os

from anthropic import Anthropic

MODEL = "claude-sonnet-4-6"


def get_client() -> Anthropic:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("Set ANTHROPIC_API_KEY before calling the LLM layer.")
    return Anthropic(api_key=api_key)


def ask(prompt: str, system: str | None = None) -> str:
    """Send a single-turn prompt to Claude and return the text response."""
    client = get_client()
    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system=system or "",
        messages=[{"role": "user", "content": prompt}],
    )
    return "".join(block.text for block in response.content if block.type == "text")


if __name__ == "__main__":
    print(ask("Say hello in one short sentence."))
