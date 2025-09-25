"""
OpenAI LLM Provider Implementation

Provides OpenAI GPT model integration with connection pooling and optimizations.
"""

import json
import time
from typing import Dict, List, Optional, Any

from .base import BaseLLMProvider, LLMResponse, LLMConnectionError, LLMAnalysisError
from ....utils.logging.setup import get_logger

logger = get_logger(__name__)


class OpenAIProvider(BaseLLMProvider):
    """
    OpenAI API provider implementation.
    Supports GPT-4o, GPT-4-turbo, GPT-4, GPT-3.5-turbo, and other OpenAI models.
    """
    
    # OpenAI model definitions with metadata
    AVAILABLE_MODELS = {
        'gpt-4o-mini': {
            'name': 'gpt-4o-mini',
            'description': '🚀 FASTEST: Ultra-fast GPT-4-level model. 60% cheaper than gpt-4o.',
            'context_window': 128000,
            'recommended': True,
            'tier': 'gpt-4-mini',
            'speed': 'ultra-fast',
            'cost': 'ultra-cheap'
        },
        'gpt-4o': {
            'name': 'gpt-4o',
            'description': 'Fastest and cheapest GPT-4-tier model. High quality.',
            'context_window': 128000,
            'recommended': True,
            'tier': 'gpt-4'
        },
        'gpt-4-turbo': {
            'name': 'gpt-4-turbo',
            'description': 'GPT-4-based model optimized for performance and cost.',
            'context_window': 128000,
            'recommended': True,
            'tier': 'gpt-4'
        },
        'gpt-4': {
            'name': 'gpt-4',
            'description': 'Original GPT-4. Slower and more expensive.',
            'context_window': 8192,
            'recommended': False,
            'tier': 'gpt-4'
        },
        'gpt-3.5-turbo': {
            'name': 'gpt-3.5-turbo',
            'description': 'Lightweight GPT-3.5 model. Cheaper and faster.',
            'context_window': 16385,
            'recommended': True,
            'tier': 'gpt-3.5'
        }
    }
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize OpenAI provider with optimizations"""
        super().__init__(config)
        
        # OpenAI-specific configuration
        self.api_key = config.get('api_key')
        self.base_url = config.get('base_url', 'https://api.openai.com/v1')
        
        # Validate API key
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
        
        # Initialize OpenAI client with connection pooling
        self._initialize_client()
        
        logger.info(f"OpenAI provider initialized - Model: {self.model}, Timeout: {self.timeout}s")
    
    def _get_default_model(self) -> str:
        """Get the default model for OpenAI"""
        return 'gpt-4o-mini'  # Fast and cost-effective default
    
    def _initialize_client(self):
        """Initialize OpenAI client with connection pooling"""
        try:
            import openai
            import httpx
            
            # Create HTTP client with connection pooling
            http_client = httpx.Client(
                timeout=self.timeout,
                limits=httpx.Limits(
                    max_keepalive_connections=20,  # Connection pool size
                    max_connections=100,           # Max total connections
                    keepalive_expiry=30           # Keep connections alive for 30s
                ),
                headers={
                    "User-Agent": "ContractAnalyzer/1.1.0",
                    "Connection": "keep-alive"
                }
            )
            
            self.client = openai.OpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
                timeout=self.timeout,
                max_retries=2,  # Reduced retries for speed
                http_client=http_client
            )
            
            logger.debug("OpenAI client initialized with connection pooling")
            
        except ImportError as e:
            raise LLMConnectionError(f"OpenAI library not installed: {e}")
        except Exception as e:
            raise LLMConnectionError(f"Failed to initialize OpenAI client: {e}")
    
    def _make_request(self, prompt: str, **kwargs) -> LLMResponse:
        """
        Make a request to OpenAI API
        
        Args:
            prompt: The prompt to send
            **kwargs: Additional parameters
            
        Returns:
            LLMResponse object
        """
        try:
            # Prepare request parameters
            request_params = {
                'model': kwargs.get('model', self.model),
                'messages': [{'role': 'user', 'content': prompt}],
                'temperature': kwargs.get('temperature', self.temperature),
                'max_tokens': kwargs.get('max_tokens', self.max_tokens),
                'top_p': kwargs.get('top_p', 0.9),
                'frequency_penalty': kwargs.get('frequency_penalty', 0),
                'presence_penalty': kwargs.get('presence_penalty', 0)
            }
            
            # Make API call
            start_time = time.time()
            response = self.client.chat.completions.create(**request_params)
            response_time = time.time() - start_time
            
            # Extract response content
            if not response.choices:
                raise LLMAnalysisError("No response choices returned from OpenAI")
            
            content = response.choices[0].message.content
            if not content:
                raise LLMAnalysisError("Empty response content from OpenAI")
            
            # Prepare usage information
            usage = {}
            if hasattr(response, 'usage') and response.usage:
                usage = {
                    'prompt_tokens': response.usage.prompt_tokens,
                    'completion_tokens': response.usage.completion_tokens,
                    'total_tokens': response.usage.total_tokens
                }
            
            # Create response object
            llm_response = LLMResponse(
                content=content.strip(),
                usage=usage,
                model=response.model,
                provider='openai',
                response_time=response_time,
                metadata={
                    'finish_reason': response.choices[0].finish_reason,
                    'response_id': response.id,
                    'created': response.created
                }
            )
            
            logger.debug(f"OpenAI request successful - Tokens: {usage.get('total_tokens', 0)}")
            return llm_response
            
        except Exception as e:
            if "rate limit" in str(e).lower():
                raise LLMConnectionError(f"OpenAI rate limit exceeded: {e}")
            elif "timeout" in str(e).lower():
                raise LLMConnectionError(f"OpenAI request timeout: {e}")
            elif "connection" in str(e).lower():
                raise LLMConnectionError(f"OpenAI connection error: {e}")
            elif "authentication" in str(e).lower():
                raise LLMConnectionError(f"OpenAI authentication failed: {e}")
            else:
                raise LLMAnalysisError(f"OpenAI request failed: {e}")
    
    def _check_connection(self) -> bool:
        """
        Check OpenAI API connectivity
        
        Returns:
            True if connection is healthy
        """
        try:
            # Make a lightweight request to test connectivity
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{'role': 'user', 'content': 'test'}],
                max_tokens=1,
                temperature=0
            )
            return True
            
        except Exception as e:
            logger.warning(f"OpenAI health check failed: {e}")
            return False
    
    def get_available_models(self) -> List[str]:
        """
        Get list of available OpenAI models
        
        Returns:
            List of model names
        """
        try:
            # Try to get models from API
            models_response = self.client.models.list()
            api_models = [model.id for model in models_response.data]
            
            # Filter to only include models we support
            supported_models = []
            for model_id in api_models:
                if model_id in self.AVAILABLE_MODELS:
                    supported_models.append(model_id)
            
            return supported_models if supported_models else list(self.AVAILABLE_MODELS.keys())
            
        except Exception as e:
            logger.warning(f"Failed to fetch OpenAI models from API: {e}")
            # Return our known models as fallback
            return list(self.AVAILABLE_MODELS.keys())
    
    def get_model_metadata(self, model_name: str) -> Dict[str, Any]:
        """
        Get metadata for a specific model
        
        Args:
            model_name: Name of the model
            
        Returns:
            Model metadata dictionary
        """
        return self.AVAILABLE_MODELS.get(model_name, {})
    
    def estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for text (rough approximation)
        
        Args:
            text: Text to estimate
            
        Returns:
            Estimated token count
        """
        # Rough estimation: 1 token ≈ 4 characters for English text
        return len(text) // 4
    
    def validate_model(self, model_name: str) -> bool:
        """
        Validate if a model is supported
        
        Args:
            model_name: Model name to validate
            
        Returns:
            True if model is supported
        """
        return model_name in self.AVAILABLE_MODELS
    
    def get_recommended_models(self) -> List[str]:
        """
        Get list of recommended models
        
        Returns:
            List of recommended model names
        """
        return [
            name for name, info in self.AVAILABLE_MODELS.items()
            if info.get('recommended', False)
        ]
    
    def switch_model(self, model_name: str) -> bool:
        """
        Switch to a different model
        
        Args:
            model_name: Name of the model to switch to
            
        Returns:
            True if switch was successful
        """
        if not self.validate_model(model_name):
            logger.error(f"Invalid model name: {model_name}")
            return False
        
        old_model = self.model
        self.model = model_name
        
        logger.info(f"Switched from {old_model} to {model_name}")
        return True


def create_openai_provider(config: Dict[str, Any]) -> OpenAIProvider:
    """
    Factory function to create OpenAI provider
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Configured OpenAI provider instance
    """
    return OpenAIProvider(config)


__all__ = ['OpenAIProvider', 'create_openai_provider']