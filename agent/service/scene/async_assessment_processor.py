"""
异步评估任务处理器

支持后台异步执行评估任务，避免阻塞WebSocket连接
"""
import threading
import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class AsyncAssessmentProcessor:
    """
    异步评估任务处理器
    
    在后台线程中执行评估任务，包括：
    1. 能力维度评估和打分
    2. SOP质检项评估和打分
    3. AI总结建议
    4. 总分计算
    """
    
    def __init__(self, assessment_service):
        """
        初始化异步评估处理器
        
        Args:
            assessment_service: SceneAssessmentService 实例
        """
        self.assessment_service = assessment_service
        self.active_tasks = {}
        
    def submit_assessment_task(
        self,
        session_id: str,
        word_content: str,
        dimensions: list,
        industry: str,
        role_type: str,
        role_description: str,
        scene_id: int,
        user_id: int,
        oss_file_path: str = None,
        call_duration: int = 0
    ) -> str:
        """
        提交评估任务到后台执行
        
        Args:
            session_id: 会话 ID
            word_content: 对话内容
            dimensions: 能力维度配置
            industry: 行业
            role_type: 角色类型
            role_description: 角色描述
            scene_id: 场景 ID
            user_id: 用户 ID
            oss_file_path: 音频文件路径
            call_duration: 通话时长
            
        Returns:
            任务 ID
        """
        task_id = f"{session_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        task_data = {
            'task_id': task_id,
            'session_id': session_id,
            'word_content': word_content,
            'dimensions': dimensions,
            'industry': industry,
            'role_type': role_type,
            'role_description': role_description,
            'scene_id': scene_id,
            'user_id': user_id,
            'oss_file_path': oss_file_path,
            'call_duration': call_duration,
            'status': 'pending',
            'created_at': datetime.now()
        }
        
        self.active_tasks[task_id] = task_data
        
        thread = threading.Thread(
            target=self._execute_assessment,
            args=(task_data,),
            name=f"Assessment-{task_id}"
        )
        thread.daemon = True
        thread.start()
        
        logger.info(f"评估任务已提交: task_id={task_id}, session_id={session_id}")
        
        return task_id
    
    def _execute_assessment(self, task_data: Dict[str, Any]):
        """
        执行评估任务（在后台线程中）
        
        Args:
            task_data: 任务数据
        """
        task_id = task_data['task_id']
        session_id = task_data['session_id']
        
        try:
            self.active_tasks[task_id]['status'] = 'processing'
            self.active_tasks[task_id]['started_at'] = datetime.now()
            
            logger.info(f"开始执行评估任务: task_id={task_id}")
            
            # 步骤1: 能力维度评估和打分
            logger.info(f"[{task_id}] 步骤1/4: 开始能力维度评估...")
            dimension_report = self.assessment_service.generate_report(
                session_id=session_id,
                word_content=task_data['word_content'],
                dimensions=task_data['dimensions'],
                industry=task_data['industry'],
                role_type=task_data['role_type'],
                role_description=task_data['role_description']
            )
            
            if not dimension_report:
                raise Exception("能力维度评估失败")
            
            logger.info(f"[{task_id}] 步骤1/4: 能力维度评估完成, 综合得分={dimension_report.get('overall_score', 0)}")
            
            # 步骤2: SOP质检项评估和打分
            logger.info(f"[{task_id}] 步骤2/4: 开始SOP质检评估...")
            sop_result = None
            try:
                from database.sop_dao import sop_dao
                sop_checklist = sop_dao.get_scene_sop_checklist(task_data['scene_id'])
                
                if sop_checklist:
                    sop_result = self.assessment_service.evaluate_sop(
                        word_content=task_data['word_content'],
                        sop_checklist=sop_checklist
                    )
                    logger.info(f"[{task_id}] 步骤2/4: SOP质检评估完成, 得分={sop_result.get('sop_score', 0)}")
                else:
                    logger.info(f"[{task_id}] 步骤2/4: 场景未配置SOP质检项，跳过")
            except Exception as sop_e:
                logger.warning(f"[{task_id}] SOP质检评估失败: {sop_e}")
                sop_result = None
            
            # 步骤3: AI总结建议
            logger.info(f"[{task_id}] 步骤3/4: 生成AI总结建议...")
            ai_advise = self.assessment_service._generate_ai_advise(dimension_report)
            dimension_report['ai_advise'] = ai_advise
            logger.info(f"[{task_id}] 步骤3/4: AI总结建议生成完成")
            
            # 步骤4: 总分计算
            logger.info(f"[{task_id}] 步骤4/4: 计算总分...")
            final_score = self._calculate_final_score(
                dimension_report=dimension_report,
                sop_result=sop_result
            )
            logger.info(f"[{task_id}] 步骤4/4: 总分计算完成, 最终得分={final_score}")
            
            # 保存到数据库
            logger.info(f"[{task_id}] 保存评估结果到数据库...")
            success = self.assessment_service.save_to_database(
                session_id=session_id,
                report=dimension_report,
                scene_id=task_data['scene_id'],
                user_id=task_data['user_id'],
                word_content=task_data['word_content'],
                oss_file_path=task_data['oss_file_path'],
                call_duration=task_data['call_duration'],
                sop_result=sop_result
            )
            
            if success:
                logger.info(f"[{task_id}] 评估任务完成并保存成功")
                self.active_tasks[task_id]['status'] = 'completed'
                self.active_tasks[task_id]['completed_at'] = datetime.now()
                self.active_tasks[task_id]['result'] = {
                    'dimension_report': dimension_report,
                    'sop_result': sop_result,
                    'ai_advise': ai_advise,
                    'final_score': final_score
                }
            else:
                raise Exception("保存评估结果到数据库失败")
            
        except Exception as e:
            logger.error(f"[{task_id}] 评估任务执行失败: {str(e)}", exc_info=True)
            self.active_tasks[task_id]['status'] = 'failed'
            self.active_tasks[task_id]['error'] = str(e)
            self.active_tasks[task_id]['failed_at'] = datetime.now()
    
    def _calculate_final_score(
        self,
        dimension_report: Dict[str, Any],
        sop_result: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        计算最终得分
        
        计算规则：
        - 能力维度得分权重：70%
        - SOP质检得分权重：30%
        - 如果没有SOP质检，则只使用能力维度得分
        
        Args:
            dimension_report: 能力维度评估报告
            sop_result: SOP质检结果
            
        Returns:
            最终得分（0-100）
        """
        dimension_score = dimension_report.get('overall_score', 0)
        
        if sop_result is None:
            logger.info("未配置SOP质检，最终得分 = 能力维度得分")
            return int(dimension_score)
        
        sop_score = sop_result.get('sop_score', 0)
        
        final_score = int(dimension_score * 0.7 + sop_score * 0.3)
        
        logger.info(f"总分计算: 能力维度得分={dimension_score}, SOP得分={sop_score}, 最终得分={final_score} (权重: 70%/30%)")
        
        return final_score
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        获取任务状态
        
        Args:
            task_id: 任务 ID
            
        Returns:
            任务状态信息，如果任务不存在则返回 None
        """
        return self.active_tasks.get(task_id)
    
    def cleanup_old_tasks(self, max_age_hours: int = 24):
        """
        清理旧任务记录
        
        Args:
            max_age_hours: 任务最大保留时间（小时）
        """
        from datetime import timedelta
        
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        
        to_remove = []
        for task_id, task_data in self.active_tasks.items():
            created_at = task_data.get('created_at')
            if created_at and created_at < cutoff_time:
                to_remove.append(task_id)
        
        for task_id in to_remove:
            del self.active_tasks[task_id]
        
        if to_remove:
            logger.info(f"清理了 {len(to_remove)} 个旧任务记录")


# 全局异步评估处理器实例
_async_processor = None


def get_async_processor(assessment_service) -> AsyncAssessmentProcessor:
    """
    获取全局异步评估处理器实例
    
    Args:
        assessment_service: SceneAssessmentService 实例
        
    Returns:
        AsyncAssessmentProcessor 实例
    """
    global _async_processor
    if _async_processor is None:
        _async_processor = AsyncAssessmentProcessor(assessment_service)
    return _async_processor
