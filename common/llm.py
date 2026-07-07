"""Provider-abstraction layer with an ordered fallback chain used by BOTH the
ingestion extractor and the agents:

    1. Gemini (primary)   GEMINI_API_KEY
    2. Groq   (fallback)  GROQ_API_KEY   — only after Gemini is missing/rate-limited
    3. caller's own fallback (e.g. golden extraction) when this raises NoProviderAvailable

Rate-limit discipline for a FREE tier:
    * calls are SEQUENTIAL and globally throttled (min seconds between any two calls)
    * exponential backoff on HTTP 429 / quota errors, then advance to the next provider
    * the serving provider is logged so the fallback is observable on demo day
"""
from __future__ import annotations
import time, threading, json

from . import config

MIN_INTERVAL = float(config.get("LLM_MIN_INTERVAL_S", "5") or 5)
MAX_RETRIES = int(config.get("LLM_MAX_RETRIES", "4") or 4)

_lock = threading.Lock()   # serialize all LLM calls process-wide
_last_call = 0.0
_disabled: set[str] = set()  # circuit breaker: providers quota-exhausted this process


class NoProviderAvailable(RuntimeError):
    pass


def _throttle():
    global _last_call
    now = time.time()
    wait = MIN_INTERVAL - (now - _last_call)
    if wait > 0:
        time.sleep(wait)
    _last_call = time.time()


def _is_rate_limited(exc: Exception) -> bool:
    s = f"{type(exc).__name__} {exc}".lower()
    return any(t in s for t in ("429", "rate", "quota", "resource_exhausted", "resourceexhausted", "too many requests"))


# --------------------------------------------------------------------- providers
def _gemini_call(system, prompt, json_mode, temperature):
    from google import genai
    client = genai.Client(api_key=config.GEMINI_API_KEY)
    cfg = {"temperature": temperature,
           "response_mime_type": "application/json" if json_mode else "text/plain"}
    resp = client.models.generate_content(
        model=config.GEMINI_MODEL, contents=f"{system}\n\n{prompt}", config=cfg)
    return resp.text


def _groq_call(system, prompt, json_mode, temperature):
    from groq import Groq
    client = Groq(api_key=config.get("GROQ_API_KEY"))
    kwargs = dict(model=config.get("GROQ_MODEL", "llama-3.1-8b-instant"),
                  messages=[{"role": "system", "content": system},
                            {"role": "user", "content": prompt}],
                  temperature=temperature)
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}
    resp = client.chat.completions.create(**kwargs)
    return resp.choices[0].message.content


def _providers():
    provs = []
    if config.GEMINI_API_KEY and "gemini" not in _disabled:
        provs.append(("gemini", config.GEMINI_MODEL, _gemini_call))
    if config.get("GROQ_API_KEY") and "groq" not in _disabled:
        provs.append(("groq", config.get("GROQ_MODEL", "llama-3.1-8b-instant"), _groq_call))
    return provs


def available() -> list[str]:
    return [p[0] for p in _providers()]


def complete(system: str, prompt: str, json_mode: bool = False,
             temperature: float = 0.0, log=print) -> tuple[str, str]:
    """Return (text, provider_label). Raises NoProviderAvailable if all tiers fail."""
    provs = _providers()
    if not provs:
        raise NoProviderAvailable("no LLM providers configured (set GEMINI_API_KEY or GROQ_API_KEY)")
    last_err = None
    with _lock:  # process-wide serialization: never parallelize LLM calls
        for name, model, fn in provs:
            for attempt in range(MAX_RETRIES):
                _throttle()
                try:
                    text = fn(system, prompt, json_mode, temperature)
                    log(f"[llm] provider={name} model={model} ok (attempt {attempt + 1})")
                    return text, f"{name}:{model}"
                except Exception as e:  # noqa: BLE001
                    last_err = e
                    if _is_rate_limited(e) and attempt < MAX_RETRIES - 1:
                        backoff = MIN_INTERVAL * (2 ** attempt)
                        log(f"[llm] provider={name} rate-limited (attempt {attempt + 1}); "
                            f"backoff {backoff:.0f}s")
                        time.sleep(backoff)
                        continue
                    if _is_rate_limited(e):
                        # quota exhausted after retries: trip the breaker so later calls
                        # this process skip straight to the next tier (no repeated backoff)
                        _disabled.add(name)
                        log(f"[llm] provider={name} quota-exhausted; disabling for this process")
                    else:
                        log(f"[llm] provider={name} failed: {type(e).__name__}: {str(e)[:160]}")
                    break  # advance to next provider
    raise NoProviderAvailable(f"all providers failed; last error: {last_err}")


def complete_json(system: str, prompt: str, temperature: float = 0.0, log=print) -> tuple[dict, str]:
    text, provider = complete(system, prompt, json_mode=True, temperature=temperature, log=log)
    return json.loads(text), provider
