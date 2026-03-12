"""
测试 WebSocket session_end 消息处理
验证后端是否正确接收和处理会话结束信号
"""
import json
import time
import websocket
import threading

def test_session_end():
    """测试发送 session_end 消息"""
    print("\n=== 测试 WebSocket session_end 处理 ===\n")
    
    # WebSocket URL（根据实际情况修改）
    ws_url = "ws://localhost:5000/api/realtime/ws/15?provider=qwen"
    
    messages_received = []
    
    def on_message(ws, message):
        print(f"收到消息: {message}")
        try:
            data = json.loads(message)
            messages_received.append(data)
            
            # 如果收到评估完成消息，打印详情
            if data.get('type') == 'assessment_complete':
                print(f"\n[成功] 收到评估完成消息:")
                print(f"  Session ID: {data.get('session_id')}")
                print(f"  评估分数: {data.get('score')}")
        except:
            pass
    
    def on_error(ws, error):
        print(f"错误: {error}")
    
    def on_close(ws, close_status_code, close_msg):
        print(f"\n连接关闭: code={close_status_code}, msg={close_msg}")
    
    def on_open(ws):
        print("WebSocket 连接已建立\n")
        
        # 等待一秒
        time.sleep(1)
        
        # 发送一些测试音频数据（模拟对话）
        print("发送测试文本消息...")
        ws.send(json.dumps({
            'type': 'text',
            'text': '你好，我想咨询一下产品。'
        }))
        
        # 等待响应
        time.sleep(2)
        
        # 发送 session_end 消息
        print("\n发送 session_end 消息...")
        ws.send(json.dumps({
            'type': 'session_end',
            'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S')
        }))
        
        # 等待评估完成
        print("等待评估完成...")
        time.sleep(10)
        
        # 检查是否收到评估完成消息
        assessment_received = any(
            msg.get('type') == 'assessment_complete' 
            for msg in messages_received
        )
        
        if assessment_received:
            print("\n[✓] 测试通过：成功收到评估完成消息")
        else:
            print("\n[✗] 测试失败：未收到评估完成消息")
            print(f"收到的消息: {messages_received}")
    
    # 创建 WebSocket 连接
    ws = websocket.WebSocketApp(
        ws_url,
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )
    
    # 启动连接
    ws.run_forever()

if __name__ == "__main__":
    print("\n" + "="*60)
    print("WebSocket session_end 消息处理测试")
    print("="*60)
    print("\n注意：")
    print("1. 确保 Flask 应用正在运行（python app.py）")
    print("2. 确保有可用的场景（scene_id=15）")
    print("3. 观察后端日志输出\n")
    
    input("按 Enter 开始测试...")
    
    try:
        test_session_end()
    except KeyboardInterrupt:
        print("\n\n测试已取消")
    except Exception as e:
        print(f"\n\n测试失败: {e}")
