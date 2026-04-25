"""Anthropic (Claude) drop-in replacement for SAPER's Gemini api_inference.

Exposes the same `api_inference(RAG_prompt, model)` signature used in
RAPM/GEMINI_inference.py, structural_retrieval/src/enhanced_prompt.py, and
structural_retrieval/src/run_prostt5_rapm_sim.py.

Differences from the Gemini version, all intentional:
- Reads ANTHROPIC_API_KEY (not GEMINI_API_KEY).
- Default model is `claude-sonnet-4-6` if the caller passes a Gemini model
  name (we silently rewrite gemini-* -> claude-sonnet-4-6 so the existing
  shell commands keep working). Override with the LLM_MODEL env var or the
  CLI's [model] argument.
- No safety_settings: Anthropic exposes no equivalent BLOCK_NONE flag for
  scientific content; the default policy already permits it.
- Same JSON-stripping post-processing (```json fences + {"description": ...}).
- Same empty-string-on-error contract so the rest of the pipeline keeps going.
"""

import json
import os
import time

import anthropic


# ── Defaults you can override via env vars ───────────────────────────────────
DEFAULT_MODEL = os.environ.get("LLM_MODEL", "claude-sonnet-4-6")
DEFAULT_MAX_TOKENS = int(os.environ.get("LLM_MAX_TOKENS", "4096"))
DEFAULT_TEMPERATURE = float(os.environ.get("LLM_TEMPERATURE", "0.7"))


# Module-level client; reuses connections across calls.
_client = None


def _get_client():
    global _client
    if _client is None:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError(
                "ANTHROPIC_API_KEY is not set. Run `export ANTHROPIC_API_KEY=...`"
            )
        _client = anthropic.Anthropic(api_key=api_key)
    return _client


def _normalize_model(model: str) -> str:
    """Map gemini-* names that SAPER scripts default to onto a Claude model."""
    if not model or model.lower().startswith("gemini"):
        return DEFAULT_MODEL
    return model


def _strip_json_fences(text: str) -> str:
    return text.replace("```json", "").replace("```", "").strip()


def api_inference(RAG_prompt: str, model: str = DEFAULT_MODEL) -> str:
    """Single-prompt inference. Returns the model's text answer or ""."""
    client = _get_client()
    model = _normalize_model(model)

    backoff = 2.0
    for attempt in range(5):
        try:
            resp = client.messages.create(
                model=model,
                max_tokens=DEFAULT_MAX_TOKENS,
                temperature=DEFAULT_TEMPERATURE,
                messages=[{"role": "user", "content": RAG_prompt}],
            )

            parts = [b.text for b in resp.content if getattr(b, "type", "") == "text"]
            output = "".join(parts) if parts else ""
            output = _strip_json_fences(output)

            # If the model returned the prompted JSON shape, pull out the
            # description field to match the Gemini path.
            try:
                parsed = json.loads(output)
                if isinstance(parsed, dict) and "description" in parsed:
                    output = parsed["description"]
            except json.JSONDecodeError:
                pass

            return output

        except anthropic.RateLimitError:
            time.sleep(backoff)
            backoff *= 2
        except anthropic.APIStatusError as e:
            # 5xx -> retry with backoff; 4xx -> give up (and let the run
            # continue with an empty prediction so SAPER's eval doesn't crash).
            if e.status_code and 500 <= e.status_code < 600:
                time.sleep(backoff)
                backoff *= 2
                continue
            print(f"Claude API error (status {e.status_code}): {e}")
            return ""
        except Exception as e:
            print(f"Claude API error: {e}")
            return ""

    return ""


if __name__ == "__main__":
    # Quick smoke test: `python claude_inference.py`
    print(api_inference(
        'Reply with the JSON {"description": "ok"} and nothing else.'
    ))
