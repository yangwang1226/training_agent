import os
import json
import logging
import requests
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass
class LLMConfig:
    api_key: str
    api_base: str
    model_name: str
    temperature: float = 0.7
    max_tokens: int = 4096


class LLMClient:
    def __init__(self, config: Optional[LLMConfig] = None):
        if config:
            self.config = config
        else:
            self.config = LLMConfig(
                api_key=os.getenv("AZURE_OPENAI_API_KEY", "c8575027653b42b1b47747f0b4ab135b"),
                api_base=os.getenv("AZURE_OPENAI_ENDPOINT", "https://menshen.test.xdf.cn/"),
                model_name=os.getenv("LLM_MODEL_NAME", "deepseek-r1"),
                temperature=0.7,
                max_tokens=4096
            )
    
    def _build_messages(self, system_prompt: str, user_prompt: str) -> List[Dict]:
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    
    def call(self, system_prompt: str, user_prompt: str, 
             temperature: Optional[float] = None) -> str:
        messages = self._build_messages(system_prompt, user_prompt)
        
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.config.model_name,
            "messages": messages,
            "temperature": temperature or self.config.temperature,
            "max_tokens": self.config.max_tokens
        }
        
        try:
            response = requests.post(
                f"{self.config.api_base}v1/chat/completions",
                headers=headers,
                json=data,
                timeout=120
            )
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["message"]["content"]
        except Exception as e:
            logging.error(f"LLM调用失败: {str(e)}")
            raise
    
    async def async_call(self, system_prompt: str, user_prompt: str,
                         temperature: Optional[float] = None) -> str:
        import aiohttp
        
        messages = self._build_messages(system_prompt, user_prompt)
        
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.config.model_name,
            "messages": messages,
            "temperature": temperature or self.config.temperature,
            "max_tokens": self.config.max_tokens
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.config.api_base}v1/chat/completions",
                    headers=headers,
                    json=data,
                    timeout=aiohttp.ClientTimeout(total=120)
                ) as response:
                    response.raise_for_status()
                    result = await response.json()
                    return result["choices"][0]["message"]["content"]
        except Exception as e:
            logging.error(f"LLM异步调用失败: {str(e)}")
            raise
    
    def call_with_json_output(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        response = self.call(system_prompt, user_prompt)
        logging.debug(f"LLM原始响应: {response[:1000] if len(response) > 1000 else response}")
        try:
            json_str = self._extract_json(response)
            if not json_str or json_str.strip() == "":
                logging.error(f"无法从响应中提取JSON，原始响应: {response}")
                raise json.JSONDecodeError("Empty JSON response", response, 0)
            json_str = self._clean_json_string(json_str)
            json_str = self._repair_incomplete_json(json_str)
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            logging.error(f"JSON解析失败: {str(e)}")
            logging.error(f"提取的JSON字符串: {json_str[:500] if json_str else 'None'}")
            logging.error(f"原始响应长度: {len(response)}")
            raise
    
    def _repair_incomplete_json(self, json_str: str) -> str:
        try:
            json.loads(json_str)
            return json_str
        except json.JSONDecodeError:
            pass
        
        open_braces = json_str.count('{') - json_str.count('}')
        open_brackets = json_str.count('[') - json_str.count(']')
        
        if open_braces > 0 or open_brackets > 0:
            json_str = json_str.rstrip(',')
            json_str = json_str.rstrip()
            
            for _ in range(open_brackets):
                json_str += ']'
            for _ in range(open_braces):
                json_str += '}'
            
            logging.warning(f"JSON不完整，尝试修复: 添加了 {open_brackets} 个 ']' 和 {open_braces} 个 '}}'")
        
        return json_str
    
    def _extract_json(self, text: str) -> str:
        text = text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
        
        start_idx = text.find("{")
        if start_idx == -1:
            return text
        
        depth = 0
        in_string = False
        escape_next = False
        
        for i in range(start_idx, len(text)):
            char = text[i]
            
            if escape_next:
                escape_next = False
                continue
            
            if char == '\\' and in_string:
                escape_next = True
                continue
            
            if char == '"':
                in_string = not in_string
                continue
            
            if not in_string:
                if char == '{':
                    depth += 1
                elif char == '}':
                    depth -= 1
                    if depth == 0:
                        return text[start_idx:i + 1]
        
        return text[start_idx:]
    
    def _clean_json_string(self, json_str: str) -> str:
        result = []
        i = 0
        in_string = False
        escape_next = False
        
        while i < len(json_str):
            char = json_str[i]
            
            if escape_next:
                result.append(char)
                escape_next = False
                i += 1
                continue
            
            if char == '\\' and in_string:
                result.append(char)
                escape_next = True
                i += 1
                continue
            
            if char == '"':
                in_string = not in_string
                result.append(char)
                i += 1
                continue
            
            if in_string:
                if char == '\n':
                    result.append('\\n')
                elif char == '\r':
                    result.append('\\r')
                elif char == '\t':
                    result.append('\\t')
                else:
                    result.append(char)
            else:
                result.append(char)
            
            i += 1
        
        return ''.join(result)
