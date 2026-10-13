"""Deterministic mock chat adapter for the optional legacy task API."""
from .base import PHIGuard


class MockLLM:
    """No language-model call is performed; responses are explicitly labeled."""

    def __init__(self, system_name: str = "Gwas Manhattan Pvalue Cleaner"):
        self.system_name = system_name

    def invoke(self, prompt: str) -> str:
        PHIGuard.assert_no_phi(prompt)
        return (
            f"[{self.system_name} mock chat] No analysis or verification has been "
            "performed. The requested prompt is not processed by a model."
        )


class LLMFactory:
    """Provide mock mode only. Do not silently impersonate external providers."""

    @staticmethod
    def create(provider: str = "mock", system_name: str = "Gwas Manhattan Pvalue Cleaner"):
        prov = str(provider).lower()
        if prov in ("mock", "deterministic", "test"):
            return MockLLM(system_name)
        raise ValueError(
            f"Provider {provider!r} is not implemented; use 'mock' explicitly."
        )
