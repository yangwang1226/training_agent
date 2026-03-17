"""
SOP质检项智能提取服务
"""
import os
import json
import logging
from typing import List, Dict, Any, Optional

from langchain_core.messages import HumanMessage, SystemMessage

logger = logging.getLogger(__name__)


class SOPExtractionService:
    """SOP质检项智能提取服务"""
    
    def __init__(self):
        import dashscope
        from dashscope import MultiModalConversation
        
        dashscope.api_key = os.getenv("DASHSCOPE_API_KEY")
        self.llm_model = os.getenv("QWEN_PLUS_MODEL", "qwen-plus")
        self.generation = MultiModalConversation
        
        logger.info(f"SOP提取服务初始化完成，使用模型：{self.llm_model}")
    
    def _call_model(self, messages: List, temperature: float = 0.7) -> str:
        """调用 Qwen 模型"""
        formatted_messages = []
        for msg in messages:
            if isinstance(msg, SystemMessage):
                formatted_messages.append({
                    "role": "system", 
                    "content": [{"text": msg.content}]
                })
            elif isinstance(msg, HumanMessage):
                formatted_messages.append({
                    "role": "user", 
                    "content": [{"text": msg.content}]
                })
        
        response = self.generation.call(
            model=self.llm_model,
            messages=formatted_messages,
            temperature=temperature
        )
        
        if response.status_code == 200:
            return response.output.choices[0].message.content[0]["text"]
        else:
            raise Exception(f"Qwen API error: {response.code}")
    
    def extract_from_text(
        self,
        scene_code: str,
        text_content: str,
        scene_description: str = "",
        extract_must_do: bool = True,
        extract_must_not: bool = True,
        extract_should_do: bool = True,
        auto_scoring: bool = True
    ) -> List[Dict[str, Any]]:
        """
        从文本中智能提取质检项
        
        Args:
            scene_code: 场景代码
            text_content: SOP文档或对话文本
            scene_description: 场景描述
            extract_must_do: 是否提取必须项
            extract_must_not: 是否提取禁止项
            extract_should_do: 是否提取建议项
            auto_scoring: 是否自动评分
            
        Returns:
            质检项列表
        """
        try:
            # 构建提取类型说明
            extract_types = []
            if extract_must_do:
                extract_types.append("must_do (必须做的事项)")
            if extract_must_not:
                extract_types.append("must_not_do (禁止做的事项)")
            if extract_should_do:
                extract_types.append("should_do (建议做的事项)")
            
            types_text = "、".join(extract_types)
            
            prompt = f"""你是一位专业的SOP质检专家。请从以下文本中提取销售场景的质检项。

【场景信息】
场景：{scene_code}
描述：{scene_description if scene_description else "无"}

【待分析文本】
{text_content}

【提取要求】
1. 提取类型：{types_text}
2. 每个质检项需包含：
   - item_name: 质检项名称（简洁明确，15字以内）
   - check_type: must_do（必须做）/ must_not_do（禁止做）/ should_do（建议做）
   - keywords: 关键词列表，用于AI判断（3-5个关键词）
   - category: 分类标签（如：greeting开场、needs_analysis需求分析、product_intro产品介绍、closing结束、compliance合规）
   - item_desc: 详细描述和要求（50字以内）
   - importance_level: 重要性等级（critical/high/medium/low）

3. 重要性等级判断标准：
   - critical（关键）：法律合规要求、品牌形象关键、客户安全相关
     示例：合规声明、禁止虚假宣传、必须确认客户身份
   - high（重要）：业务流程关键环节、直接影响转化率
     示例：需求挖掘、异议处理、促成技巧
   - medium（一般）：流程完整性、标准化要求
     示例：自我介绍、产品介绍、结束感谢
   - low（加分）：体验优化、额外服务
     示例：个性化称呼、情绪共鸣、额外关怀

4. 注意事项：
   - 质检项要具体可判断，避免模糊表述
   - 关键词要准确，便于AI识别
   - 合理分类，便于管理
   - must_do和must_not_do是核心项，数量控制在5-10个
   - should_do可以多一些，控制在10-15个

请严格按照以下JSON格式输出：
{{
    "checklist": [
        {{
            "item_name": "30秒内主动问候客户",
            "check_type": "must_do",
            "keywords": ["您好", "欢迎", "问候", "打招呼"],
            "category": "greeting",
            "item_desc": "销售人员应在对话开始30秒内主动向客户问好，表现出热情和专业",
            "importance_level": "high"
        }}
    ]
}}
"""
            
            logger.info(f"开始从文本提取SOP质检项，场景：{scene_code}")
            
            response = self._call_model([
                SystemMessage(content="你是专业的SOP质检专家，擅长从文本中提取结构化的质检标准。"),
                HumanMessage(content=prompt)
            ])
            
            # 解析JSON
            result_json = self._extract_json(response)
            result = json.loads(result_json)
            
            checklist = result.get('checklist', [])
            
            # 为每个质检项生成ID
            for idx, item in enumerate(checklist):
                item['item_id'] = f"SOP_{idx+1:03d}"
            
            logger.info(f"成功提取 {len(checklist)} 个质检项")
            
            # 自动评分
            if auto_scoring and checklist:
                from .sop_scoring_service import sop_scoring_service
                
                logger.info("开始自动评分...")
                
                for item in checklist:
                    # 计算分数
                    item = sop_scoring_service.calculate_item_score(item)
                
                # 平衡总分到100分
                checklist = sop_scoring_service.balance_scores(checklist, 100)
                
                total_score = sum(i.get('final_score', 0) for i in checklist)
                logger.info(f"自动评分完成，总分：{total_score}")
            
            return checklist
            
        except Exception as e:
            logger.error(f"从文本提取质检项失败: {e}", exc_info=True)
            raise
    
    def _extract_json(self, text: str) -> str:
        """从文本中提取JSON"""
        text = text.strip()
        
        # 移除markdown代码块
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
        
        # 查找JSON对象
        start_idx = text.find("{")
        if start_idx == -1:
            return text
        
        # 匹配括号
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


# 全局服务实例
sop_extraction_service = SOPExtractionService()