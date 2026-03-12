# WebSocket 连接异常关闭问题诊断与修复

## 问题分析

从日志分析：
```
2026-03-12 18:13:18,092 - INFO - Qwen: Connection closed: code=None, msg=None
2026-03-12 18:13:18,092 - ERROR - Send status error: Connection closed: 1005
```

**关键发现：**
1. ❌ 没有 "收到前端会话结束信号" 日志 → backend 没有收到 session_end 消息
2. ❌ Connection closed: code=None → 连接异常关闭（不是正常的 close code）
3. ❌ code=1005 → 表示没有收到状态码（abnormal closure）
4. ❌ 404 错误 → 评估报告未生成

## 根本原因

### 可能性 1：Qwen 实时语音连接关闭导致主 WebSocket 关闭

**证据：** 日志显示 "Qwen: Connection closed" 在主 WebSocket 关闭之前

**原因：** 
- Qwen 的 WebSocket 连接关闭时，可能触发了错误处理逻辑
- 错误处理中可能包含了 break 或 return，导致主循环退出
- 主 WebSocket 随之关闭，没有机会处理 session_end 消息

**解决方案：** 分离 Qwen 连接的生命周期和主 WebSocket 的生命周期

### 可能性 2：前端在 Qwen 停止后立即发送 session_end 导致时序问题

**原因：**
- 用户点击 "结束" 按钮
- 前端停止录音，关闭 Qwen 连接
- Qwen 连接关闭触发后端的连接关闭处理
- 此时前端才发送 session_end 消息
- 但后端已经在处理 Qwen 连接关闭，可能错过了 session_end 消息

**解决方案：** 调整消息发送时序

### 可能性 3：异常处理不当

**原因：** 后端在处理 Qwen 连接关闭时抛出异常，导致主循环退出

## 修复方案

### 方案 A：增强后端错误处理（推荐）

修改 `routes/realtime_routes.py`：

```python
# 在 Qwen client 的回调函数中
def on_status(status):
    try:
        logger.info(f"Qwen: {status}")
        
        # ⚠️ 不要在这里break或return
        # Qwen连接关闭是正常的，不应该影响主WebSocket
        
        if 'error' in status.lower():
            try:
                ws.send(json.dumps({
                    'type': 'status',
                    'status': status
                }))
            except:
                logger.warning("无法发送状态消息（连接可能已关闭）")
                
    except Exception as e:
        logger.error(f"处理状态更新失败: {e}", exc_info=True)
        # 不要让异常传播出去

# 在主消息循环中
while True:
    try:
        data = ws.receive(timeout=60)
        
        if data is None:
            logger.info("未收到数据，继续等待...")
            continue  # 不要break，继续等待
        
        # ... 处理消息 ...
        
    except Exception as e:
        logger.error(f"消息处理异常: {e}", exc_info=True)
        # 只有在WebSocket真正关闭时才退出
        if not ws or ws.closed:
            break
        continue  # 其他异常继续处理
```

### 方案 B：改进前端发送时序

修改 `front_end/realtime/static/js/realtime.js`：

```javascript
function stopSession() {
    console.log('准备停止会话...');
    isRecording = false;
    
    // 1. 先发送 session_end 消息（趁连接还在）
    if (ws && ws.readyState === WebSocket.OPEN) {
        console.log('[步骤1] 发送会话结束信号...');
        
        ws.send(JSON.stringify({
            type: 'session_end',
            timestamp: new Date().toISOString()
        }));
        
        updateStatus('processing', '正在保存对话记录和生成评估报告...');
        stopBtn.disabled = true;
        
        // 等待一小段时间确保消息发送
        setTimeout(() => {
            console.log('[步骤2] 停止录音和媒体流...');
            stopAllStreams();
        }, 100);
        
    } else {
        console.error('WebSocket 未连接');
        stopAllStreams();
    }
}
```

### 方案 C：添加连接状态检查

在后端添加连接健康检查：

```python
# 在处理每个消息之前
def is_websocket_alive(ws):
    try:
        # 发送一个ping看看连接是否还活着
        ws.send(json.dumps({'type': 'ping'}))
        return True
    except:
        return False

# 在主循环中
while True:
    try:
        data = ws.receive(timeout=60)
        
        # 检查连接状态
        if data is None:
            if not is_websocket_alive(ws):
                logger.warning("WebSocket 连接已断开")
                break
            continue
        
        # ... 处理消息 ...
```

### 方案 D：分离 Qwen 连接管理

```python
# 将 Qwen client 的错误处理独立出来
try:
    # Qwen 连接相关操作
    client.send_audio(data)
except Exception as qwen_error:
    logger.error(f"Qwen 连接错误: {qwen_error}")
    # 发送错误消息给前端，但不要终止主循环
    try:
        ws.send(json.dumps({
            'type': 'ai_error',
            'error': str(qwen_error)
        }))
    except:
        pass
    # 继续处理其他消息，不要 break
```

## 立即修复步骤

### 第一步：添加详细日志

在 `routes/realtime_routes.py` 中添加更多调试日志：

```python
# 在主循环开始前
logger.info("WebSocket 主循环开始")

# 在循环中
while True:
    logger.debug(f"等待消息... (ws.closed={ws.closed if ws else 'N/A'})")
    
    try:
        data = ws.receive(timeout=60)
        logger.debug(f"收到数据: type={type(data)}, len={len(data) if data else 0}")
        
        if data is None:
            logger.warning("收到 None 数据")
            continue
        
        if isinstance(data, bytes):
            logger.debug(f"收到二进制数据: {len(data)} bytes")
            # ...
        else:
            try:
                message = json.loads(data)
                msg_type = message.get('type', 'unknown')
                logger.info(f"收到消息类型: {msg_type}")
                
                # ...
                
            except json.JSONDecodeError as e:
                logger.error(f"JSON 解析失败: {e}, data={data[:100]}")
                continue
                
    except Exception as e:
        logger.error(f"循环异常: {e}", exc_info=True)
        if ws and not ws.closed:
            continue
        else:
            logger.error("WebSocket 已关闭，退出循环")
            break

logger.info("WebSocket 主循环结束")
```

### 第二步：确保 session_end 一定被处理

```python
elif msg_type == 'session_end':
    logger.info("=" * 60)
    logger.info("收到前端会话结束信号")
    logger.info("=" * 60)
    session_ended = True
    
    # 立即确认收到
    try:
        ws.send(json.dumps({
            'type': 'session_end_received',
            'message': '服务器已收到结束信号，正在处理...'
        }))
    except Exception as ack_error:
        logger.warning(f"发送确认失败: {ack_error}")
    
    try:
        # ... 评估逻辑 ...
        
    except Exception as eval_error:
        logger.error(f"评估处理失败: {eval_error}", exc_info=True)
        try:
            ws.send(json.dumps({
                'type': 'assessment_error',
                'error': str(eval_error)
            }))
        except:
            pass
    finally:
        # 无论如何都要退出循环
        logger.info("session_end 处理完成，退出循环")
        break
```

### 第三步：前端添加调试

```javascript
// 在 stopSession 函数中
function stopSession() {
    console.log('='.repeat(60));
    console.log('用户点击结束按钮');
    console.log('WebSocket readyState:', ws ? ws.readyState : 'null');
    console.log('='.repeat(60));
    
    isRecording = false;
    
    if (ws && ws.readyState === WebSocket.OPEN) {
        const message = {
            type: 'session_end',
            timestamp: new Date().toISOString()
        };
        
        console.log('发送消息:', JSON.stringify(message));
        
        try {
            ws.send(JSON.stringify(message));
            console.log('✓ 消息已发送');
        } catch (e) {
            console.error('✗ 发送失败:', e);
        }
        
        updateStatus('processing', '正在保存对话记录和生成评估报告...');
        stopBtn.disabled = true;
        
    } else {
        console.error('✗ WebSocket 未连接或已关闭');
        console.log('  - ws exists:', !!ws);
        console.log('  - readyState:', ws ? ws.readyState : 'N/A');
    }
    
    // 延迟停止媒体流
    setTimeout(() => {
        console.log('停止所有媒体流');
        stopAllStreams();
    }, 500);
}

// 添加消息接收日志
ws.onmessage = (event) => {
    console.log('收到服务器消息:', event.data);
    
    try {
        const data = JSON.parse(event.data);
        console.log('消息类型:', data.type);
        
        // ... 处理消息 ...
    } catch (e) {
        console.error('解析消息失败:', e);
    }
};
```

## 测试步骤

1. 启动应用，启用详细日志
2. 进入实时对练页面
3. 说几句话
4. 点击 "结束" 按钮
5. **同时观察：**
   - 浏览器控制台输出
   - 后端终端日志
   - 网络标签中的 WebSocket 消息

## 预期日志输出

**浏览器控制台：**
```
==================================================
用户点击结束按钮
WebSocket readyState: 1
==================================================
发送消息: {"type":"session_end","timestamp":"..."}
✓ 消息已发送
停止所有媒体流
收到服务器消息: {"type":"session_end_received",...}
消息类型: session_end_received
收到服务器消息: {"type":"assessment_complete",...}
消息类型: assessment_complete
```

**后端日志：**
```
INFO: 收到消息类型: session_end
INFO: ============================================================
INFO: 收到前端会话结束信号
INFO: ============================================================
INFO: 对话记录已保存: session_id=xxx
INFO: 开始生成评估报告...
INFO: 评估报告生成成功
INFO: 评估报告已保存到数据库
INFO: session_end 处理完成，退出循环
```

## 紧急临时方案

如果上述修复太复杂，可以使用临时方案：

**在会话异常结束时强制保存：**

```python
finally:
    # 无论如何都要尝试保存
    if not session_ended and recorder and len(recorder.messages) > 0:
        logger.warning("会话未正常结束，强制保存...")
        try:
            save_result = recorder.save()
            if save_result:
                logger.info(f"强制保存成功: {save_result['session_id']}")
                
                # 尝试生成评估
                # ... (简化的评估逻辑)
                
        except Exception as e:
            logger.error(f"强制保存失败: {e}", exc_info=True)
```

这样即使 session_end 消息丢失，至少对话记录能被保存。
