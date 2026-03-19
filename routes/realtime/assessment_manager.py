"""
评估任务管理器

管理评估任务的提交和处理，包括：
- 维度配置解析
- 评估任务提交
- 评估结果通知
"""

import json
import logging
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


class AssessmentTaskManager:
    """管理评估任务的提交"""
    
    def __init__(self, async_processor):
        """
        初始化评估任务管理器
        
        Args:
            async_processor: 异步评估处理器实例
        """
        self.async_processor = async_processor
    
    def submit_assessment(
        self,
        session_manager,
        save_result: Optional[Dict] = None
    ) -> Optional[str]:
        """
        提交评估任务
        
        Args:
            session_manager: RealtimeSessionManager 实例
            save_result: 对话保存结果，包含 audio_file, call_duration 等
            
        Returns:
            task_id，失败返回 None
        """
        try:
            logger.info("提交异步评估任务...")
            
            # 解析维度配置
            dimensions = self._parse_dimensions(
                session_manager.scene.get('dimension_config')
            )
            
            # 获取对话转录
            word_content = session_manager.get_transcript_text()
            
            if not word_content :
                logger.warning("对话转录为空，跳过评估")
                return None
            
            # 准备评估参数
            assessment_params = self._prepare_assessment_params(
                session_manager=session_manager,
                dimensions=dimensions,
                word_content=word_content,
                save_result=save_result
            )
            
            # 提交任务
            task_id = self.async_processor.submit_assessment_task(**assessment_params)
            
            logger.info(f"异步评估任务已提交: task_id={task_id}")
            return task_id
            
        except Exception as e:
            logger.error(f"提交异步评估任务失败：{str(e)}", exc_info=True)
            return None
    
    def _prepare_assessment_params(
        self,
        session_manager,
        dimensions: List[Dict],
        word_content: str,
        save_result: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        准备评估任务参数
        
        Args:
            session_manager: 会话管理器
            dimensions: 评估维度列表
            word_content: 对话转录
            save_result: 保存结果
            
        Returns:
            评估任务参数字典
        """
        scene = session_manager.scene
        
        params = {
            'session_id': session_manager.get_session_id(),
            'word_content': word_content,
            'dimensions': dimensions,
            'industry': scene.get('industry', ''),
            'role_type': scene.get('ai_role', ''),
            'role_description': scene.get('role_description', ''),
            'scene_id': session_manager.scene_id,
            'user_id': session_manager.get_user_id(),
        }
        
        # 添加保存结果信息
        if save_result:
            params['oss_file_path'] = save_result.get('audio_file', '')
            params['call_duration'] = save_result.get('call_duration', 0)
        else:
            params['oss_file_path'] = ''
            params['call_duration'] = session_manager.get_call_duration()
        
        return params
    
    def _parse_dimensions(self, dimension_config: Optional[str]) -> List[Dict]:
        """
        解析维度配置
        
        Args:
            dimension_config: JSON 格式的维度配置字符串
            
        Returns:
            维度列表
        """
        if not dimension_config:
            logger.info("维度配置为空，使用默认维度")
            return []
        
        try:
            config_data = json.loads(dimension_config)
            dimensions = config_data.get('dimensions', [])
            logger.info(f"解析到 {len(dimensions)} 个评估维度")
            return dimensions
        except json.JSONDecodeError as e:
            logger.warning(f"维度配置 JSON 解析失败: {e}")
            return []
        except Exception as e:
            logger.warning(f"解析维度配置失败: {e}")
            return []
    
    def notify_assessment_submitted(self, ws, session_id: str, task_id: str):
        """
        通知前端评估任务已提交
        
        Args:
            ws: WebSocket 连接
            session_id: 会话 ID
            task_id: 任务 ID
        """
        try:
            ws.send(json.dumps({
                'type': 'assessment_submitted',
                'session_id': session_id,
                'task_id': task_id,
                'message': '评估任务已提交，正在后台处理中...'
            }))
            logger.info(f"Assessment submission notification sent: task_id={task_id}")
        except Exception as e:
            logger.error(f"Failed to notify assessment submission: {e}")
    
    def notify_assessment_error(self, ws, error: str):
        """
        通知前端评估任务错误
        
        Args:
            ws: WebSocket 连接
            error: 错误信息
        """
        try:
            ws.send(json.dumps({
                'type': 'assessment_error',
                'error': error
            }))
        except Exception as e:
            logger.error(f"Failed to notify assessment error: {e}")
    
    def notify_ready_to_close(self, ws):
        """
        通知前端可以关闭连接
        
        Args:
            ws: WebSocket 连接
        """
        try:
            ws.send(json.dumps({
                'type': 'ready_to_close'
            }))
            logger.info("Ready to close notification sent")
        except Exception as e:
            logger.error(f"Failed to notify ready to close: {e}")