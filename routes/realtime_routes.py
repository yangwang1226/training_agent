import os
import sys
import json
import logging
import base64
from pathlib import Path

from flask import Blueprint, render_template, jsonify, request

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import db as db_module
from agent.service.conversational import ConversationRecorder
from agent.service.scene.assessment_service import assessment_service as scene_assessment_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

_realtime_dir = Path(__file__).parent

# 模板和静态文件实际在 front_end/realtime 目录下
# 从 routes/ 目录向上两级到项目根目录，然后到 front_end/realtime
project_root = _realtime_dir.parent
_realtime_template_dir = project_root / 'front_end' / 'realtime' / 'templates'
_realtime_static_dir = project_root / 'front_end' / 'realtime' / 'static'

realtime_bp = Blueprint('realtime', __name__, 
                        url_prefix='/realtime',
                        template_folder=str(_realtime_template_dir),
                        static_folder=str(_realtime_static_dir),
                        static_url_path='/realtime/static')

DEFAULT_PROVIDER = os.getenv("REALTIME_PROVIDER", "qwen").lower()


@realtime_bp.route('/<scene_id>')
def index(scene_id):
    try:
        scene_id_int = int(scene_id)
        scene = db_module.get_scene_by_id(scene_id_int)
        if not scene:
            return "场景不存在", 404
        
        scene_name = scene.get('scene_name', '未知场景')
        provider = request.args.get('provider', DEFAULT_PROVIDER)
        
        return render_template('realtime.html', 
                              scene_id=scene_id, 
                              scene_name=scene_name,
                              provider=provider)
    except ValueError:
        return "无效的场景 ID", 400
    except Exception as e:
        logger.error(f"获取场景失败：{e}")
        return "获取场景失败", 500


@realtime_bp.route('/prompt/<scene_id>')
def get_prompt(scene_id):
    try:
        scene_id_int = int(scene_id)
        prompt = db_module.get_prompt_by_scene_id(scene_id_int)
        if prompt:
            return jsonify({'success': True, 'prompt': prompt})
        else:
            return jsonify({'success': False, 'error': '场景不存在'})
    except ValueError:
        return jsonify({'success': False, 'error': '无效的场景 ID'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


def register_websocket(sock):
    """注册 WebSocket 路由"""
    logger.info("Registering WebSocket routes")
    
    @sock.route('/api/realtime/ws/<scene_id>')
    def realtime_ws(ws, scene_id):
        provider = request.args.get('provider', DEFAULT_PROVIDER).lower()
        logger.info(f"WebSocket connection for scene: {scene_id}, provider: {provider}")
        
        try:
            scene_id_int = int(scene_id)
            scene = db_module.get_scene_by_id(scene_id_int)
            if not scene:
                ws.send(json.dumps({'type': 'error', 'message': '场景不存在'}))
                ws.close()
                return
            
            scene_name = scene.get('scene_name', '未知场景')
            system_prompt = scene.get('scene_prompt', '')
        except ValueError:
            ws.send(json.dumps({'type': 'error', 'message': '无效的场景 ID'}))
            ws.close()
            return
        except Exception as e:
            ws.send(json.dumps({'type': 'error', 'message': f'获取场景失败：{str(e)}'}))
            ws.close()
            return
        
        recorder = ConversationRecorder(scene_id, scene_name, provider)
        recorder.set_system_prompt(system_prompt)
        
        from llm import create_realtime_client, RealtimeConfig, ProviderType
        
        config = RealtimeConfig.from_provider(ProviderType(provider))
        client = create_realtime_client(provider, config)
        
        def on_text(text, role, is_final):
            try:
                if is_final and text:
                    recorder.add_message(role, text)
                
                ws.send(json.dumps({
                    'type': 'text',
                    'role': role,
                    'text': text,
                    'is_final': is_final
                }))
            except Exception as e:
                logger.error(f"Send text error: {e}")
        
        def on_audio(audio_b64):
            try:
                logger.info(f"Received audio data, length: {len(audio_b64)}")
                recorder.add_audio_chunk(audio_b64)
                ws.send(json.dumps({
                    'type': 'audio',
                    'audio': audio_b64
                }))
            except Exception as e:
                logger.error(f"Send audio error: {e}")
        
        def on_status(status, message):
            try:
                ws.send(json.dumps({
                    'type': 'status',
                    'status': status,
                    'message': message
                }))
            except Exception as e:
                logger.error(f"Send status error: {e}")
        
        client.on_text(on_text)
        client.on_audio(on_audio)
        client.on_status(on_status)
        
        try:
            ws.send(json.dumps({
                'type': 'status',
                'status': 'connecting',
                'message': f'正在连接服务器 (服务商：{provider})...'
            }))
            
            client.connect(instructions=system_prompt)
            
            ws.send(json.dumps({
                'type': 'status',
                'status': 'connected',
                'message': f'已连接到服务器 (服务商：{provider})'
            }))
            
            while True:
                try:
                    data = ws.receive(timeout=60)
                    if data is None:
                        break
                    
                    try:
                        if isinstance(data, bytes):
                            client.send_audio(data)
                        else:
                            message = json.loads(data)
                            msg_type = message.get('type', 'unknown')
                            
                            if msg_type == 'audio':
                                audio_b64 = message.get('audio', '')
                                if audio_b64:
                                    audio_data = base64.b64decode(audio_b64)
                                    client.send_audio(audio_data)
                            
                            elif msg_type == 'text':
                                text = message.get('text', '')
                                if text:
                                    client.send_text(text)
                            
                                elif msg_type == 'session_end':
                                    # ✅ 处理会话结束信号
                                    logger.info("收到前端会话结束信号，开始保存和评估...")
                                
                                                                try:
                                    # 1. 保存对话记录和音频
                                    save_result = recorder.save()
                                    if save_result:
                                        logger.info(f"对话记录已保存: session_id={save_result['session_id']}, audio={save_result.get('audio_file')}")
                                        ws.send(json.dumps({
                                            'type': 'save_complete',
                                            'session_id': save_result['session_id'],
                                            'audio_file': save_result.get('audio_file', ''),
                                            'call_duration': save_result.get('call_duration', 0)
                                        }))
                                    
                                    # 2. 生成评估报告
                                    logger.info("开始生成评估报告...")
                                    transcript = recorder.get_transcript_text()
                                    
                                    # 获取场景的维度配置
                                    dimension_config = scene.get('dimension_config')
                                    dimensions = []
                                    if dimension_config:
                                        try:
                                            config_data = json.loads(dimension_config)
                                            dimensions = config_data.get('dimensions', [])
                                        except:
                                            logger.warning("场景维度配置解析失败")
                                    
                                        report = scene_assessment_service.generate_report(
                                        session_id=recorder.session_id,
                                        transcript=transcript,
                                        dimensions=dimensions,
                                        industry=scene.get('industry', ''),
                                        role_type=scene.get('ai_role', ''),
                                        background_info=scene.get('background', '')
                                    )
                                    
                                    if report:
                                                                                # 3. 保存评估报告到数据库
                                        scene_assessment_service.save_to_database(
                                            session_id=recorder.session_id,
                                            report=report,
                                            scene_id=int(scene_id),
                                            user_id=recorder.user_id,
                                            word_content=transcript,
                                            oss_file_path=save_result.get('audio_file', ''),
                                            call_duration=save_result.get('call_duration', 0)
                                        )
                                        
                                        ws.send(json.dumps({
                                            'type': 'assessment_complete',
                                            'session_id': recorder.session_id,
                                            'report': report
                                        }))
                                        logger.info("评估报告生成并保存成功")
                                    else:
                                        ws.send(json.dumps({
                                            'type': 'assessment_error',
                                            'error': '评估报告生成失败'
                                        }))
                                    
                                except Exception as e:
                                    logger.error(f"会话结束处理失败：{str(e)}", exc_info=True)
                                    ws.send(json.dumps({
                                        'type': 'assessment_error',
                                        'error': str(e)
                                    }))
                                
                                # 通知前端可以关闭连接
                                ws.send(json.dumps({
                                    'type': 'ready_to_close'
                                }))
                                break
                            
                            elif msg_type == 'stop':
                                break
                                
                    except json.JSONDecodeError:
                        logger.warning("Invalid JSON message")
                    except Exception as e:
                        logger.error(f"Process message error: {e}")
                        
                except Exception as e:
                    logger.error(f"WebSocket receive error: {e}")
                    break
            
        except Exception as e:
            logger.error(f"Session error: {e}")
            ws.send(json.dumps({'type': 'error', 'message': str(e)}))
        finally:
            client.close()
            
            saved_path = recorder.save()
            if saved_path:
                logger.info(f"Conversation record saved: {saved_path}")
                
                # 生成评估报告
                try:
                    logger.info("正在生成评估报告...")
                    
                    # 获取场景信息
                    scene = db_module.get_scene_by_id(scene_id_int)
                    dimension_config = scene.get('dimension_config') if scene else None
                    
                    dimensions = []
                    if dimension_config:
                        try:
                            config_data = json.loads(dimension_config)
                            dimensions = config_data.get('dimensions', [])
                        except:
                            logger.warning("解析维度配置失败")
                    
                    # 获取对话转录
                    transcript = recorder.get_transcript_text()
                    
                    # 生成评估报告
                    report = scene_assessment_service.generate_report(
                        session_id=recorder.session_id,
                        transcript=transcript,
                        dimensions=dimensions,
                        industry=scene.get('industry', '') if scene else '',
                        role_type=scene.get('role_type', '') if scene else '',
                        background_info=scene.get('scene_prompt', '')[:1000] if scene else ''
                    )
                    
                    if report:
                        # 保存到数据库
                        scene_assessment_service.save_to_database(
                            session_id=recorder.session_id,
                            report=report,
                            scene_id=scene_id_int,
                            user_id=1,  # TODO: 从 session 获取真实用户 ID
                            word_content=json.dumps(recorder.get_messages(), ensure_ascii=False),
                            oss_file_path=saved_path,
                            call_duration=recorder.get_duration()
                        )
                        logger.info(f"评估报告已保存：session_id={recorder.session_id}")
                    else:
                        logger.error("评估报告生成失败")
                        
                except Exception as e:
                    logger.error(f"生成评估报告失败：{str(e)}", exc_info=True)
            
            logger.info(f"WebSocket closed for scene: {scene_id}")
