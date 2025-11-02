"""
Ollama Service - Interface with Ollama API
"""
import requests
import json
from typing import Optional, Dict, List
import asyncio
from app.config import settings, MODEL_CONFIGS


class OllamaService:
    """
    Service to interact with Ollama API
    """
    
    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL
        self.model = settings.OLLAMA_MODEL
        self.timeout = settings.OLLAMA_TIMEOUT
        self.temperature = settings.OLLAMA_TEMPERATURE
    
    async def generate(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        stream: bool = False
    ) -> str:
        """
        Generate text using Ollama model
        """
        url = f"{self.base_url}/api/generate"
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "format": "json",
            "stream": stream,
            "options": {
                "temperature": temperature or self.temperature,
                "num_predict": 4096,  # Allow longer responses
                "top_k": 40,
                "top_p": 0.9,
            }
        }
        
        if system_prompt:
            payload["system"] = system_prompt
        
        try:
            response = requests.post(
                url,
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            if stream:
                return self._handle_streaming_response(response)
            else:
                result = response.json()
                return result.get("response", "")
        
        except requests.exceptions.Timeout:
            raise Exception(f"Ollama request timed out after {self.timeout} seconds")
        except requests.exceptions.ConnectionError:
            raise Exception(f"Cannot connect to Ollama at {self.base_url}. Is Ollama running?")
        except Exception as e:
            raise Exception(f"Ollama generation error: {str(e)}")
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None
    ) -> str:
        """
        Chat with Ollama model using conversation format
        """
        url = f"{self.base_url}/api/chat"
        
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature or self.temperature,
            }
        }
        
        try:
            response = requests.post(
                url,
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            result = response.json()
            return result.get("message", {}).get("content", "")
        
        except Exception as e:
            raise Exception(f"Ollama chat error: {str(e)}")
    
    async def generate_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        retry_attempts: int = 3
    ) -> Dict:
        """
        Generate JSON response with automatic retry on parse failures
        """
        for attempt in range(retry_attempts):
            try:
                print(f"Attempt {attempt + 1}/{retry_attempts} - Calling Ollama...")
                
                response_text = await self.generate(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    temperature=0.05  # Very low temperature for consistent JSON
                )
                
                print(f"Received response ({len(response_text)} chars)")
                
                # Try to extract JSON from response
                json_data = self._extract_json(response_text)
                
                print("Successfully parsed JSON")
                return json_data
            
            except json.JSONDecodeError as e:
                print(f"JSON parse error on attempt {attempt + 1}: {str(e)}")
                print(f"Response text: {response_text[:500]}...")  # Print first 500 chars
                
                if attempt < retry_attempts - 1:
                    # Retry with more explicit instructions
                    prompt = prompt + "\n\nRETURN ONLY VALID JSON. Start with { and end with }. No markdown, no code blocks."
                    await asyncio.sleep(2)
                else:
                    raise Exception(f"Failed to parse JSON after {retry_attempts} attempts: {str(e)}\nResponse: {response_text[:1000]}")
            except Exception as e:
                print(f"Error on attempt {attempt + 1}: {str(e)}")
                if attempt < retry_attempts - 1:
                    await asyncio.sleep(2)
                else:
                    raise e
    
    def _extract_json(self, text: str) -> Dict:
        """
        Extract JSON from text response (handles markdown code blocks)
        """
        # Remove markdown code blocks if present
        text = text.strip()
        
        # Try to find JSON in markdown code block
        if "```json" in text:
            start = text.find("```json") + 7
            end = text.find("```", start)
            text = text[start:end].strip()
        elif "```" in text:
            start = text.find("```") + 3
            end = text.find("```", start)
            text = text[start:end].strip()
        
        # Try to find JSON object boundaries
        if not text.startswith('{'):
            start = text.find('{')
            if start != -1:
                text = text[start:]
        
        if not text.endswith('}'):
            end = text.rfind('}')
            if end != -1:
                text = text[:end+1]
        
        # Parse JSON
        return json.loads(text)
    
    def _handle_streaming_response(self, response) -> str:
        """
        Handle streaming response from Ollama
        """
        full_response = ""
        
        for line in response.iter_lines():
            if line:
                try:
                    json_response = json.loads(line)
                    if "response" in json_response:
                        full_response += json_response["response"]
                except json.JSONDecodeError:
                    continue
        
        return full_response
    
    async def list_models(self) -> List[Dict]:
        """
        List available Ollama models
        """
        url = f"{self.base_url}/api/tags"
        
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            return result.get("models", [])
        
        except Exception as e:
            raise Exception(f"Failed to list models: {str(e)}")
    
    async def pull_model(self, model_name: str) -> bool:
        """
        Pull a model from Ollama registry
        """
        url = f"{self.base_url}/api/pull"
        
        payload = {
            "name": model_name,
            "stream": False
        }
        
        try:
            response = requests.post(url, json=payload, timeout=300)
            response.raise_for_status()
            return True
        
        except Exception as e:
            raise Exception(f"Failed to pull model: {str(e)}")
    
    def check_connection(self) -> bool:
        """
        Check if Ollama is accessible
        """
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False