"""Minimal NEAR AI Cloud client (OpenAI-compatible), stdlib only.

Reads the API key from the NEAR_AI_API_KEY environment variable.
The key is never logged, never stored, and never sent anywhere except
https://cloud-api.near.ai as a bearer token.
"""
import json
import os
import urllib.request
import urllib.error

API_URL = "https://cloud-api.near.ai/v1/chat/completions"
DEFAULT_MODEL = "anthropic/claude-haiku-5-5"


def chat(messages, model=None, max_tokens=800, temperature=0.2):
    """Send a chat completion request to NEAR AI Cloud and return the reply text."""
    key = os.environ.get("NEAR_AI_API_KEY")
    if not key:
        raise RuntimeError("NEAR_AI_API_KEY is not set (see .env.example)")
    body = {
        "model": model or os.environ.get("NEAR_AI_MODEL", DEFAULT_MODEL),
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    req = urllib.request.Request(
        API_URL,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": "Bearer " + key,
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise RuntimeError("NEAR AI Cloud returned HTTP %s" % e.code)
    return payload["choices"][0]["message"]["content"]
