"""
Provider 配置管理器

管理不同 realtime provider 的配置信息和支持的功能
"""

import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class ProviderConfigManager:
    """管理不同 provider 的配置"""
    
    SUPPORTED_PROVIDERS = {
        'qwen': {
            'name': '通义千问',
            'display_name': 'Qwen Realtime',
            'features': ['audio', 'text', 'streaming'],
            'description': '阿里云通义千问实时语音对话'
        },
        'volc': {
            'name': '火山引擎',
            'display_name': 'Volcano Engine',
            'features': ['audio', 'text'],
            'description': '火山引擎实时语音对话'
        },
        # 可以轻松添加新的 provider
        # 'openai': {
        #     'name': 'OpenAI',
        #     'display_name': 'OpenAI Realtime',
        #     'features': ['audio', 'text', 'streaming', 'function_calling'],
        #     'description': 'OpenAI Realtime API'
        # }
    }
    
    @classmethod
    def get_provider_info(cls, provider: str) -> Optional[Dict]:
        """
        获取 provider 信息
        
        Args:
            provider: provider 名称
            
        Returns:
            provider 信息字典，如果不存在则返回 None
        """
        return cls.SUPPORTED_PROVIDERS.get(provider.lower())
    
    @classmethod
    def is_supported(cls, provider: str) -> bool:
        """
        检查是否支持该 provider
        
        Args:
            provider: provider 名称
            
        Returns:
            是否支持
        """
        return provider.lower() in cls.SUPPORTED_PROVIDERS
    
    @classmethod
    def list_providers(cls) -> List[Dict]:
        """
        列出所有支持的 provider
        
        Returns:
            provider 列表，包含 id, name, features 等信息
        """
        providers = []
        for provider_id, info in cls.SUPPORTED_PROVIDERS.items():
            providers.append({
                'id': provider_id,
                'name': info['name'],
                'display_name': info['display_name'],
                'features': info['features'],
                'description': info['description']
            })
        return providers
    
    @classmethod
    def validate_provider(cls, provider: str) -> tuple[bool, Optional[str]]:
        """
        验证 provider 是否有效
        
        Args:
            provider: provider 名称
            
        Returns:
            (是否有效, 错误消息)
        """
        if not provider:
            return False, "Provider 不能为空"
        
        if not cls.is_supported(provider):
            supported = ', '.join(cls.SUPPORTED_PROVIDERS.keys())
            return False, f"不支持的 provider: {provider}，支持的有: {supported}"
        
        return True, None
    
    @classmethod
    def get_provider_features(cls, provider: str) -> List[str]:
        """
        获取 provider 支持的功能
        
        Args:
            provider: provider 名称
            
        Returns:
            功能列表
        """
        info = cls.get_provider_info(provider)
        return info['features'] if info else []
    
    @classmethod
    def supports_feature(cls, provider: str, feature: str) -> bool:
        """
        检查 provider 是否支持特定功能
        
        Args:
            provider: provider 名称
            feature: 功能名称
            
        Returns:
            是否支持该功能
        """
        features = cls.get_provider_features(provider)
        return feature in features