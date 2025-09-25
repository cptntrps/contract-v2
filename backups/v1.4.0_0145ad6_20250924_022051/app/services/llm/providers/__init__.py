"""
LLM Provider Package

Factory functions and provider registry for different LLM providers.
"""

from typing import Dict, Any, Type, Optional
from .base import BaseLLMProvider, LLMError, LLMConnectionError, LLMAnalysisError
from .openai import OpenAIProvider

# Provider registry
PROVIDER_REGISTRY: Dict[str, Type[BaseLLMProvider]] = {
    'openai': OpenAIProvider,
}


def create_llm_provider(provider_name: str, config: Dict[str, Any]) -> BaseLLMProvider:
    """
    Factory function to create LLM providers
    
    Args:
        provider_name: Name of the provider ('openai', etc.)
        config: Provider configuration
        
    Returns:
        Configured provider instance
        
    Raises:
        ValueError: If provider is not supported
        LLMError: If provider initialization fails
    """
    provider_class = PROVIDER_REGISTRY.get(provider_name.lower())
    
    if not provider_class:
        available_providers = list(PROVIDER_REGISTRY.keys())
        raise ValueError(f"Unsupported provider '{provider_name}'. Available: {available_providers}")
    
    try:
        return provider_class(config)
    except Exception as e:
        raise LLMError(f"Failed to initialize {provider_name} provider: {e}")


def get_available_providers() -> list[str]:
    """
    Get list of available provider names
    
    Returns:
        List of provider names
    """
    return list(PROVIDER_REGISTRY.keys())


def register_provider(name: str, provider_class: Type[BaseLLMProvider]):
    """
    Register a new provider
    
    Args:
        name: Provider name
        provider_class: Provider class
    """
    PROVIDER_REGISTRY[name.lower()] = provider_class


__all__ = [
    'BaseLLMProvider',
    'OpenAIProvider', 
    'LLMError',
    'LLMConnectionError',
    'LLMAnalysisError',
    'create_llm_provider',
    'get_available_providers',
    'register_provider'
]