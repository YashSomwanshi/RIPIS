"""
AI Engine - Ollama/DeepSeek Integration for RIPIS
"""
import requests
import json
from typing import Generator, Optional
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import OLLAMA_MODEL, OLLAMA_HOST
from core.prompt_templates import INTERVIEWER_SYSTEM_PROMPT


class AIEngine:
    """Handles communication with Ollama/DeepSeek for interview responses."""
    
    def __init__(self):
        self.model = OLLAMA_MODEL
        self.host = OLLAMA_HOST
        self.conversation_history = []
        self.system_prompt = INTERVIEWER_SYSTEM_PROMPT
        
    def test_connection(self) -> bool:
        """Test if Ollama is running and model is available."""
        try:
            response = requests.get(f"{self.host}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get("models", [])
                model_names = [m.get("name", "") for m in models]
                # Check if our model is available (handle version tags)
                for name in model_names:
                    if self.model.split(":")[0] in name:
                        return True
                print(f"Model {self.model} not found. Available: {model_names}")
                return False
            return False
        except requests.exceptions.ConnectionError:
            print("Ollama is not running. Start it with 'ollama serve'")
            return False
        except Exception as e:
            print(f"Connection error: {e}")
            return False
    
    def reset_conversation(self):
        """Reset conversation history for a new interview."""
        self.conversation_history = []
    
    def generate_response(self, prompt: str, context: Optional[str] = None) -> str:
        """Generate a response from the AI model (non-streaming)."""
        messages = self._build_messages(prompt, context)
        
        print(f"[AI] Generating response for prompt: {prompt[:80]}...")
        
        try:
            response = requests.post(
                f"{self.host}/api/chat",
                json={
                    "model": self.model,
                    "messages": messages,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "top_p": 0.9,
                        "num_predict": 512  # Increased for better responses
                    }
                },
                timeout=120  # Increased timeout
            )
            
            print(f"[AI] Response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                assistant_message = result.get("message", {}).get("content", "")
                
                # Handle DeepSeek R1's <think> tags - extract only the final response
                assistant_message = self._clean_response(assistant_message)
                
                print(f"[AI] Got response: {assistant_message[:100] if assistant_message else 'EMPTY'}...")
                
                # Add to conversation history
                self.conversation_history.append({"role": "user", "content": prompt})
                self.conversation_history.append({"role": "assistant", "content": assistant_message})
                
                return assistant_message if assistant_message else "I'm here to help! Please go ahead."
            else:
                print(f"[AI] Error response: {response.text}")
                return f"I apologize, I'm having some trouble. Let me try again."
                
        except requests.exceptions.Timeout:
            print("[AI] Request timed out")
            return "I need a moment to think about that..."
        except Exception as e:
            print(f"[AI] Error: {e}")
            return f"I apologize for the technical issue. Please continue."
    
    def _clean_response(self, response: str) -> str:
        """Clean DeepSeek response by removing think tags and extracting content."""
        if not response:
            return ""
        
        import re
        
        # DeepSeek R1 uses <think>...</think> for reasoning
        # We want to extract only the final response after thinking
        
        # Remove <think>...</think> blocks completely
        cleaned = re.sub(r'<think>.*?</think>', '', response, flags=re.DOTALL)
        
        # Also handle case where response starts with thinking and ends with actual response
        if '</think>' in response:
            parts = response.split('</think>')
            if len(parts) > 1:
                cleaned = parts[-1]  # Take everything after the last </think>
        
        # Clean up whitespace
        cleaned = cleaned.strip()
        
        return cleaned
    
    def generate_response_stream(self, prompt: str, context: Optional[str] = None) -> Generator[str, None, None]:
        """Generate a streaming response from the AI model."""
        messages = self._build_messages(prompt, context)
        
        try:
            response = requests.post(
                f"{self.host}/api/chat",
                json={
                    "model": self.model,
                    "messages": messages,
                    "stream": True,
                    "options": {
                        "temperature": 0.7,
                        "top_p": 0.9,
                        "num_predict": 256
                    }
                },
                stream=True,
                timeout=60
            )
            
            full_response = ""
            for line in response.iter_lines():
                if line:
                    try:
                        data = json.loads(line)
                        chunk = data.get("message", {}).get("content", "")
                        full_response += chunk
                        yield chunk
                    except json.JSONDecodeError:
                        continue
            
            # Add to conversation history after streaming completes
            self.conversation_history.append({"role": "user", "content": prompt})
            self.conversation_history.append({"role": "assistant", "content": full_response})
            
        except Exception as e:
            yield f"Error: {str(e)}"
    
    def _build_messages(self, prompt: str, context: Optional[str] = None) -> list:
        """Build the messages array for the API call."""
        messages = [{"role": "system", "content": self.system_prompt}]
        
        # Add conversation history (keep last 10 exchanges for context)
        history_limit = 20  # 10 pairs of user/assistant
        recent_history = self.conversation_history[-history_limit:]
        messages.extend(recent_history)
        
        # Add context if provided
        if context:
            prompt = f"Context:\n{context}\n\n{prompt}"
        
        messages.append({"role": "user", "content": prompt})
        return messages
    
    def analyze_code(self, code: str, question: str) -> str:
        """Quick analysis of the candidate's code."""
        from core.prompt_templates import CODE_ANALYSIS_PROMPT
        prompt = CODE_ANALYSIS_PROMPT.format(code=code, question=question)
        return self.generate_response(prompt)


# Test the connection when run directly
if __name__ == "__main__":
    engine = AIEngine()
    if engine.test_connection():
        print("✓ Ollama connection successful!")
        print("Testing response generation...")
        response = engine.generate_response("Say 'Hello, I am Alex, your interviewer today!' in a friendly way.")
        print(f"Response: {response}")
    else:
        print("✗ Could not connect to Ollama")
