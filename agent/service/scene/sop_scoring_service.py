"""
SOP质检项智能评分服务
"""
import os
import json
import logging
from typing import List, Dict, Any

from langchain_core.messages import HumanMessage, SystemMessage

logger = logging.getLogger(__name__)


class SOPScoringService:
    """SOP质检项智能评分服务"""
    
    # 重要性等级与基础分值映射
    IMPORTANCE_SCORES = {
        "critical": 30,   # 关键项：法律合规、客户体验核心
        "high": 20,       # 重要项：业务流程关键环节
        "medium": 10,     # 一般项：流程完整性
        "low": 5          # 加分项：体验优化
    }
    
    # 质检类型系数
    TYPE_WEIGHTS = {
        "must_do": 1.0,      # 必须做
        "must_not_do": 1.2,  # 禁止项（违规后果严重，系数更高）
        "should_do": 0.8     # 建议项（加分项，系数较低）
    }
    
    # 场景环节权重（可配置）
    CATEGORY_WEIGHTS = {
        "greeting": 1.0,           # 开场问候
        "needs_analysis": 1.2,     # 需求分析（核心环节）
        "product_intro": 1.0,      # 产品介绍
        "objection_handling": 1.1, # 异议处理
        "closing": 1.1,            # 促成结束
        "compliance": 1.5,         # 合规要求（最高权重）
        "general": 0.8             # 一般要求
    }
    
    def __init__(self):
        import dashscope
        from dashscope import MultiModalConversation
        
        dashscope.api_key = os.getenv("DASHSCOPE_API_KEY")
        self.llm_model = os.getenv("QWEN_PLUS_MODEL", "qwen-plus")
        self.generation = MultiModalConversation
        
        logger.info(f"SOP评分服务初始化完成，使用模型：{self.llm_model}")
    
    def calculate_item_score(self, item: Dict) -> Dict:
        """
        计算单个质检项的分数
        
        返回带评分的质检项
        """
        # 1. 确定重要性等级
        importance = item.get('importance_level', 'medium')
        base_score = self.IMPORTANCE_SCORES.get(importance, 10)
        
        # 2. 应用类型系数
        check_type = item.get('check_type', 'should_do')
        type_weight = self.TYPE_WEIGHTS.get(check_type, 1.0)
        
        # 3. 应用分类权重
        category = item.get('category', 'general')
        category_weight = self.CATEGORY_WEIGHTS.get(category, 1.0)
        
        # 4. 计算最终分数
        final_score = round(base_score * type_weight * category_weight)
        
        # 5. 更新质检项
        item['base_score'] = base_score
        item['weight'] = round(type_weight * category_weight, 2)
        item['final_score'] = final_score
        item['score_reason'] = self._generate_score_reason(
            importance, check_type, category, final_score
        )
        
        return item
    
    def balance_scores(
        self, 
        checklist: List[Dict],
        target_total: int = 100
    ) -> List[Dict]:
        """
        平衡质检项分数，使总分达到目标值
        
        Args:
            checklist: 质检项列表
            target_total: 目标总分（默认100分）
            
        Returns:
            调整后的质检项列表
        """
        if not checklist:
            return checklist
        
        # 1. 计算当前总分
        current_total = sum(item.get('final_score', 0) for item in checklist)
        
        if current_total == 0:
            logger.error("质检项总分为0，无法平衡")
            return checklist
        
        # 2. 计算调整系数
        adjustment_factor = target_total / current_total
        
        # 3. 按比例调整每个质检项的分数
        for item in checklist:
            old_score = item.get('final_score', 0)
            new_score = round(old_score * adjustment_factor)
            
            # 确保分数不为0
            if old_score > 0 and new_score == 0:
                new_score = 1
            
            item['final_score'] = new_score
            item['adjusted'] = True
            item['adjustment_factor'] = round(adjustment_factor, 2)
        
        # 4. 微调确保总分精确为target_total
        actual_total = sum(item.get('final_score', 0) for item in checklist)
        diff = target_total - actual_total
        
        if diff != 0:
            # 将差值分配到分数最高的几项
            sorted_items = sorted(
                checklist, 
                key=lambda x: x.get('final_score', 0), 
                reverse=True
            )
            
            for i in range(min(abs(diff), len(sorted_items))):
                sorted_items[i]['final_score'] += (1 if diff > 0 else -1)
        
        logger.info(f"分数平衡完成：{current_total} → {target_total}")
        
        return checklist
    
    def adjust_item_score(
        self,
        item: Dict,
        new_score: int = None,
        new_importance: str = None
    ) -> Dict:
        """
        调整单个质检项的分数
        
        Args:
            item: 质检项
            new_score: 新的分数（直接指定）
            new_importance: 新的重要性等级（重新计算）
            
        Returns:
            更新后的质检项
        """
        if new_importance:
            # 根据新的重要性等级重新计算
            item['importance_level'] = new_importance
            return self.calculate_item_score(item)
        elif new_score is not None:
            # 直接设置分数
            item['final_score'] = new_score
            item['manual_adjusted'] = True
            return item
        
        return item
    
    def get_scoring_summary(self, checklist: List[Dict]) -> Dict[str, Any]:
        """
        获取评分摘要
        
        Args:
            checklist: 质检项列表
            
        Returns:
            评分摘要
        """
        summary = {
            "total_score": 0,
            "must_do_score": 0,
            "must_not_score": 0,
            "should_do_score": 0,
            "critical_count": 0,
            "high_count": 0,
            "medium_count": 0,
            "low_count": 0,
            "total_items": len(checklist)
        }
        
        for item in checklist:
            score = item.get('final_score', 0)
            check_type = item.get('check_type', 'should_do')
            importance = item.get('importance_level', 'medium')
            
            summary['total_score'] += score
            
            if check_type == 'must_do':
                summary['must_do_score'] += score
            elif check_type == 'must_not_do':
                summary['must_not_score'] += score
            else:
                summary['should_do_score'] += score
            
            if importance == 'critical':
                summary['critical_count'] += 1
            elif importance == 'high':
                summary['high_count'] += 1
            elif importance == 'medium':
                summary['medium_count'] += 1
            else:
                summary['low_count'] += 1
        
        return summary
    
    def _generate_score_reason(
        self,
        importance: str,
        check_type: str,
        category: str,
        final_score: int
    ) -> str:
        """生成评分说明"""
        importance_desc = {
            "critical": "关键项",
            "high": "重要项",
            "medium": "一般项",
            "low": "加分项"
        }
        
        type_desc = {
            "must_do": "必须执行",
            "must_not_do": "严格禁止",
            "should_do": "建议执行"
        }
        
        category_desc = {
            "greeting": "开场环节",
            "needs_analysis": "需求分析（核心）",
            "product_intro": "产品介绍",
            "objection_handling": "异议处理",
            "closing": "促成结束",
            "compliance": "合规要求（高权重）",
            "general": "一般要求"
        }
        
        return f"{importance_desc.get(importance, '')}，{type_desc.get(check_type, '')}，{category_desc.get(category, '')}，分值{final_score}分"
    
    def get_scoring_rules(self) -> Dict[str, Any]:
        """
        获取评分规则配置
        
        Returns:
            评分规则字典
        """
        return {
            "importance_scores": self.IMPORTANCE_SCORES,
            "type_weights": self.TYPE_WEIGHTS,
            "category_weights": self.CATEGORY_WEIGHTS,
            "customizable": True,
            "formula": "最终分数 = 基础分 × 类型系数 × 分类权重"
        }


# 全局服务实例
sop_scoring_service = SOPScoringService()