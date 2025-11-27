# screening/services/ollama_client.py

import aiohttp
import json
from typing import Optional, Dict
from config import OLLAMA_BASE_URL, OLLAMA_MODEL, OLLAMA_TIMEOUT


class OllamaClient:
    """Async client for Ollama API"""
    
    def __init__(self, base_url: str = OLLAMA_BASE_URL, model: str = OLLAMA_MODEL):
        self.base_url = base_url
        self.model = model
        self.endpoint = f"{base_url}/api/generate"
    
    async def query(self, prompt: str, temperature: float = 0.7, max_tokens: int = 2000) -> str:
        """
        Send a query to Ollama and return the response
        
        Args:
            prompt: The prompt to send
            temperature: Sampling temperature (0.0 - 1.0)
            max_tokens: Maximum tokens to generate
            
        Returns:
            Response text from the model
        """
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            }
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.endpoint,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=OLLAMA_TIMEOUT)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result.get("response", "")
                    else:
                        error_text = await response.text()
                        raise Exception(f"Ollama API error: {response.status} - {error_text}")
        
        except aiohttp.ClientError as e:
            raise Exception(f"Failed to connect to Ollama: {str(e)}")
        except Exception as e:
            raise Exception(f"Ollama query failed: {str(e)}")
    
    async def query_with_retry(self, prompt: str, max_retries: int = 3) -> str:
        """
        Query with automatic retry on failure
        
        Args:
            prompt: The prompt to send
            max_retries: Maximum number of retry attempts
            
        Returns:
            Response text from the model
        """
        last_error = None
        
        for attempt in range(max_retries):
            try:
                return await self.query(prompt)
            except Exception as e:
                last_error = e
                if attempt < max_retries - 1:
                    print(f"Retry {attempt + 1}/{max_retries} after error: {str(e)}")
                    continue
        
        raise Exception(f"Failed after {max_retries} attempts: {str(last_error)}")
    
    async def health_check(self) -> bool:
        """
        Check if Ollama is running and accessible
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/api/tags",
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    return response.status == 200
        except:
            return False