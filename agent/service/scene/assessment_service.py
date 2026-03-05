"""
场景对练评估报告生成服务

基于对话转录和考核维度生成详细的评估报告
"""
import os
import json
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import JsonOutputParser

from dotenv import load_dotenv
load_dotenv()

from .prompts import ASSESSMENT_REPORT_PROMPT

logger = logging.getLogger(__name__)


class SceneAssessmentService:
    """
    场景对练评估报告生成服务
    
    基于对话转录和考核维度生成详细的评估报告，保存到数据库
    """
    
    def __init__(self):
        # 初始化 LLM (使用 Qwen Plus 3.5)
        import dashscope
        from dashscope import MultiModalConversation
        
        dashscope.api_key = os.getenv("DASHSCOPE_API_KEY")
        self.llm_model = os.getenv("QWEN_PLUS_MODEL", "qwen3.5-plus")
        self.generation = MultiModalConversation
        
        logger.info(f"评估服务初始化完成，使用模型：{self.llm_model}")

    def _call_model(self, messages: List, temperature: float = 0.3) -> str:
        """调用 Qwen 模型"""
        formatted_messages = []
        for msg in messages:
            if isinstance(msg, SystemMessage):
                formatted_messages.append({"role": "system", "content": [{"text": msg.content}]})
            elif isinstance(msg, HumanMessage):
                formatted_messages.append({"role": "user", "content": [{"text": msg.content}]})
            elif isinstance(msg, dict):
                if isinstance(msg.get("content"), list):
                    formatted_messages.append(msg)
                else:
                    formatted_messages.append({"role": msg.get("role", "user"), "content": [{"text": msg.get("content", "")}]})
            else:
                formatted_messages.append({"role": "user", "content": [{"text": str(msg)}]})
        
        response = self.generation.call(
            model=self.llm_model,
            enable_thinking=False,
            messages=formatted_messages,
            temperature=temperature
        )
        
        if response.status_code == 200:
            return response.output.choices[0].message.content[0]["text"]
        else:
            raise Exception(f"Qwen API error: {response.code} - {response.message}")

    def generate_report(
        self,
        session_id: str,
        transcript: str,
        dimensions: List[Dict[str, Any]],
        industry: str = "",
        role_type: str = "",
        background_info: str = ""
    ) -> Optional[Dict[str, Any]]:
        """
        生成评估报告
        
        Args:
            session_id: 训练会话 ID
            transcript: 对话转录文字
            dimensions: 考核维度列表
            industry: 行业
            role_type: 角色类型
            background_info: 场景背景信息
            
        Returns:
            评估报告字典，如果生成失败则返回 None
        """
        try:
            logger.info("=" * 50)
            logger.info("开始生成评估报告...")
            logger.info(f"会话 ID: {session_id}")
            logger.info(f"行业：{industry}")
            logger.info(f"角色：{role_type}")
            logger.info(f"考核维度数量：{len(dimensions)}")
            logger.info(f"对话转录长度：{len(transcript)}")
            logger.info("=" * 50)
            
            # 构建评估提示词
            dimensions_text = self._format_dimensions_text(dimensions)
            
            prompt = ASSESSMENT_REPORT_PROMPT.format(
                industry=industry,
                role_type=role_type,
                background_info=background_info,
                dimensions_text=dimensions_text,
                transcript=transcript
            )
            
            # 调用 LLM 生成评估报告
            logger.info("正在调用 Qwen Plus 3.5 生成评估报告...")
            response = self._call_model([
                SystemMessage(content="你是一位专业的培训评估专家，请根据提供的考核维度对培训对话进行客观、公正的评估。"),
                HumanMessage(content=prompt)
            ])
            
            # 解析 JSON 结果
            logger.info("正在解析评估结果...")
            result_json = self._extract_json(response)
            report_data = json.loads(result_json)
            
            # 验证报告格式
            if not self._validate_report(report_data):
                logger.error("评估报告格式验证失败")
                return None
            
            # 添加元数据
            report_data["session_id"] = session_id
            report_data["generated_at"] = self._get_current_timestamp()
            
            logger.info(f"评估报告生成成功，综合得分：{report_data.get('overall_score', 0)}")
            logger.info(f"维度得分数量：{len(report_data.get('dimension_scores', []))}")
            logger.info(f"亮点数量：{len(report_data.get('highlights', []))}")
            logger.info(f"改进建议数量：{len(report_data.get('improvements', []))}")
            
            return report_data
            
        except Exception as e:
            logger.error(f"生成评估报告失败：{str(e)}", exc_info=True)
            return None

    def _format_dimensions_text(self, dimensions: List[Dict[str, Any]]) -> str:
        """格式化考核维度文本"""
        if not dimensions:
            return "无考核维度"
        
        lines = []
        for dim in dimensions:
            dim_name = dim.get("dimension_name", "")
            weight = dim.get("weight", 0)
            sub_criteria = dim.get("sub_criteria", {})
            
            lines.append(f"## {dim_name} (权重：{weight*100:.0f}%)")
            lines.append("评估要点:")
            for criterion, desc in sub_criteria.items():
                lines.append(f"- {criterion}: {desc}")
            lines.append("")
        
        return "\n".join(lines)

    def _validate_report(self, report_data: Dict[str, Any]) -> bool:
        """验证评估报告格式"""
        required_fields = [
            "overall_score",
            "dimension_scores",
            "highlights",
            "improvements"
        ]
        
        for field in required_fields:
            if field not in report_data:
                logger.error(f"缺少必需字段：{field}")
                return False
        
        # 验证 dimension_scores 格式
        for dim_score in report_data.get("dimension_scores", []):
            if "dimension_name" not in dim_score or "score" not in dim_score:
                logger.error("维度得分格式错误")
                return False
        
        # 验证综合得分范围
        overall_score = report_data.get("overall_score", 0)
        if not (0 <= overall_score <= 100):
            logger.error(f"综合得分超出范围：{overall_score}")
            return False
        
        return True

    def _extract_json(self, text: str) -> str:
        """从文本中提取 JSON"""
        text = text.strip()
        
        # 移除 markdown 代码块标记
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
        
        # 找到第一个 { 的位置
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

    def _get_current_timestamp(self) -> str:
        """获取当前时间戳"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def save_to_database(
        self,
        session_id: str,
        report: Dict[str, Any],
        scene_id: int,
        user_id: int = 1,
        word_content: str = None,
        oss_file_path: str = None,
        call_duration: int = None
    ) -> bool:
        """
        保存评估报告到数据库
        
        Args:
            session_id: 会话 ID
            report: 评估报告字典
            scene_id: 场景 ID
            user_id: 用户 ID
            word_content: 对话内容 JSON
            oss_file_path: 音频文件路径
            call_duration: 通话时长
            
        Returns:
            保存是否成功
        """
        try:
            from database.record_dao import save_coach_record
            
            # 将评估报告转换为 JSON 字符串
            ai_evaluate = json.dumps(report, ensure_ascii=False)
            
            # 计算综合得分
            score = int(report.get("overall_score", 0))
            
            # 生成 AI 建议
            ai_advise = self._generate_ai_advise(report)
            
            # 保存到数据库
            success = save_coach_record(
                session_id=session_id,
                scene_id=scene_id,
                user_id=user_id,
                word_content=word_content,
                oss_file_path=oss_file_path,
                call_duration=call_duration,
                ai_evaluate=ai_evaluate,
                ai_advise=ai_advise,
                score=score
            )
            
            if success:
                logger.info(f"评估报告已保存到数据库：session_id={session_id}")
            else:
                logger.error(f"保存评估报告失败：session_id={session_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"保存评估报告到数据库失败：{str(e)}", exc_info=True)
            return False

    def _generate_ai_advise(self, report: Dict[str, Any]) -> str:
        """生成 AI 建议摘要"""
        improvements = report.get("improvements", [])
        highlights = report.get("highlights", [])
        summary = report.get("summary", "")
        
        advise_parts = []
        
        if highlights:
            advise_parts.append("【亮点】")
            advise_parts.append("、".join(highlights[:3]))
        
        if improvements:
            advise_parts.append("【改进建议】")
            advise_parts.append("、".join(improvements[:3]))
        
        if summary:
            advise_parts.append("【总结】")
            advise_parts.append(summary)
        
        return "\n".join(advise_parts) if advise_parts else "无"


# 全局服务实例
assessment_service = SceneAssessmentService()
