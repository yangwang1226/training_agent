# Session End 问题修复方案

## 问题描述

从日志分析：
```
2026-03-12 18:13:18,092 - INFO - Qwen: Connection closed: code=None, msg=None
2026-03-12 18:13:18,092 - ERROR - Send status error: Connection closed: 1005
2026-03-12 18:13:20,405 - INFO - 127.0.0.1 - - [12/Mar/2026 18:13:20] "GET /evaluate/api/report/ac04120a-235d-4ee5-9398-e8523a0fb616 HTTP/1.1" 404 -
```

**问题特征：**
1. WebSocket 连接突然关闭（code=None）
2. 后端没有输出 "收到前端会话结束信号" 的日志
3. 评估报告没有生成（404 错误）
4. 数据库中没有保存记录

## 可能原因

### 1. 前端问题
- ✗ 前端发送 `session_end` 后立即关闭了 WebSocket 连接
- ✗ 前端没有等待后端处理完成就跳转页面
- ✗ 浏览器刷新或关闭标签页

### 2. 后端问题
- ✗ 后端在接收到消息前连接就断开了
- ✗ 消息处理逻辑中存在异常但没有捕获
- ✗ 超时设置不合理

### 3. 网络问题
- ✗ WebSocket 连接不稳定
- ✗ 消息在传输过程中丢失

## 修复方案

### 方案 1：前端修复（推荐）

**问题：** 前端可能在发送 `session_end` 后立即关闭连接或跳转页面

**修复步骤：**

1. 修改 `front_end/realtime/static/js/realtime.js` 中的 `stopSession` 函数：

```javascript
function stopSession() {
    isRecording = false;
    
    // 停止所有媒体流
    stopAllStreams();
    
    // 发送会话结束信号给后端
    if (ws && ws.readyState === WebSocket.OPEN) {
        console.log('发送会话结束信号...');
        updateStatus('processing', '正在保存对话记录和生成评估报告...');
        
        // 禁用结束按钮，防止重复点击
        stopBtn.disabled = true;
        
        ws.send(JSON.stringify({
            type: 'session_end',
            timestamp: new Date().toISOString()
        }));
        
        // ⚠️ 重要：不要立即关闭 WebSocket
        // 等待后端发送评估完成消息后再关闭
        console.log('等待评估完成...');
        
        // 设置超时保护（30秒后强制跳转）
        setTimeout(() => {
            console.warn('评估超时，强制跳转');
            if (ws) {
                ws.close();
            }
            updateStatus('error', '评估超时，请稍后查看报告');
        }, 30000);
        
    } else {
        console.error('WebSocket 未连接，无法发送结束信号');
        updateStatus('error', 'WebSocket 未连接');
    }
}
```

2. 确保在收到 `assessment_complete` 消息后才关闭连接：

```javascript
ws.onmessage = (event) => {
    const message = JSON.parse(event.data);
    
    if (message.type === 'assessment_complete') {
        console.log('评估完成，会话ID:', message.session_id);
        
        // 关闭 WebSocket
        if (ws) {
            ws.close();
        }
        
        // 跳转到评估页面
        const evaluateUrl = `/evaluate?session_id=${message.session_id}`;
        console.log('跳转到评估页面:', evaluateUrl);
        window.location.href = evaluateUrl;
        
    } else if (message.type === 'assessment_error') {
        console.error('评估失败:', message.error);
        updateStatus('error', '评估失败: ' + message.error);
        
        // 关闭连接
        if (ws) {
            ws.close();
        }
    }
    
    // ... 其他消息处理
};
```

### 方案 2：后端增强错误处理

在 `routes/realtime_routes.py` 中增强 session_end 处理：

```python
elif msg_type == 'session_end':
    # 处理会话结束信号
    logger.info("收到前端会话结束信号，开始保存和评估...")
    session_ended = True
    
    try:
        # 先发送确认消息
        ws.send(json.dumps({
            'type': 'session_end_ack',
            'message': '正在处理，请稍候...'
        }))
        
        # 1. 保存对话记录和音频
        logger.info("步骤1: 保存对话记录...")
        save_result = recorder.save()
        if save_result:
            logger.info(f"对话记录已保存: session_id={save_result['session_id']}")
            
            # 发送进度更新
            ws.send(json.dumps({
                'type': 'progress',
                'message': '对话记录已保存，正在生成评估...'
            }))
        
        # 2-6. 评估流程...
        
        # 7. 发送完成消息
        logger.info(f"评估完成，发送完成消息...")
        ws.send(json.dumps({
            'type': 'assessment_complete',
            'session_id': recorder.session_id,
            'score': report.get('final_score', 0)
        }))
        
        # 等待消息发送完成
        time.sleep(0.5)
        
        logger.info("会话结束处理完成")
        break
        
    except Exception as e:
        logger.error(f"会话结束处理失败：{str(e)}", exc_info=True)
        try:
            ws.send(json.dumps({
                'type': 'assessment_error',
                'error': str(e)
            }))
        except:
            pass
        break
```

### 方案 3：添加心跳机制

防止连接在评估过程中超时：

```python
# 在评估过程中发送心跳
def generate_report_with_heartbeat(ws, recorder, scene_id, dimensions):
    def heartbeat():
        while not stop_heartbeat.is_set():
            try:
                ws.send(json.dumps({'type': 'heartbeat'}))
                time.sleep(5)
            except:
                break
    
    stop_heartbeat = threading.Event()
    heartbeat_thread = threading.Thread(target=heartbeat)
    heartbeat_thread.start()
    
    try:
        # 生成评估报告
        report = scene_assessment_service.generate_report(...)
        return report
    finally:
        stop_heartbeat.set()
        heartbeat_thread.join()
```

## 调试步骤

### 1. 检查前端是否发送了消息

在浏览器控制台（F12）查看：
```javascript
// 应该看到这些日志
发送会话结束信号...
等待评估完成...
```

### 2. 检查后端是否收到消息

在后端日志中查看：
```
INFO: 收到前端会话结束信号，开始保存和评估...
INFO: 对话记录已保存: session_id=xxx
INFO: 开始生成评估报告...
```

### 3. 检查 WebSocket 连接状态

在前端添加调试日志：
```javascript
ws.onclose = (event) => {
    console.log('WebSocket 关闭:', event.code, event.reason);
    console.log('关闭时机:', new Date().toISOString());
};
```

### 4. 检查数据库

```sql
-- 查看最近的记录
SELECT session_id, ai_score, sop_score, final_score, created_time
FROM ai_coach_record
WHERE is_delete = 0
ORDER BY created_time DESC
LIMIT 5;
```

## 推荐方案

**优先级 1：前端修复**
- 确保发送 `session_end` 后等待 `assessment_complete` 消息
- 不要立即关闭 WebSocket 或跳转页面
- 添加超时保护机制

**优先级 2：后端增强**
- 添加 session_end 确认消息
- 增强错误日志
- 添加进度更新消息

**优先级 3：测试验证**
- 使用测试脚本验证 WebSocket 通信
- 检查完整的消息流
- 确保评估报告正确保存

## 快速测试

1. 启动 Flask 应用
2. 运行测试脚本：
   ```bash
   python tests/test_websocket_session_end.py
   ```
3. 观察后端日志和测试输出
4. 确认是否收到评估完成消息

## 预期结果

修复后应该看到：

**前端日志：**
```
发送会话结束信号...
等待评估完成...
评估完成，会话ID: xxx
跳转到评估页面: /evaluate?session_id=xxx
```

**后端日志：**
```
INFO: 收到前端会话结束信号，开始保存和评估...
INFO: 对话记录已保存: session_id=xxx
INFO: 开始生成评估报告...
INFO: 评估报告生成成功
INFO: 评估报告已保存到数据库
INFO: 发送评估完成消息
```

**数据库：**
- 新增一条 `ai_coach_record` 记录
- `final_score` 字段有值
- 所有评分字段都已填充
