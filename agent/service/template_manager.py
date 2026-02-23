import os
import logging
from typing import Dict, Optional
from pathlib import Path


class TemplateManager:
    def __init__(self, template_dir: Optional[str] = None):
        if template_dir:
            self.template_dir = Path(template_dir)
        else:
            self.template_dir = Path(__file__).parent.parent / "template"
        
        self._templates: Dict[str, str] = {}
        self._load_templates()
    
    def _load_templates(self):
        if not self.template_dir.exists():
            logging.warning(f"模板目录不存在: {self.template_dir}")
            return
        
        for template_file in self.template_dir.glob("*.txt"):
            template_name = template_file.stem
            try:
                with open(template_file, "r", encoding="utf-8") as f:
                    self._templates[template_name] = f.read()
                logging.info(f"加载模板: {template_name}")
            except Exception as e:
                logging.error(f"加载模板失败 {template_name}: {str(e)}")
    
    def get_template(self, template_name: str) -> Optional[str]:
        return self._templates.get(template_name)
    
    def get_template_names(self) -> list:
        return list(self._templates.keys())
    
    def fill_background_info(self, template: str, background_text: str) -> str:
        placeholder = "#背景信息："
        if placeholder in template:
            return template.replace(
                f"{placeholder}\n\n---",
                f"{placeholder}\n{background_text}\n---"
            )
        return template
    
    def fill_main_questions(self, template: str, questions_text: str) -> str:
        placeholder = "# 待提问主列表："
        if placeholder in template:
            return template.replace(
                f"{placeholder}\n\n",
                f"{placeholder}\n{questions_text}\n\n"
            )
        return template
    
    def fill_trigger_groups(self, template: str, trigger_groups_text: str) -> str:
        section_start = "# 关联问题"
        section_end = "# 防御性对话设计"
        
        if section_start not in template:
            return template
        
        start_idx = template.find(section_start)
        end_idx = template.find(section_end)
        
        if start_idx != -1 and end_idx != -1:
            header = template[:start_idx]
            footer = template[end_idx:]
            
            new_section = f"""# 关联问题
## 必须要满足触发关联问题规则：
- 在命中"对方话术中触发问题的关键信息"中的任意关键字或语义近似，均触发该分组中的触发问题列表问题。
- 在触发关联问题后，如果是陈述句，不允许在陈述句后加【待提问主列表】中的问题
	
{trigger_groups_text}

"""
            return header + new_section + footer
        
        return template
    
    def generate_full_prompt(self, template_name: str, 
                             background_text: str,
                             questions_text: str,
                             trigger_groups_text: str) -> str:
        template = self.get_template(template_name)
        if not template:
            raise ValueError(f"模板不存在: {template_name}")
        
        result = self.fill_background_info(template, background_text)
        result = self.fill_main_questions(result, questions_text)
        result = self.fill_trigger_groups(result, trigger_groups_text)
        
        return result
