"""
Base LLM Provider Interface

Defines the abstract interface that all LLM providers must implement.
"""

import time
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Tuple
from contextlib import contextmanager

from ....utils.logging.setup import get_logger

logger = get_logger(__name__)


class LLMError(Exception):
    """Base exception for LLM-related errors"""
    pass


class LLMConnectionError(LLMError):
    """Exception raised when connection to LLM fails"""
    pass


class LLMAnalysisError(LLMError):
    """Exception raised when LLM analysis fails"""
    pass


class LLMResponse:
    """Standardized response object for LLM operations"""
    
    def __init__(
        self,
        content: str,
        usage: Optional[Dict[str, int]] = None,
        model: Optional[str] = None,
        provider: Optional[str] = None,
        response_time: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.content = content
        self.usage = usage or {}
        self.model = model
        self.provider = provider
        self.response_time = response_time
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert response to dictionary"""
        return {
            'content': self.content,
            'usage': self.usage,
            'model': self.model,
            'provider': self.provider,
            'response_time': self.response_time,
            'metadata': self.metadata
        }


class BaseLLMProvider(ABC):
    """
    Abstract base class for all LLM providers.
    Defines the interface that all providers must implement.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the provider with configuration
        
        Args:
            config: Provider configuration dictionary
        """
        self.config = config
        self.provider_name = self.__class__.__name__.replace('Provider', '').lower()
        
        # Basic configuration
        self.max_retries = config.get('max_retries', 3)
        self.retry_delay = config.get('retry_delay', 2)
        self.timeout = config.get('timeout', 30)
        
        # Model parameters
        self.temperature = config.get('temperature', 0.1)
        self.max_tokens = config.get('max_tokens', 512)
        self.model = config.get('model', self._get_default_model())
        
        # Connection health tracking
        self._connection_healthy = None
        self._last_health_check = 0
        self._health_check_interval = 30  # seconds
        
        # Performance tracking
        self._total_requests = 0
        self._total_tokens = 0
        self._total_response_time = 0.0
        
        logger.info(f"{self.provider_name} provider initialized - Model: {self.model}")
    
    @abstractmethod
    def _get_default_model(self) -> str:
        """Get the default model for this provider"""
        pass
    
    @abstractmethod
    def _make_request(self, prompt: str, **kwargs) -> LLMResponse:
        """
        Make a request to the LLM provider
        
        Args:
            prompt: The prompt to send
            **kwargs: Additional parameters
            
        Returns:
            LLMResponse object
            
        Raises:
            LLMConnectionError: If connection fails
            LLMAnalysisError: If analysis fails
        """
        pass
    
    @abstractmethod
    def _check_connection(self) -> bool:
        """
        Check if the provider is available and healthy
        
        Returns:
            True if healthy, False otherwise
        """
        pass
    
    @abstractmethod
    def get_available_models(self) -> List[str]:
        """
        Get list of available models for this provider
        
        Returns:
            List of model names
        """
        pass
    
    def generate_response(self, prompt: str, **kwargs) -> LLMResponse:
        """
        Generate a response from the LLM with retry logic
        
        Args:
            prompt: The prompt to send
            **kwargs: Additional parameters
            
        Returns:
            LLMResponse object
            
        Raises:
            LLMConnectionError: If all retries fail
            LLMAnalysisError: If analysis fails
        """
        if not prompt or not prompt.strip():
            raise LLMAnalysisError("Prompt cannot be empty")
        
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                start_time = time.time()
                
                # Make the request
                response = self._make_request(prompt, **kwargs)
                
                # Track performance
                response_time = time.time() - start_time
                response.response_time = response_time
                response.provider = self.provider_name
                
                self._update_metrics(response)
                
                logger.debug(f"LLM request successful in {response_time:.3f}s")
                return response
                
            except (LLMConnectionError, LLMAnalysisError) as e:
                last_exception = e
                
                if attempt < self.max_retries:
                    wait_time = self.retry_delay * (2 ** attempt)  # Exponential backoff
                    logger.warning(f"LLM request failed (attempt {attempt + 1}), retrying in {wait_time}s: {e}")
                    time.sleep(wait_time)
                else:
                    logger.error(f"LLM request failed after {self.max_retries + 1} attempts: {e}")
        
        # All retries failed
        raise LLMConnectionError(f"Failed after {self.max_retries + 1} attempts: {last_exception}")
    
    def generate_batch_responses(
        self, 
        prompts: List[str], 
        **kwargs
    ) -> List[LLMResponse]:
        """
        Generate responses for multiple prompts
        
        Args:
            prompts: List of prompts
            **kwargs: Additional parameters
            
        Returns:
            List of LLMResponse objects
        """
        responses = []
        
        for i, prompt in enumerate(prompts):
            try:
                response = self.generate_response(prompt, **kwargs)
                responses.append(response)
                logger.debug(f"Batch request {i+1}/{len(prompts)} completed")
            except Exception as e:
                logger.error(f"Batch request {i+1}/{len(prompts)} failed: {e}")
                # Create error response
                error_response = LLMResponse(
                    content="",
                    metadata={'error': str(e), 'batch_index': i}
                )
                responses.append(error_response)
        
        return responses
    
    def is_healthy(self) -> bool:
        """
        Check if the provider is healthy (with caching)
        
        Returns:
            True if healthy, False otherwise
        """
        current_time = time.time()
        
        # Use cached result if recent
        if (self._connection_healthy is not None and 
            current_time - self._last_health_check < self._health_check_interval):
            return self._connection_healthy
        
        # Perform health check
        try:
            self._connection_healthy = self._check_connection()
            self._last_health_check = current_time
            
            if self._connection_healthy:
                logger.debug(f"{self.provider_name} provider is healthy")
            else:
                logger.warning(f"{self.provider_name} provider is unhealthy")
                
        except Exception as e:
            logger.error(f"{self.provider_name} health check failed: {e}")
            self._connection_healthy = False
        
        return self._connection_healthy
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the current model
        
        Returns:
            Dictionary with model information
        """
        return {
            'provider': self.provider_name,
            'model': self.model,
            'temperature': self.temperature,
            'max_tokens': self.max_tokens,
            'timeout': self.timeout,
            'healthy': self.is_healthy()
        }
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get performance metrics for this provider
        
        Returns:
            Dictionary with performance metrics
        """
        avg_response_time = (
            self._total_response_time / self._total_requests 
            if self._total_requests > 0 else 0
        )
        
        return {
            'provider': self.provider_name,
            'total_requests': self._total_requests,
            'total_tokens': self._total_tokens,
            'average_response_time': round(avg_response_time, 3),
            'total_response_time': round(self._total_response_time, 3)
        }
    
    def _update_metrics(self, response: LLMResponse):
        """Update performance metrics"""
        self._total_requests += 1
        if response.response_time:
            self._total_response_time += response.response_time
        if response.usage:
            self._total_tokens += response.usage.get('total_tokens', 0)
    
    @contextmanager
    def _request_context(self):
        """Context manager for request handling"""
        start_time = time.time()
        try:
            yield
        finally:
            end_time = time.time()
            logger.debug(f"Request completed in {end_time - start_time:.3f}s")


__all__ = [
    'BaseLLMProvider',
    'LLMResponse', 
    'LLMError',
    'LLMConnectionError',
    'LLMAnalysisError'
]