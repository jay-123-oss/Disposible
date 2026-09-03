"""Unified LLM Gateway: run agents against ANY model provider's API key.

Replaces the hard-coded "run models on Kaggle/Colab GPU notebooks" workflow with a
production-ready key-based model backend. Configure once (env vars or a local
``.env`` file) and every agent (coding / testing / security / quality /
infrastructure / embedding) transparently talks to the provider you chose.

Quick setup (example — OpenAI):
    LLM_PROVIDER=openai
    OPENAI_API_KEY=sk-...
    LLM_MODEL=gpt-4o-mini            # optional; provider default otherwise

Any OpenAI-compatible endpoint works too (Groq, OpenRouter, Mistral, Together,
DeepSeek, xAI, LM Studio, vLLM, ...):
    LLM_PROVIDER=openai-compatible
    LLM_BASE_URL=https://api.groq.com/openai/v1
    LLM_API_KEY=gsk_...
    LLM_MODEL=llama-3.3-70b-versatile

No API key configured? The gateway falls back to the local Ollama runtime
(http://localhost:11434) exactly like the previous behaviour. If Ollama is also
down, agents keep their deterministic offline templates.

Security notes
    * Keys are read from the environment / a git-ignored .env file only.
    * Never logged and never returned by get_llm_status() (masked).
    * OpenAI / Anthropic / Gemini keys are read directly from the process
      environment; .env is a convenience loader for local development.
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional

import requests

logger = logging.getLogger("LLMGateway")

DEFAULT_OLLAMA_URL = "http://localhost:11434"

# name -> { base_url, key_env, default_model, env_header? }
PROVIDER_PRESETS: Dict[str, Dict[str, Any]] = {
    "openai": {
        "base_url": "https://api.openai.com/v1",
        "key_env": "OPENAI_API_KEY",
        "default_model": "gpt-4o-mini",
        "supports_embeddings": True,
    },
    "anthropic": {
        "base_url": "https://api.anthropic.com/v1",
        "key_env": "ANTHROPIC_API_KEY",
        "default_model": "claude-3-5-sonnet-latest",
        "supports_embeddings": False,
    },
    "gemini": {
        "base_url": "https://generativelanguage.googleapis.com/v1beta",
        "key_env": "GEMINI_API_KEY",
        "default_model": "gemini-1.5-flash",
        "supports_embeddings": True,
    },
    "groq": {
        "base_url": "https://api.groq.com/openai/v1",
        "key_env": "GROQ_API_KEY",
        "default_model": "llama-3.3-70b-versatile",
        "supports_embeddings": False,
    },
    "openrouter": {
        "base_url": "https://openrouter.ai/api/v1",
        "key_env": "OPENROUTER_API_KEY",
        "default_model": "anthropic/claude-3.5-sonnet",
        "supports_embeddings": False,
    },
    "mistral": {
        "base_url": "https://api.mistral.ai/v1",
        "key_env": "MISTRAL_API_KEY",
        "default_model": "mistral-large-latest",
        "supports_embeddings": False,
    },
    "together": {
        "base_url": "https://api.together.xyz/v1",
        "key_env": "TOGETHER_API_KEY",
        "default_model": "meta-llama/Llama-3.3-70B-Instruct-Turbo",
        "supports_embeddings": True,
    },
    "xai": {
        "base_url": "https://api.x.ai/v1",
        "key_env": "XAI_API_KEY",
        "default_model": "grok-beta",
        "supports_embeddings": False,
    },
    "deepseek": {
        "base_url": "https://api.deepseek.com/v1",
        "key_env": "DEEPSEEK_API_KEY",
        "default_model": "deepseek-chat",
        "supports_embeddings": False,
    },
    "ollama": {
        "base_url": DEFAULT_OLLAMA_URL,
        "key_env": None,
        "default_model": "qwen2.5-coder:3b",
        "supports_embeddings": False,
    },
    "openai-compatible": {
        "base_url": None,  # must come from LLM_BASE_URL
        "key_env": "LLM_API_KEY",
        "default_model": None,  # must come from LLM_MODEL or LLM_BASE_URL provider default
        "supports_embeddings": True,
    },
}

# Order used when LLM_PROVIDER is unset (first provider with a key wins).
_KEYED_PROVIDER_ORDER = [
    "openai",
    "anthropic",
    "gemini",
    "groq",
    "openrouter",
    "mistral",
    "together",
    "xai",
    "deepseek",
]

_DOTENV_LOADED = False
# The .env lives next to this module (the project root) — not the process CWD,
# which can be anything (Electron launcher, systemd, IDE run config, …).
_DOTENV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")


def _load_dotenv(path: Optional[str] = None) -> None:
    """Minimal .env loader (KEY=VALUE, # comments) — no third-party dependency.

    Looks for the .env next to this module first, then falls back to the process
    CWD so standalone scripts that deliberately place a .env nearby still work.
    """
    global _DOTENV_LOADED
    if _DOTENV_LOADED:
        return
    _DOTENV_LOADED = True
    candidates = [path] if path else [_DOTENV_PATH, os.path.join(os.getcwd(), ".env")]
    for candidate in candidates:
        if not candidate:
            continue
        try:
            with open(candidate, "r", encoding="utf-8") as fh:
                for raw in fh:
                    line = raw.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    key, _, value = line.partition("=")
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    if key and key not in os.environ:
                        os.environ[key] = value
            return  # first readable candidate wins
        except OSError:
            continue


def _get_env(name: str, default: Optional[str] = None) -> Optional[str]:
    _load_dotenv()
    return os.environ.get(name, default)


def resolve_provider() -> str:
    """Pick the active provider: explicit LLM_PROVIDER, first keyed preset, else ollama."""
    explicit = (_get_env("LLM_PROVIDER") or "").strip().lower()
    if explicit:
        if explicit in PROVIDER_PRESETS:
            return explicit
        # Unknown provider names are treated as a generic OpenAI-compatible endpoint.
        return "openai-compatible"
    for name in _KEYED_PROVIDER_ORDER:
        key_env = PROVIDER_PRESETS[name]["key_env"]
        if _get_env(key_env):
            return name
    return "ollama"


def _provider_api_key(provider: str) -> Optional[str]:
    key_env = PROVIDER_PRESETS[provider]["key_env"]
    if key_env:
        return _get_env(key_env)
    return None


def _provider_base_url(provider: str) -> Optional[str]:
    preset = PROVIDER_PRESETS[provider]
    # Global override first, then the preset base, then (for generic compatible
    # endpoints) the LLM_BASE_URL requirement.
    base = _get_env("LLM_BASE_URL") or preset.get("base_url")
    if provider == "openai-compatible" and not base:
        base = _get_env("OPENAI_BASE_URL") or "https://api.openai.com/v1"
    return (base or "").rstrip("/") or None


def resolve_model(requested: Optional[str] = None) -> Optional[str]:
    """Effective model: LLM_MODEL env override > requested model > provider default."""
    env_model = (_get_env("LLM_MODEL") or "").strip()
    if env_model:
        return env_model
    if requested:
        return requested
    preset = PROVIDER_PRESETS[resolve_provider()]
    return preset.get("default_model")


def is_key_configured() -> bool:
    provider = resolve_provider()
    if provider == "ollama":
        return False
    return bool(_provider_api_key(provider) or _get_env("LLM_API_KEY"))


# ==============================================================================
# Chat / text generation
# ==============================================================================
def _ollama_generate(model: str, prompt: str) -> Optional[str]:
    """Legacy local-runtime path (no API key required)."""
    url = (_get_env("OLLAMA_URL") or DEFAULT_OLLAMA_URL).rstrip("/")
    try:
        resp = requests.post(
            f"{url}/api/generate",
            json={"model": model, "prompt": prompt, "stream": False},
            timeout=(0.5, 120.0),
        )
        if resp.status_code == 200:
            return resp.json().get("response") or None
    except Exception as exc:
        logger.debug("Ollama generate failed (%s)", exc)
    return None


def _openai_compatible_chat(
    base_url: str,
    api_key: str,
    model: str,
    messages: List[Dict[str, str]],
    temperature: float,
    max_tokens: int,
) -> Optional[str]:
    url = base_url
    if not url.endswith("/chat/completions"):
        url += "/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload: Dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    resp = requests.post(url, headers=headers, json=payload, timeout=(1.0, 180.0))
    resp.raise_for_status()
    data = resp.json()
    content = data["choices"][0]["message"]["content"]
    return str(content)


def _anthropic_chat(
    base_url: str,
    api_key: str,
    model: str,
    system: str,
    prompt: str,
    max_tokens: int,
) -> Optional[str]:
    url = base_url.rstrip("/") + "/messages"
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json",
    }
    payload: Dict[str, Any] = {"model": model, "max_tokens": max_tokens, "messages": [{"role": "user", "content": prompt}]}
    if system:
        payload["system"] = system
    resp = requests.post(url, headers=headers, json=payload, timeout=(1.0, 180.0))
    resp.raise_for_status()
    data = resp.json()
    parts = data.get("content") or []
    return "".join(str(p.get("text", "")) for p in parts if p.get("type") == "text") or None


def _gemini_chat(
    base_url: str,
    api_key: str,
    model: str,
    system: str,
    prompt: str,
    max_tokens: int,
) -> Optional[str]:
    url = f"{base_url.rstrip('/')}/models/{model}:generateContent?key={api_key}"
    payload: Dict[str, Any] = {"contents": [{"parts": [{"text": prompt}]}]}
    if system:
        payload["systemInstruction"] = {"parts": [{"text": system}]}
    payload.setdefault("generationConfig", {"maxOutputTokens": max_tokens})
    resp = requests.post(url, json=payload, timeout=(1.0, 180.0))
    resp.raise_for_status()
    data = resp.json()
    candidates = data.get("candidates") or []
    parts = candidates[0].get("content", {}).get("parts", []) if candidates else []
    return "".join(str(p.get("text", "")) for p in parts) or None


def generate_text(
    prompt: str,
    system: Optional[str] = None,
    model: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 1500,
) -> Optional[str]:
    """Generate text through the configured provider.

    Returns None when the provider is unreachable / misconfigured so callers can
    fall back gracefully (agents keep their deterministic offline templates).
    """
    provider = resolve_provider()
    effective_model = resolve_model(model)
    if not effective_model:
        logger.warning("No model resolved for provider '%s'", provider)
        return None

    # Local runtime path (no key required)
    if provider == "ollama":
        full_prompt = system + "\n\nTask: " + prompt if system else prompt
        return _ollama_generate(effective_model, full_prompt)

    api_key = _provider_api_key(provider) or _get_env("LLM_API_KEY")
    if not api_key:
        logger.warning("Provider '%s' selected but no API key configured", provider)
        return None

    base_url = _provider_base_url(provider)
    if not base_url:
        logger.warning("Provider '%s' requires LLM_BASE_URL", provider)
        return None

    try:
        if provider == "anthropic":
            return _anthropic_chat(base_url, api_key, effective_model, system or "", prompt, max_tokens)
        if provider == "gemini":
            return _gemini_chat(base_url, api_key, effective_model, system or "", prompt, max_tokens)
        # Everything else speaks OpenAI-compatible chat completions.
        messages: List[Dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        return _openai_compatible_chat(base_url, api_key, effective_model, messages, temperature, max_tokens)
    except Exception as exc:
        logger.debug("LLM generate failed on provider '%s': %s", provider, exc)
        return None


# ==============================================================================
# Embeddings
# ==============================================================================
def _ollama_embed(text: str, model: Optional[str] = None) -> Optional[List[float]]:
    """Local Ollama /api/embeddings (keyless runtime backend)."""
    url = (_get_env("OLLAMA_URL") or DEFAULT_OLLAMA_URL).rstrip("/")
    local_model = (_get_env("LLM_EMBEDDING_MODEL") or "").strip() or model or "nomic-embed-text"
    try:
        resp = requests.post(
            f"{url}/api/embeddings",
            json={"model": local_model, "prompt": text},
            timeout=(0.5, 30.0),
        )
        if resp.status_code == 200:
            return resp.json().get("embedding")
    except Exception as exc:
        logger.debug("Ollama embeddings failed (%s)", exc)
    return None


def embed_text(text: str, model: Optional[str] = None) -> Optional[List[float]]:
    """Single embedding choke point: cloud provider first, local Ollama second.

    Order of attempts:
      1. The configured cloud provider, when it supports embeddings and an API
         key is set (OpenAI-compatible /embeddings or Gemini embedContent).
      2. The local Ollama runtime (keyless) — honors ``OLLAMA_URL`` and
         ``LLM_EMBEDDING_MODEL``; falls back to ``model`` (e.g. nomic-embed-text).

    Returns None only when every backend is unreachable / misconfigured, so the
    caller can fall back to a deterministic vector.
    """
    provider = resolve_provider()
    preset = PROVIDER_PRESETS[provider]
    api_key = _provider_api_key(provider) or _get_env("LLM_API_KEY")
    if preset.get("supports_embeddings") and api_key:
        base_url = _provider_base_url(provider)
        if base_url:
            cloud_model = (_get_env("LLM_EMBEDDING_MODEL") or "").strip() or None
            try:
                if provider == "gemini":
                    url = f"{base_url}/models/{cloud_model or 'text-embedding-004'}:embedContent?key={api_key}"
                    payload = {"content": {"parts": [{"text": text}]}}
                    resp = requests.post(url, json=payload, timeout=(1.0, 60.0))
                    resp.raise_for_status()
                    vector = resp.json().get("embedding", {}).get("values")
                    if vector:
                        return vector
                else:
                    # OpenAI-compatible /embeddings
                    url = f"{base_url.rstrip('/')}/embeddings"
                    payload: Dict[str, Any] = {
                        "model": cloud_model or "text-embedding-3-small",
                        "input": text,
                    }
                    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
                    resp = requests.post(url, headers=headers, json=payload, timeout=(1.0, 60.0))
                    resp.raise_for_status()
                    data = resp.json().get("data") or []
                    if data and data[0].get("embedding"):
                        return data[0]["embedding"]
            except Exception as exc:
                logger.debug("Cloud embed failed on provider '%s': %s", provider, exc)
                # Fall through to the local Ollama runtime below.

    # Keyless local runtime (also the only path for the 'ollama' provider).
    return _ollama_embed(text, model)


# ==============================================================================
# Status (safe to expose over HTTP — never includes the key)
# ==============================================================================
def mask_key(key: Optional[str]) -> str:
    if not key:
        return ""
    if len(key) <= 8:
        return "*" * len(key)
    return f"{key[:4]}...{key[-4:]}"


def get_llm_status() -> Dict[str, Any]:
    provider = resolve_provider()
    preset = PROVIDER_PRESETS[provider]
    key = _provider_api_key(provider) or _get_env("LLM_API_KEY")
    base_url = _provider_base_url(provider)
    return {
        "provider": provider,
        "model": resolve_model(),
        "base_url": base_url,
        "key_configured": bool(key),
        "key_masked": mask_key(key) if key else "",
        "mode": "cloud-api-key" if key else ("local-ollama" if provider == "ollama" else "not-configured"),
        "supported_providers": sorted(PROVIDER_PRESETS.keys()),
        "hint": "Set LLM_PROVIDER + <PROVIDER>_API_KEY (or LLM_API_KEY + LLM_BASE_URL + LLM_MODEL) in .env to use hosted models."
        if not key
        else "",
    }
