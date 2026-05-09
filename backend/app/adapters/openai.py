import httpx
from app.adapters.base import ModelAdapter

class OpenAIAdapter(ModelAdapter):
    def __init__(self, api_key: str, base_url: str = None, model: str = "gpt-4"):
        self.api_key = api_key
        self.base_url = base_url or "https://api.openai.com/v1"
        self.model = model

    def _build_extra_params(self, config: dict) -> dict:
        """构建 DeepSeek 特有参数"""
        extra = {}
        if config.get("reasoning_effort"):
            extra["reasoning_effort"] = config["reasoning_effort"]
        if config.get("thinking"):
            extra["thinking"] = config["thinking"]
        return extra

    def send_message(self, messages: list, config: dict) -> str:
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": config.get("model", self.model),
            "messages": messages,
            "temperature": config.get("temperature", 0.7),
            "max_tokens": config.get("max_tokens", 4096)
        }
        extra_params = self._build_extra_params(config)
        data.update(extra_params)

        with httpx.Client(timeout=30.0) as client:
            response = client.post(url, json=data, headers=headers)
            response.raise_for_status()
            result = response.json()
            if "choices" not in result or not result["choices"]:
                raise ValueError(f"API error: {result}")
            return result["choices"][0]["message"]["content"]

    def stream_message(self, messages: list, config: dict):
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": config.get("model", self.model),
            "messages": messages,
            "temperature": config.get("temperature", 0.7),
            "max_tokens": config.get("max_tokens", 4096),
            "stream": True
        }
        extra_params = self._build_extra_params(config)
        data.update(extra_params)

        with httpx.Client(timeout=30.0) as client:
            with client.stream("POST", url, json=data, headers=headers) as response:
                response.raise_for_status()
                for chunk in response.iter_text():
                    if chunk.startswith("data: "):
                        yield chunk[6:]