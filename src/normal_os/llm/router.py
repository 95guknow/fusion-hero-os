"""LLMRouter - Multi-provider LLM router with free tier support

Supports: Google AI Studio (Gemini), OpenRouter, Groq, Cerebras, Mistral,
Hugging Face Inference, Github Models, and more.
"""
from __future__ import annotations

from typing import AsyncIterator, Dict, List, Optional

from pydantic_settings import BaseSettings

from .providers import (
    CerebrasProvider,
    GitHubModelsProvider,
    GoogleProvider,
    GroqProvider,
    HuggingFaceProvider,
    LLMMessage,
    LLMProvider,
    LLMResponse,
    MistralProvider,
    OpenRouterProvider,
)

# Bevorzugte Reihenfolge: schnelle/kostenlose Provider zuerst.
_PROVIDER_PRIORITY = ("groq", "cerebras", "openrouter", "github", "google", "mistral", "huggingface")

_PROVIDER_CLASSES: Dict[str, type] = {
    "google": GoogleProvider,
    "openrouter": OpenRouterProvider,
    "groq": GroqProvider,
    "mistral": MistralProvider,
    "huggingface": HuggingFaceProvider,
    "github": GitHubModelsProvider,
    "cerebras": CerebrasProvider,
}


class LLMSettings(BaseSettings):
    """API-Keys je Provider aus Env-Variablen (leer = Provider nicht verfuegbar)."""

    google_api_key: str = ""
    openrouter_api_key: str = ""
    groq_api_key: str = ""
    mistral_api_key: str = ""
    huggingface_api_key: str = ""
    github_api_key: str = ""
    cerebras_api_key: str = ""


class LLMRouter:
    """Waehlt automatisch einen verfuegbaren Provider (per konfiguriertem API-Key)."""

    def __init__(self, settings: Optional[LLMSettings] = None):
        self.settings = settings or LLMSettings()
        self._providers: Dict[str, LLMProvider] = {}
        keys = {
            "google": self.settings.google_api_key,
            "openrouter": self.settings.openrouter_api_key,
            "groq": self.settings.groq_api_key,
            "mistral": self.settings.mistral_api_key,
            "huggingface": self.settings.huggingface_api_key,
            "github": self.settings.github_api_key,
            "cerebras": self.settings.cerebras_api_key,
        }
        for name, api_key in keys.items():
            if api_key:
                self._providers[name] = _PROVIDER_CLASSES[name](api_key)

    @property
    def available_providers(self) -> List[str]:
        return [name for name in _PROVIDER_PRIORITY if name in self._providers]

    def _pick_provider(self, prefer: Optional[str] = None) -> LLMProvider:
        if prefer:
            if prefer not in self._providers:
                raise ValueError(f"Provider '{prefer}' nicht verfuegbar (kein API-Key konfiguriert).")
            return self._providers[prefer]
        for name in _PROVIDER_PRIORITY:
            if name in self._providers:
                return self._providers[name]
        raise RuntimeError(
            "Kein LLM-Provider verfuegbar - keine API-Keys konfiguriert "
            f"(erwartet Env-Variablen wie {', '.join(n.upper() + '_API_KEY' for n in _PROVIDER_PRIORITY)})."
        )

    async def generate(self, messages: List[LLMMessage], model: Optional[str] = None,
                        provider: Optional[str] = None, temperature: float = 0.7,
                        max_tokens: Optional[int] = None, **kwargs) -> LLMResponse:
        p = self._pick_provider(prefer=provider)
        return await p.generate(messages, model=model or p.models[0], temperature=temperature,
                                 max_tokens=max_tokens, **kwargs)

    async def stream(self, messages: List[LLMMessage], model: Optional[str] = None,
                      provider: Optional[str] = None, temperature: float = 0.7,
                      max_tokens: Optional[int] = None, **kwargs) -> AsyncIterator[str]:
        p = self._pick_provider(prefer=provider)
        async for chunk in p.stream(messages, model=model or p.models[0], temperature=temperature,
                                     max_tokens=max_tokens, **kwargs):
            yield chunk

    async def embedding(self, text: str, model: Optional[str] = None,
                         provider: Optional[str] = None) -> List[float]:
        p = self._pick_provider(prefer=provider)
        return await p.embedding(text, model=model or p.models[0])

    async def vision(self, messages: List[LLMMessage], model: Optional[str] = None,
                      provider: Optional[str] = None, temperature: float = 0.7,
                      max_tokens: Optional[int] = None, **kwargs) -> LLMResponse:
        p = self._pick_provider(prefer=provider)
        return await p.vision(messages, model=model or p.models[0], temperature=temperature,
                               max_tokens=max_tokens, **kwargs)
