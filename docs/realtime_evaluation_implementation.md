# 实时对练评估功能实现文档

## 📋 实施时间
2025年1月 - 第一阶段功能实现

## 🎯 功能目标

解决实时对练结束后没有触发评估报告生成的问题，实现：
1. ✅ 用户点击"结束对练"按钮时触发后端接口
2. ✅ 保存对话记录和音频文件
3. ✅ 自动生成评估报告
4. ✅ 跳转到评估报告页面

## 🔧 技术方案

### 方案架构
```
用户点击"结束对练" 
    ↓
前端发送 session_end 消息 (WebSocket)
    ↓
后端接收并处理:
    1. 调用 recorder.save() 保存对话和音频
    2. 调用 scene_assessment_service.generate_report() 生成评估
    3. 调用 scene_assessment_service.save_to_database() 保存报告
    ↓
后端发送响应消息给前端
    ↓
前端跳转到评估报告页面
```

## 📝 代码修改详情

### 1. 前端修改 - `front_end/realtime/static/js/realtime.js`

#### 修改点1：handleWebSocketMessage 添加新消息类型处理

**位置**：在 `case 'error':` 之后添加

```javascript
case 'error':
    addMessage('错误: ' + data.message, 'ai');
    break;

// ✅ 新增：处理保存完成消息
case 'save_complete':
    console.log('对话记录已保存:', data.session_id);
    updateStatus('processing', '对话记录已保存，正在生成评估报告...');
    break;

// ✅ 新增：处理评估完成消息
case 'assessment_complete':
    console.log('评估报告生成成功，会话ID:', data.session_id);
    updateStatus('completed', '✅ 评估报告已生成');
    setTimeout(() => {
        window.location.href = `/evaluate?session_id=${data.session_id}`;
    }, 1500);
    break;

// ✅ 新增：处理评估错误消息
case 'assessment_error':
    console.error('评估报告生成失败:', data.error);
    updateStatus('error', '❌ 评估报告生成失败: ' + data.error);
    break;

// ✅ 新增：处理准备关闭消息
case 'ready_to_close':
    console.log('后端处理完成，准备关闭连接');
    if (ws) {
        ws.close();
    }
    break;
```

#### 修改点2：stopSession 函数 - 发送结束信号

**原代码**：
```javascript
if (ws) {
    ws.close();
}

if (animationId) {
    cancelAnimationFrame(animationId);
}

handleDisconnect();
```

**修改为**：
```javascript
// ✅ 发送结束信号给后端，触发保存和评估
if (ws && ws.readyState === WebSocket.OPEN) {
    console.log('发送会话结束信号...');
    updateStatus('processing', '正在保存对话记录和生成评估报告...');
    
    ws.send(JSON.stringify({
        type: 'session_end',
        timestamp: new Date().toISOString()
    }));
    
    // 不立即关闭WebSocket，等待后端处理完成后发送ready_to_close消息
    // 设置超时保护，5秒后强制关闭
    setTimeout(() => {
        if (ws && ws.readyState === WebSocket.OPEN) {
            console.log('超时，强制关闭WebSocket');
            ws.close();
        }
        if (animationId) {
            cancelAnimationFrame(animationId);
        }
        handleDisconnect();
    }, 5000);
} else {
    if (ws) {
        ws.close();
    }
    if (animationId) {
        cancelAnimationFrame(animationId);
    }
    handleDisconnect();
}
```

---

### 2. 后端修改 - `routes/realtime_routes.py`

#### 修改点：在 WebSocket 消息处理循环中添加 session_end 处理

**位置**：在 `elif msg_type == 'stop':` 之前添加

```python
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
```

---

## 🔄 消息流程图

```
前端 (realtime.js)                     后端 (realtime_routes.py)
      │                                        │
      │  1. 点击"结束对练"按钮                    │
      │─────────────────────────────────────>│
      │     type: 'session_end'               │
      │                                        │
      │                                    2. recorder.save()
      │                                        ├─ 保存音频文件
      │                                        ├─ 保存对话转录
      │                                        └─ 保存到数据库
      │                                        │
      │<─────────────────────────────────────│
      │     type: 'save_complete'             │
      │     显示: "对话记录已保存..."           │
      │                                        │
      │                                    3. generate_report()
      │                                        ├─ 调用 Qwen Plus 3.5
      │                                        └─ 生成评估报告
      │                                        │
      │                                    4. save_to_database()
      │                                        └─ 保存评估到数据库
      │                                        │
      │<─────────────────────────────────────│
      │     type: 'assessment_complete'       │
      │     session_id: xxx                   │
      │                                        │
      │  5. 1.5秒后跳转到评估页面               │
      │     /evaluate?session_id=xxx          │
      │                                        │
      │<─────────────────────────────────────│
      │     type: 'ready_to_close'            │
      │                                        │
      │  6. 关闭 WebSocket                     │
      │─────────────────────────────────────>│
```

---

## 📦 涉及的文件清单

### 已修改文件
1. ✅ `front_end/realtime/static/js/realtime.js` - 前端WebSocket消息处理
2. ✅ `routes/realtime_routes.py` - 后端WebSocket消息处理

### 依赖的现有文件（无需修改）
3. `agent/service/conversational/recorder.py` - 对话记录器
   - `save()` 方法：保存对话和音频
   - `get_transcript_text()` 方法：获取转录文本

4. `agent/service/scene/assessment_service.py` - 评估服务
   - `generate_report()` 方法：生成评估报告
   - `save_to_database()` 方法：保存报告到数据库

5. `database/record_dao.py` - 数据库操作
   - `save_coach_record()` 方法：保存对话记录

---

## 🧪 测试步骤

### 1. 启动服务
```bash
python app.py
```

### 2. 测试流程
1. 访问场景列表页面：`http://localhost:5000/scenes`
2. 点击任意场景的"开始对练"按钮
3. 进入实时对练页面，点击"开始"按钮
4. 进行语音对话（至少说几句话）
5. 点击"结束"按钮

### 3. 验证结果
#### 前端验证：
- ✅ 点击"结束"后，状态栏显示："正在保存对话记录和生成评估报告..."
- ✅ 约2-3秒后，状态栏显示："✅ 评估报告已生成"
- ✅ 1.5秒后自动跳转到评估报告页面
- ✅ 浏览器控制台打印相关日志

#### 后端验证：
```bash
# 查看后端日志，应该看到：
收到前端会话结束信号，开始保存和评估...
对话记录已保存: session_id=xxx, audio=audio_file/xxx.wav
开始生成评估报告...
正在调用 Qwen Plus 3.5 生成评估报告...
评估报告生成并保存成功
```

#### 数据库验证：
```sql
-- 1. 检查对话记录是否保存
SELECT * FROM ai_coach_record 
WHERE session_id = 'xxx' 
ORDER BY created_time DESC 
LIMIT 1;

-- 2. 检查评估报告是否保存
SELECT session_id, overall_score, overall_grade, created_time 
FROM ai_coach_record 
WHERE session_id = 'xxx';

-- 3. 检查音频文件路径
SELECT session_id, oss_file_path, call_duration 
FROM ai_coach_record 
WHERE session_id = 'xxx';
```

#### 文件系统验证：
```bash
# 检查音频文件是否生成
ls -lh audio_file/*.wav

# 查看最新的音频文件
ls -lt audio_file/*.wav | head -1
```

---

## ⚠️ 注意事项

### 1. 超时保护
- 前端设置了5秒超时，如果后端5秒内没有响应，会强制关闭WebSocket
- 如果评估报告生成时间较长，可能需要调整超时时间

### 2. 错误处理
- 后端捕获所有异常，通过 `assessment_error` 消息通知前端
- 前端显示错误提示，但不会自动跳转

### 3. 用户体验
- 保存和评估过程中显示加载状态
- 评估完成后延迟1.5秒跳转，让用户看到成功提示

### 4. 依赖检查
确保以下服务正常：
- ✅ Qwen Plus 3.5 API 密钥配置正确
- ✅ 数据库连接正常
- ✅ 音频文件目录有写入权限

---

## 🚀 下一步优化（可选）

### 第二阶段：SOP质检整合
根据文档中的方案，实现 SOP质检 + 能力维度 的综合评估：

```python
# agent/service/scene/assessment_service.py

def generate_full_report(
    self,
    session_id: str,
    transcript: str,
    scene_id: int,
    **kwargs
) -> Dict[str, Any]:
    """生成包含 SOP质检 + 能力维度 的完整评估报告"""
    
    # 1. 获取场景配置
    sop_checklist = self._get_scene_sop(scene_id)
    dimensions = self._get_scene_dimensions(scene_id)
    
    # 2. SOP 质检评估
    sop_result = self._evaluate_sop(transcript, sop_checklist)
    
    # 3. 能力维度评估
    dimension_result = self.generate_report(...)
    
    # 4. 计算综合评分
    sop_weight = 0.4
    dimension_weight = 0.6
    final_score = sop_score * sop_weight + dim_score * dimension_weight
    
    return {
        "final_score": final_score,
        "sop_evaluation": sop_result,
        "dimension_evaluation": dimension_result,
        "overall_feedback": ...
    }
```

### 第三阶段：语音流畅度分析
- 集成语音识别API获取时间戳
- 分析停顿、语速、填充词
- 评估语言流畅度和表达能力

---

## 📞 问题排查

### 问题1：点击"结束"后没有反应
**排查步骤**：
1. 打开浏览器控制台，查看是否有JavaScript错误
2. 检查WebSocket连接状态：`ws.readyState === WebSocket.OPEN`
3. 查看Network面板，确认WebSocket消息是否发送

### 问题2：评估报告生成失败
**排查步骤**：
1. 查看后端日志，确认是否有异常堆栈
2. 检查Qwen API配置和余额
3. 验证场景是否配置了维度

### 问题3：音频文件没有保存
**排查步骤**：
1. 检查 `audio_file/` 目录权限
2. 查看 `recorder.audio_chunks` 是否为空
3. 确认 `recorder.add_audio_chunk()` 被正确调用

### 问题4：数据库保存失败
**排查步骤**：
1. 检查数据库连接
2. 验证表结构是否正确
3. 查看数据库日志

---

## ✅ 实施检查清单

实施前：
- [ ] 备份当前代码
- [ ] 确认Qwen API可用
- [ ] 确认数据库连接正常
- [ ] 确认音频目录有写入权限

实施中：
- [x] 修改 `front_end/realtime/static/js/realtime.js`
- [x] 修改 `routes/realtime_routes.py`
- [ ] 清除浏览器缓存（Ctrl+Shift+R）

实施后：
- [ ] 完整测试一次对练流程
- [ ] 验证数据库记录
- [ ] 验证音频文件生成
- [ ] 验证评估报告跳转
- [ ] 检查后端日志无错误

---

## 📄 相关文档

- [ConversationRecorder 类文档](../../agent/service/conversational/recorder.py)
- [SceneAssessmentService 类文档](../../agent/service/scene/assessment_service.py)
- [评估服务改造方案](./20260309T182823_session.md#评估服务改造)

---

**文档生成时间**：2025-01-09
**实施状态**：✅ 代码已修改完成，等待测试验证
**预计测试时间**：30分钟

---

## 🔧 最新更新 (2025-01-09)

### ✅ 已完成
1. **后端文件重写**：`routes/realtime_routes.py` 已完全重写，修复了所有缩进问题
   - 正确的消息类型处理：`audio`, `text`, `session_end`, `stop`
   - 完整的错误处理和资源清理
   - 会话异常结束时的兜底保存逻辑

2. **前端消息处理**：`front_end/realtime/static/js/realtime.js`
   - 添加了 4 个新的消息类型处理
   - 修改了 `stopSession()` 函数发送结束信号

### 📋 关键改进

#### 1. WebSocket 消息流程清晰化
```python
# routes/realtime_routes.py - 主消息循环
while True:
    data = ws.receive(timeout=60)
    
    # 处理二进制音频
    if isinstance(data, bytes):
        client.send_audio(data)
    
    # 处理JSON消息
    else:
        message = json.loads(data)
        msg_type = message.get('type')
        
        if msg_type == 'audio': ...
        elif msg_type == 'text': ...
        elif msg_type == 'session_end':  # ✅ 新增
            # 保存、评估、通知前端
        elif msg_type == 'stop': ...
```

#### 2. 异常结束保护
```python
finally:
    # 如果用户直接关闭浏览器，仍然保存记录
    if not session_ended and recorder and recorder.messages:
        save_result = recorder.save()
        # 尝试生成评估报告
```

### ⚠️ 已知问题

#### 问题1：前端转录文字显示乱码
**现象**：中文显示为 `閿€鍞疄鎴樻紨缁?` 等乱码

**原因**：文件编码问题，部分中文被错误编码

**临时解决方案**：
- 后端text消息传输正常（UTF-8编码）
- 前端接收和显示逻辑正常
- 只是部分静态文本显示乱码（不影响对话转录）

**完整解决方案**：需要将 `front_end/realtime/static/js/realtime.js` 文件重新保存为 UTF-8 编码

```bash
# PowerShell 命令修复编码
$content = Get-Content "front_end/realtime/static/js/realtime.js" -Encoding UTF8
$content | Out-File "front_end/realtime/static/js/realtime.js" -Encoding UTF8
```

#### 问题2：评估功能验证清单

**需要验证的功能点**：
- [ ] 点击"结束"按钮后，后端收到 `session_end` 消息
- [ ] 后端日志显示："收到前端会话结束信号，开始保存和评估..."
- [ ] 对话记录保存到数据库（`ai_coach_record` 表）
- [ ] 音频文件保存到 `audio_file/` 目录
- [ ] 评估报告生成（调用 Qwen Plus 3.5）
- [ ] 评估报告保存到数据库
- [ ] 前端收到 `assessment_complete` 消息
- [ ] 前端自动跳转到评估页面

### 🧪 快速测试步骤

1. **启动服务**
```bash
python app.py
```

2. **测试对练流程**
   - 访问：`http://localhost:5000/scenes`
   - 选择任意场景，点击"开始对练"
   - 点击"开始"按钮，说几句话（至少3-5轮对话）
   - 点击"结束"按钮

3. **查看后端日志**（关键日志）
```
INFO: 收到前端会话结束信号，开始保存和评估...
INFO: 对话记录已保存: session_id=xxx, audio=audio_file/xxx.wav
INFO: 开始生成评估报告...
INFO: 正在调用 Qwen Plus 3.5 生成评估报告...
INFO: 评估报告生成并保存成功
```

4. **查看前端效果**
   - 状态栏显示："正在保存对话记录和生成评估报告..."
   - 约2-3秒后："✅ 评估报告已生成"
   - 自动跳转到评估页面：`/evaluate?session_id=xxx`

5. **数据库验证**
```sql
-- 查看最新的对话记录
SELECT session_id, scene_id, call_duration, oss_file_path, created_time 
FROM ai_coach_record 
ORDER BY created_time DESC 
LIMIT 1;

-- 查看评估报告
SELECT session_id, overall_score, overall_grade 
FROM ai_coach_record 
WHERE session_id = 'xxx';
```

### 📁 备份文件
- `routes/realtime_routes_backup.py` - 修改前的原始文件（已备份）

### 🚨 如果测试失败

**回滚方案**：
```bash
Move-Item -Path "routes/realtime_routes_backup.py" -Destination "routes/realtime_routes.py" -Force
```

### 📞 调试技巧

1. **前端调试**：打开浏览器控制台（F12），查看：
   - Console：查看 JavaScript 日志和错误
   - Network > WS：查看 WebSocket 消息

2. **后端调试**：查看终端日志输出，重点关注：
   - `收到前端会话结束信号`
   - `对话记录已保存`
   - `评估报告生成`

3. **常见错误排查**：
   - **WebSocket 连接失败**：检查端口和防火墙
   - **评估报告生成失败**：检查 Qwen API 配置和余额
   - **数据库保存失败**：检查数据库连接和表结构
   - **音频文件保存失败**：检查 `audio_file/` 目录权限

---

祝测试顺利！🎉

如有问题，请查看：
- 后端日志（终端输出）
- 前端控制台（浏览器F12）
- 数据库记录（SQL查询）