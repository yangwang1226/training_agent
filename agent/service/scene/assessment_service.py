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

    def _generate_transcript(self, word_content: str) -> str:
        """处理对话转录文本
        
        注意：word_content 已经是格式化的转录文本，直接返回即可
        格式示例：
        [2026-03-19 16:03:00] 用户: 你好
        [2026-03-19 16:03:05] AI: 您好，欢迎...
        """
        return word_content

    def generate_report(
        self,
        session_id: str,
        word_content: str,
        dimensions: List[Dict[str, Any]],
        industry: str = "",
        role_type: str = "",
        role_description: str = ""
    ) -> Optional[Dict[str, Any]]:
        """
        生成评估报告
        
        Args:
            session_id: 训练会话 ID
            word_content: 对话内容文字
            dimensions: 考核维度列表
            industry: 行业
            role_type: 角色类型
            role_description: 角色描述
            
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
            logger.info(f"对话内容长度：{len(word_content)}")
            logger.info("=" * 50)
            
            # 构建评估提示词
            dimensions_text = self._format_dimensions_text(dimensions)
            
            # 转录一下对话内容，确保符合评估要求
            transcript = self._generate_transcript(word_content)
            # 构建评估提示词
            prompt = ASSESSMENT_REPORT_PROMPT.format(
                industry=industry,
                role_type=role_type,
                role_description=role_description,
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
    
    def evaluate_sop(
        self,
        word_content: str,
        sop_checklist: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """SOP质检评估
        
        Args:
            word_content: 对话文本
            sop_checklist: SOP质检项列表
            
        Returns:
            SOP评估结果字典
        """
        if not sop_checklist:
            logger.warning("SOP质检项为空，跳过SOP评估")
            return {
                "score": 0,
                "total_items": 0,
                "passed_count": 0,
                "failed_count": 0,
                "details": [],
                "summary": "未配置SOP质检项"
            }
        
        # 生成对话转录
        transcript = self._generate_transcript(word_content)

        try:
            # 构建质检项描述
            items_text = "\n".join([
                f"[{idx+1}] {item['item_name']} (类型: {item['check_type']})\n   描述: {item.get('item_desc', '无')}\n   关键词: {item.get('keywords', '无')}"
                for idx, item in enumerate(sop_checklist)
            ])
            
            prompt = f"""你是专业的销售质检专家。请严格按照以下SOP标准，逐项检查销售人员的对话表现。
            
            ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            【🎯 关键角色说明 - 请务必仔细阅读】
            ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            
            这是一个销售培训场景，对话中有两个角色：
            
            1. 【销售人员】= 转录中标注为 "用户" 的发言
               → 这是被评估的对象！
               → 你需要检查TA是否按照SOP执行
            
            2. 【模拟客户】= 转录中标注为 "AI" 的发言
               → 这是训练用的AI角色
               → 不需要评估TA的表现
            
            ⚠️⚠️⚠️ 特别提醒：
            - 只评估 "用户"（销售人员）的表现
            - 不要评估 "AI"（模拟客户）的表现
            - 如果SOP要求"主动问候"，要看"用户"是否说了问候语
            ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

            【SOP质检项】
            {items_text}

            【对话转录】
            {transcript}

            【质检要求】
            1. 评估对象：销售人员（对话中标注为"用户"的发言）
            2. 对每个质检项，判断销售人员是否执行（passed: true/false）
            3. must_do（必须项）：销售人员必须执行
            4. must_not_do（禁止项）：销售人员不能做
            5. should_do（建议项）：销售人员建议执行
            6. evidence（依据）：说明销售人员在对话中的表现
            7. suggestion（建议）：针对销售人员的改进建议

            请按照以下JSON格式返回评估结果：
            {{
                "check_results": [
                    {{
                        "item_name": "质检项名称",
                        "check_type": "must_do/must_not_do/should_do",
                        "passed": true/false,
                        "evidence": "对话中的依据或说明",
                        "suggestion": "改进建议（未通过时）"
                    }}
                ],
                "summary": "总体评价"
            }}
            """
            
            logger.info("开始SOP质检评估...")
            
            response = self._call_model([
                SystemMessage(content="你是专业的销售质检专家，严格按照SOP标准逐项检查。返回严格的JSON格式。"),
                HumanMessage(content=prompt)
            ])
            
            # 解析响应
            result_json = self._extract_json(response)
            result = json.loads(result_json)
            
            # 计算得分和分数
            details = result.get('check_results', [])
            total = len(details)
            passed = sum(1 for d in details if d.get('passed', False))
            failed = total - passed
            
            # 计算 SOP 分数（基于分数规则）
            total_score = 0
            actual_score = 0
            
            for detail in details:
                check_type = detail.get('check_type', 'should_do')
                is_passed = detail.get('passed', False)
                
                # 根据类型分配默认分数
                if check_type == 'must_do':
                    default_score = 30
                elif check_type == 'must_not_do':
                    default_score = 30
                else:  # should_do
                    default_score = 15
                
                detail['default_score'] = default_score
                
                # 计算实际得分
                if check_type == 'must_not_do':
                    # 禁止项：违反扣分，未违反得分
                    detail['actual_score'] = 0 if is_passed else default_score  # passed=True 表示违反了
                    actual_score += detail['actual_score']
                else:
                    # 必须项和建议项：通过得分，未通过不得分
                    detail['actual_score'] = default_score if is_passed else 0
                    actual_score += detail['actual_score']
                    total_score += default_score
            
            # 计算百分制分数
            sop_score = round((actual_score / total_score) * 100) if total_score > 0 else 0
            
            logger.info(f"SOP质检完成: 总数={total}, 通过={passed}, 未通过={failed}, 得分={sop_score}")
            
            return {
                "sop_score": sop_score,  # 百分制总分
                "total_score": total_score,  # 总可得分数
                "actual_score": actual_score,  # 实际得分
                "total_items": total,
                "passed_count": passed,
                "failed_count": failed,
                "pass_rate": round(passed / total, 2) if total > 0 else 0,
                "details": details,
                "summary": result.get('summary', '')
            }
            
        except Exception as e:
            logger.error(f"SOP质检评估失败: {e}", exc_info=True)
            return {
                "score": 0,
                "total_items": len(sop_checklist),
                "passed_count": 0,
                "failed_count": len(sop_checklist),
                "details": [],
                "summary": f"SOP质检评估失败: {str(e)}",
                                "error": str(e)
            }

    def save_to_database(
        self,
        session_id: str,
        report: Dict[str, Any],
        scene_id: int,
        user_id: int = 1,
        word_content: str = None,
        oss_file_path: str = None,
        call_duration: int = None,
        sop_result: Dict[str, Any] = None
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
            sop_result: SOP质检结果
            
        Returns:
            保存是否成功
        """
        try:
            from database.record_dao import save_coach_record
            
            # 提取 AI 综合评分
            ai_score = int(report.get("overall_score", 0))
            
            # 提取 AI 评估总结
            ai_summary = report.get("summary", "")
            
                        # 保存完整的评估结果，包括维度评分、亮点、改进建议等
            dimension_result_data = {
                "dimension_scores": report.get("dimension_scores", []),
                "highlights": report.get("highlights", []),
                "improvements": report.get("improvements", []),
                "key_moments": report.get("key_moments", []),
                "golden_sentences": report.get("golden_sentences", [])
            }
            dimension_result_text = json.dumps(dimension_result_data, ensure_ascii=False)
            
            # 生成 AI 建议
            ai_advise = report.get("ai_advise", self._generate_ai_advise(report))
            
            # 处理SOP结果
            sop_result_text = None
            sop_score = None
            if sop_result:
                sop_result_text = json.dumps(sop_result, ensure_ascii=False)
                sop_score = sop_result.get('sop_score', 0)  # 提取 SOP 分数
                logger.info(f"SOP评估结果: 得分={sop_score}, 通过={sop_result.get('passed_count', 0)}/{sop_result.get('total_items', 0)}")
            
            # 保存到数据库（使用新的字段结构）
            success = save_coach_record(
                session_id=session_id,
                scene_id=scene_id,
                user_id=user_id,
                word_content=word_content,
                oss_file_path=oss_file_path,
                call_duration=call_duration,
                ai_score=ai_score,
                ai_summary=ai_summary,
                dimension_result=dimension_result_text,
                ai_advise=ai_advise,
                sop_result=sop_result_text,
                sop_score=sop_score
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

