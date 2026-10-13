"""Deterministic local chat stub.

No network LLM providers are implemented; unsupported providers are rejected.
"""
from .base import PHIGuard


class MockLLM:
    def __init__(self, system_name: str = "Secure Multiparty Clinical Trial"):
        self.system_name = system_name

    def invoke(self, prompt: str) -> str:
        PHIGuard.assert_no_phi(prompt)
        return (f"[{self.system_name} demo]: No clinical or cryptographic verification "
                f"was performed. Local mock response for query: {prompt[:60]!r}")


class LLMFactory:
    @staticmethod
    def create(provider: str = "mock", system_name: str = "Secure Multiparty Clinical Trial"):
        prov = str(provider).lower()
        if prov in ("mock", "deterministic", "test"):
            return MockLLM(system_name)
        raise ValueError(f"Provider {provider!r} is not implemented; use 'mock'")
