#!/usr/bin/env python3
"""Minimal, quota-friendly sanity check of the LLM provider chain + a direct Groq call."""
import sys, json
sys.path.insert(0, "/root/analytos-brain")
from common import llm, config

print("available providers:", llm.available())

print("\n== direct Groq minimal call ==")
try:
    from groq import Groq
    c = Groq(api_key=config.get("GROQ_API_KEY"))
    r = c.chat.completions.create(
        model=config.get("GROQ_MODEL", "llama-3.1-8b-instant"),
        messages=[{"role": "user", "content": "Reply with exactly: PONG"}],
        temperature=0, max_tokens=5)
    print("  groq ok ->", repr(r.choices[0].message.content.strip()))
except Exception as e:
    print("  groq FAILED ->", type(e).__name__, str(e)[:200])

print("\n== provider-chain JSON call (tries Gemini first, then Groq) ==")
try:
    data, provider = llm.complete_json(
        "You output JSON only.",
        'Return this JSON exactly: {"status":"ok","n":3}', temperature=0)
    print("  served by:", provider, "->", json.dumps(data))
except Exception as e:
    print("  chain FAILED ->", type(e).__name__, str(e)[:200])
