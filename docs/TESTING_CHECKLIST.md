# 🧪 实时对练评估功能测试清单

## 📋 测试前准备

### 1. 环境检查
- [ ] Python 服务正常运行 (`python app.py`)
- [ ] 数据库连接正常
- [ ] Qwen Plus 3.5 API 配置正确（`.env` 文件中的 `DASHSCOPE_API_KEY`）
- [ ] 音频文件目录存在且有写入权限 (`audio_file/`)

### 2. 浏览器设置
- [ ] 允许麦克风权限
- [ ] 清除浏览器缓存（Ctrl+Shift+R 或 Cmd+Shift+R）
- [ ] 打开开发者工具（F12）准备查看日志

---

## ✅ 核心功能测试

### 测试1：基本对练流程

**步骤**：
1. [ ] 访问场景列表：`http://localhost:5000/scenes`
2. [ ] 选择任意场景，点击"开始对练"
3. [ ] 进入对练页面，点击"开始"按钮
4. [ ] 允许麦克风权限
5. [ ] 与AI进行对话（至少3-5轮，确保有实质内容）

**预期结果**：
- [ ] 状态栏显示"已连接 - 正在录音"
- [ ] 能看到音频可视化波形
- [ ] AI的回复显示在聊天区域
- [ ] 用户的语音被转录并显示
- [ ] 消息计数正常增加

**如果失败**：
- 检查麦克风权限
- 查看浏览器控制台是否有WebSocket连接错误
- 查看后端日志是否有异常

---

### 测试2：会话结束和保存 ⭐

**步骤**：
1. [ ] 完成至少3-5轮对话后，点击"结束"按钮

**预期前端效果**：
- [ ] 状态栏显示："正在保存对话记录和生成评估报告..."
- [ ] 约2-5秒后显示："✅ 评估报告已生成"
- [ ] 自动跳转到评估页面

**预期后端日志**：
```
收到前端会话结束信号，开始保存和评估...
对话记录已保存: session_id=xxx, audio=audio_file/xxx.wav
开始生成评估报告...
正在调用 Qwen Plus 3.5 生成评估报告...
评估报告生成并保存成功
```

**浏览器控制台日志**：
```
发送会话结束信号...
对话记录已保存: xxx
评估报告生成成功，会话ID: xxx
后端处理完成，准备关闭连接
```

**如果失败**：
- [ ] 检查后端是否收到 `session_end` 消息
- [ ] 查看是否有异常日志
- [ ] 确认 recorder 是否正常工作

---

### 测试3：数据库记录验证 ⭐

**SQL查询1：检查对话记录**
```sql
SELECT 
    session_id,
    scene_id,
    call_duration,
    oss_file_path,
    word_content,
    created_time
FROM ai_coach_record 
ORDER BY created_time DESC 
LIMIT 1;
```

**检查项**：
- [ ] `session_id` 不为空
- [ ] `scene_id` 正确
- [ ] `call_duration` > 0
- [ ] `oss_file_path` 指向音频文件（如：`audio_file/20250109_123456_xxx.wav`）
- [ ] `word_content` 包含对话转录
- [ ] `created_time` 是最新时间

**SQL查询2：检查评估报告**
```sql
SELECT 
    session_id,
    overall_score,
    overall_grade,
    dimension_scores,
    ai_advise
FROM ai_coach_record 
WHERE session_id = 'xxx'  -- 替换为实际的session_id
```

**检查项**：
- [ ] `overall_score` 在 0-100 之间
- [ ] `overall_grade` 有值（如：'优秀'、'良好'等）
- [ ] `dimension_scores` 是JSON格式的能力维度评分
- [ ] `ai_advise` 包含评估建议

**如果失败**：
- 检查 `scene_assessment_service.save_to_database()` 是否被调用
- 查看数据库连接是否正常
- 检查表结构是否正确

---

### 测试4：音频文件验证

**步骤**：
1. [ ] 打开 `audio_file/` 目录
2. [ ] 找到最新的 `.wav` 文件

**检查项**：
- [ ] 文件名格式：`20250109_123456_xxx.wav`
- [ ] 文件大小 > 0
- [ ] 能播放，有声音

**PowerShell命令**：
```powershell
# 查看最新的音频文件
Get-ChildItem "audio_file/*.wav" | Sort-Object LastWriteTime -Descending | Select-Object -First 1 | Format-List Name, Length, LastWriteTime
```

**如果失败**：
- 检查 `audio_file/` 目录是否存在
- 检查目录权限
- 查看 `recorder.save()` 方法是否正常执行

---

### 测试5：评估报告页面

**步骤**：
1. [ ] 等待自动跳转，或手动访问：`/evaluate?session_id=xxx`

**检查项**：
- [ ] 页面正常加载
- [ ] 显示评估分数
- [ ] 显示评估等级
- [ ] 显示能力维度评分
- [ ] 显示AI建议
- [ ] 能查看对话转录

**如果失败**：
- 检查评估报告是否保存到数据库
- 查看前端 `/evaluate` 路由是否正常
- 检查数据格式是否正确

---

## 🔍 高级测试

### 测试6：异常中断处理

**步骤**：
1. [ ] 开始对练
2. [ ] 说几句话
3. [ ] 直接关闭浏览器标签页（不点击"结束"按钮）

**预期结果**：
- [ ] 后端检测到WebSocket断开
- [ ] 自动保存对话记录
- [ ] 尝试生成评估报告（兜底逻辑）

**后端日志**：
```
WebSocket connection closed by client
会话异常结束，尝试保存记录...
对话记录已保存: {...}
```

---

### 测试7：无对话内容

**步骤**：
1. [ ] 开始对练
2. [ ] 不说话，直接点击"结束"

**预期结果**：
- [ ] 不保存记录（recorder.messages 为空）
- [ ] 日志显示："No messages to save"
- [ ] WebSocket正常关闭

---

### 测试8：长时间对话

**步骤**：
1. [ ] 开始对练
2. [ ] 进行较长时间的对话（10轮以上）
3. [ ] 点击"结束"

**检查项**：
- [ ] 所有对话都被记录
- [ ] 音频文件完整
- [ ] 评估报告生成正常
- [ ] 时长计算正确

---

## 📊 性能测试

### 测试9：评估报告生成时间

**记录时间点**：
1. [ ] 点击"结束"按钮的时间
2. [ ] 后端日志显示"开始生成评估报告"的时间
3. [ ] 前端跳转的时间

**预期**：
- 总时间：2-5秒（取决于对话长度）
- Qwen API调用：1-3秒
- 数据库保存：< 1秒

**如果超时**：
- 检查网络连接
- 检查Qwen API响应时间
- 优化提示词长度

---

## 🐛 已知问题和解决方案

### 问题1：中文显示乱码

**现象**：前端静态文本显示为 `閿€鍞疄鎴樻紨缁?`

**原因**：文件编码问题

**解决方案**：
```powershell
$content = Get-Content "front_end/realtime/static/js/realtime.js" -Encoding UTF8
$content | Out-File "front_end/realtime/static/js/realtime.js" -Encoding UTF8
```

**注意**：对话转录的中文显示是正常的，只是部分静态文本乱码。

---

### 问题2：评估报告生成失败

**可能原因**：
1. Qwen API配置错误
2. API余额不足
3. 维度配置为空
4. 网络问题

**检查步骤**：
```bash
# 1. 检查环境变量
echo $env:DASHSCOPE_API_KEY

# 2. 测试API连接
# （运行单独的API测试脚本）

# 3. 查看详细错误日志
```

---

### 问题3：音频文件为空

**可能原因**：
1. 麦克风权限未授予
2. `recorder.audio_chunks` 为空
3. 音频编码问题

**解决方案**：
- 检查浏览器麦克风权限
- 查看 `recorder.add_audio_chunk()` 是否被调用
- 检查音频格式转换逻辑

---

## ✅ 测试通过标准

所有核心功能测试（测试1-5）都通过，即可认为实施成功：

- [x] 点击"结束"触发后端接口
- [x] 对话记录和音频保存成功
- [x] 评估报告自动生成
- [x] 数据正确保存到数据库
- [x] 前端自动跳转到评估页面

---

## 📞 联系和反馈

如果测试中遇到问题：

1. **查看文档**：`docs/realtime_evaluation_implementation.md`
2. **查看后端日志**：终端输出
3. **查看前端日志**：浏览器控制台（F12）
4. **查看数据库**：运行SQL查询

**回滚方案**（如果测试完全失败）：
```bash
Move-Item -Path "routes/realtime_routes_backup.py" -Destination "routes/realtime_routes.py" -Force
```

---

**测试日期**：_____________
**测试人员**：_____________
**测试结果**：□ 通过  □ 部分通过  □ 失败
**备注**：
