"""
llm.py — LLM Adapter
Support: Gemini, OpenAI, Ollama via LiteLLM.
"""

import logging
from . import config as cfg

logger = logging.getLogger(__name__)


def call(messages: list[dict], **kwargs) -> str:
    """
    Kirim messages ke LLM yang dikonfigurasi.
    Return: string response atau error message.
    """
    provider  = cfg.get("llm.provider", "gemini")
    model     = cfg.get("llm.model", "gemini/gemini-2.0-flash")
    api_key   = cfg.get("llm.api_key", "")
    base_url  = cfg.get("llm.base_url", "")

    try:
        import litellm

        # Setup per provider
        if provider == "ollama":
            response = litellm.completion(
                model    = f"ollama/{model}" if not model.startswith("ollama/") else model,
                messages = messages,
                api_base = base_url or "http://localhost:11434",
                **kwargs,
            )
        elif provider == "openai":
            response = litellm.completion(
                model    = model,
                messages = messages,
                api_key  = api_key,
                **kwargs,
            )
        else:
            # Gemini (default)
            response = litellm.completion(
                model    = model if "/" in model else f"gemini/{model}",
                messages = messages,
                api_key  = api_key,
                **kwargs,
            )

        return response.choices[0].message.content

    except ImportError:
        logger.error("litellm not installed. Run: pip install litellm")
        return "❌ LLM not configured. Run `simplecontext-bot setup` first."

    except Exception as e:
        logger.error(f"LLM error ({provider}): {e}")
        error_type = type(e).__name__
        if "auth" in str(e).lower() or "key" in str(e).lower():
            return "❌ Invalid API key. Run `simplecontext-bot setup` to reconfigure."
        if "rate" in str(e).lower():
            return "⚠️ Rate limit reached. Please wait a moment and try again."
        if "connect" in str(e).lower() or "network" in str(e).lower():
            return "❌ Connection error. Check your internet connection."
        return f"❌ LLM error: {error_type}"


def test_connection() -> tuple[bool, str]:
    """Test koneksi ke LLM. Return (success, message)."""
    provider = cfg.get("llm.provider", "gemini")
    model    = cfg.get("llm.model", "")
    try:
        reply = call([{"role": "user", "content": "Say 'ok' in one word."}],
                     max_tokens=10)
        if "❌" in reply or "⚠️" in reply:
            return False, reply
        return True, f"✅ Connected to {provider} / {model}"
    except Exception as e:
        return False, f"❌ Failed: {e}"
