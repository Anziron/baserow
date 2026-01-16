import requests
from typing import Optional
from django.conf import settings


class AIHandler:
    """处理 AI 模型调用"""
    
    @staticmethod
    def call_openai_compatible(
        prompt: str,
        api_url: str,
        api_key: str,
        model: str = "gpt-3.5-turbo",
        max_tokens: int = 1000
    ) -> str:
        """
        调用 OpenAI 兼容的 API
        支持 OpenAI、Azure OpenAI、本地 LLM 等
        """
        
        if not api_key:
            return f"[模拟响应] 输入: {prompt[:50]}..."
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": max_tokens
        }
        
        try:
            response = requests.post(
                api_url,
                headers=headers,
                json=data,
                timeout=60
            )
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["message"]["content"]
        except Exception as e:
            return f"[AI 错误] {str(e)}"
    
    @staticmethod
    def process_with_template(
        input_value: str,
        prompt_template: str,
        api_url: str,
        api_key: str,
        model: str
    ) -> str:
        """使用模板处理输入"""
        
        # 替换模板中的占位符
        prompt = prompt_template.replace("{input}", str(input_value))
        
        return AIHandler.call_openai_compatible(
            prompt=prompt,
            api_url=api_url,
            api_key=api_key,
            model=model
        )
