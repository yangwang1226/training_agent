"""
SOP质检项数据访问层
负责 SOP 质检项的数据库操作
"""

from typing import List, Dict, Optional
import json
from database.connection import get_connection
import logging

logger = logging.getLogger(__name__)


class SOPChecklistDAO:
    """SOP质检项数据访问对象"""

    @staticmethod
    def get_scene_sop_checklist(scene_code: str) -> Optional[List[Dict]]:
        """
        获取指定场景的默认 SOP 质检项
        
        Args:
            scene_code: 场景代码
            
        Returns:
            质检项列表，如果没有则返回 None
        """
        try:
            conn = get_connection()
            with conn.cursor() as cursor:
                sql = """
                    SELECT default_sop_checklist 
                    FROM ai_coach_preset_scene 
                    WHERE scene_code = %s AND is_active = 1
                """
                cursor.execute(sql, (scene_code,))
                result = cursor.fetchone()
                
                if result and result.get('default_sop_checklist'):
                    # 如果是字符串，需要解析为 JSON
                    checklist = result['default_sop_checklist']
                    if isinstance(checklist, str):
                        checklist = json.loads(checklist)
                    return checklist
                return None
        except Exception as e:
            logger.error(f"获取场景 SOP 质检项失败: {e}")
            return None
        finally:
            if conn:
                conn.close()

    @staticmethod
    def update_scene_sop_checklist(scene_code: str, checklist: List[Dict]) -> bool:
        """
        更新指定场景的 SOP 质检项
        
        Args:
            scene_code: 场景代码
            checklist: 质检项列表
            
        Returns:
            是否更新成功
        """
        try:
            conn = get_connection()
            with conn.cursor() as cursor:
                # 将列表转换为 JSON 字符串
                checklist_json = json.dumps(checklist, ensure_ascii=False)
                
                sql = """
                    UPDATE ai_coach_preset_scene 
                    SET default_sop_checklist = %s,
                        updated_time = NOW()
                    WHERE scene_code = %s AND is_active = 1
                """
                cursor.execute(sql, (checklist_json, scene_code))
                conn.commit()
                
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"更新场景 SOP 质检项失败: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()

    @staticmethod
    def get_all_scenes_with_sop() -> List[Dict]:
        """
        获取所有配置了 SOP 质检项的场景
        
        Returns:
            场景列表
        """
        try:
            conn = get_connection()
            with conn.cursor() as cursor:
                sql = """
                    SELECT 
                        scene_code,
                        scene_name,
                        industry_code,
                        default_sop_checklist,
                        created_time,
                        updated_time
                    FROM ai_coach_preset_scene 
                    WHERE is_active = 1 AND default_sop_checklist IS NOT NULL
                    ORDER BY industry_code, display_order
                """
                cursor.execute(sql)
                results = cursor.fetchall()
                
                # 解析 JSON 字段
                for result in results:
                    if result.get('default_sop_checklist'):
                        checklist = result['default_sop_checklist']
                        if isinstance(checklist, str):
                            result['default_sop_checklist'] = json.loads(checklist)
                        # 添加质检项数量
                        result['checklist_count'] = len(result['default_sop_checklist'])
                
                return results
        except Exception as e:
            logger.error(f"获取 SOP 场景列表失败: {e}")
            return []
        finally:
            if conn:
                conn.close()

    @staticmethod
    def validate_checklist_structure(checklist: List[Dict]) -> tuple[bool, str]:
        """
        验证质检项列表的结构是否正确
        
        Args:
            checklist: 质检项列表
            
        Returns:
            (是否有效, 错误信息)
        """
        if not isinstance(checklist, list):
            return False, "质检项必须是列表格式"
        
        required_fields = ['item_id', 'item_name', 'check_type']
        valid_check_types = ['must_do', 'must_not']
        
        for idx, item in enumerate(checklist):
            if not isinstance(item, dict):
                return False, f"质检项 {idx + 1} 必须是对象格式"
            
            # 检查必填字段
            for field in required_fields:
                if field not in item:
                    return False, f"质检项 {idx + 1} 缺少必填字段: {field}"
            
            # 检查 check_type 值
            if item['check_type'] not in valid_check_types:
                return False, f"质检项 {idx + 1} 的 check_type 必须是 must_do 或 must_not"
            
            # 检查 keywords 字段（可选，但如果存在必须是列表）
            if 'keywords' in item and not isinstance(item['keywords'], list):
                return False, f"质检项 {idx + 1} 的 keywords 必须是列表格式"
        
        return True, ""


# 单例实例
sop_dao = SOPChecklistDAO()