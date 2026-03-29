"""
场景提示词模板管理服务
负责加载和管理各类场景的提示词模板文件
"""

import os
import logging
from typing import Optional
from pathlib import Path


logger = logging.getLogger(__name__)


class TemplateManager:
    """
    提示词模板管理器
    负责从文件系统加载模板文件
    """
    
    def __init__(self, template_dir: Optional[str] = None):
        """
        初始化模板管理器
        
        Args:
            template_dir: 模板文件目录，默认为 template/
        """
        if template_dir is None:
            # 默认模板目录：项目根目录下的 agent/template/
            current_file = Path(__file__)
            project_root = current_file.parent.parent.parent  # 从 agent/service/scene/ 往上三层
            template_dir = project_root / 'template'
        
        self.template_dir = Path(template_dir)
        
        if not self.template_dir.exists():
            logger.warning(f"模板目录不存在: {self.template_dir}")
            # 尝试创建目录
            try:
                self.template_dir.mkdir(parents=True, exist_ok=True)
                logger.info(f"已创建模板目录: {self.template_dir}")
            except Exception as e:
                logger.error(f"创建模板目录失败: {e}")
        
        logger.info(f"模板管理器初始化完成，模板目录: {self.template_dir}")
    
    def get_template(self, template_name: str) -> str:
        """
        获取指定名称的模板内容
        
        Args:
            template_name: 模板名称（不含扩展名，如 'training_sales'）
        
        Returns:
            模板文本内容
            
        Raises:
            FileNotFoundError: 模板文件不存在
            IOError: 读取文件失败
        """
        # 支持 .txt 和 .md 两种扩展名
        for ext in ['.txt', '.md']:
            template_path = self.template_dir / f"{template_name}{ext}"
            
            if template_path.exists():
                try:
                    with open(template_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    logger.info(f"成功加载模板: {template_path.name}")
                    return content
                    
                except Exception as e:
                    logger.error(f"读取模板文件失败 {template_path}: {e}")
                    raise IOError(f"读取模板文件失败: {e}")
        
        # 如果都找不到，抛出异常
        error_msg = f"模板文件不存在: {template_name}.txt 或 {template_name}.md (在目录 {self.template_dir})"
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)
    
    def template_exists(self, template_name: str) -> bool:
        """
        检查模板是否存在
        
        Args:
            template_name: 模板名称（不含扩展名）
            
        Returns:
            bool: 模板是否存在
        """
        for ext in ['.txt', '.md']:
            template_path = self.template_dir / f"{template_name}{ext}"
            if template_path.exists():
                return True
        return False
    
    def list_templates(self) -> list:
        """
        列出所有可用的模板
        
        Returns:
            list: 模板名称列表（不含扩展名）
        """
        templates = []
        
        if not self.template_dir.exists():
            return templates
        
        for file_path in self.template_dir.iterdir():
            if file_path.is_file() and file_path.suffix in ['.txt', '.md']:
                # 去掉扩展名
                template_name = file_path.stem
                if template_name not in templates:
                    templates.append(template_name)
        
        return sorted(templates)
    
    def get_template_path(self, template_name: str) -> Optional[Path]:
        """
        获取模板文件的完整路径
        
        Args:
            template_name: 模板名称（不含扩展名）
            
        Returns:
            Path: 模板文件路径，如果不存在则返回 None
        """
        for ext in ['.txt', '.md']:
            template_path = self.template_dir / f"{template_name}{ext}"
            if template_path.exists():
                return template_path
        
        return None
