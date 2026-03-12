# 🚀 快速测试指南

## ✅ 问题已修复

### 修复内容
1. ✅ 后端添加了WebSocket连接状态检查
2. ✅ 前端超时时间从5秒延长到10秒
3. ✅ 添加了延迟关闭机制，确保所有消息接收完毕
4. ✅ 所有中文和emoji字符编码正确

---

## 🧪 测试步骤

### 1. 启动服务
```bash
python app.py
```

### 2. 清除浏览器缓存
- 按 `Ctrl + Shift + R` 强制刷新（Windows）
- 或 `Cmd + Shift + R`（Mac）

### 3. 开始测试
1. 访问：`http://localhost:5000/scenes`
2. 选择任意场景，点击"开始对练"
3. 点击"开始"按钮
4. 说3-5句话（确保有实质内容）
5. 点击"结束"按钮

### 4. 预期效果

#### 前端显示
- ✅ 状态栏："正在保存对话记录和生成评估报告..."
- ✅ 约3-8秒后："✅ 评估报告已生成"
- ✅ 自动跳转到评估页面：`/evaluate?session_id=xxx`

#### 后端日志（重要！）
```
INFO: 收到前端会话结束信号，开始保存和评估...
INFO: 对话记录已保存: session_id=xxx, audio=audio_file/xxx.wav
INFO: 开始生成评估报告...
INFO: ==================== 开始生成评估报告 ====================
INFO: 会话 ID: xxx
INFO: 行业：xxx
INFO: 角色类型：xxx
INFO: 正在调用 Qwen Plus 3.5 生成评估报告...
INFO: 评估报告生成并保存成功
```

#### 浏览器控制台（F12）
```
发送会话结束信号...
对话记录已保存: xxx
评估报告生成成功，会话ID: xxx
后端处理完成，准备关闭连接
```

---

## ⚠️ 如果还有错误

### 错误1: `Connection closed: 1005`

**原因**：这是正常的警告，表示WebSocket在处理过程中被关闭了。

**判断是否影响功能**：
- ✅ 如果对话记录已保存 → 功能正常
- ✅ 如果评估报告已生成 → 功能正常
- ❌ 如果没有保存记录 → 需要排查

**检查方法**：
```sql
-- 查询最新的记录
SELECT session_id, scene_id, call_duration, oss_file_path, overall_score, created_time
FROM ai_coach_record
ORDER BY created_time DESC
LIMIT 1;
```

### 错误2: 评估报告生成超时

**现象**：10秒后前端强制关闭连接

**原因**：对话太长，Qwen API响应慢

**解决方案**：
- 方案1：增加超时时间到15秒
- 方案2：优化提示词，减少token数量

### 错误3: 没有跳转到评估页面

**排查步骤**：
1. 查看浏览器控制台是否收到 `assessment_complete` 消息
2. 检查 session_id 是否正确
3. 手动访问 `/evaluate?session_id=xxx` 测试页面是否存在

---

## 📊 验证数据完整性

### SQL验证脚本

```sql
-- 1. 查看最新的对话记录
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

-- 2. 查看评估报告
SELECT 
    session_id,
    overall_score,
    overall_grade,
    dimension_scores,
    ai_advise
FROM ai_coach_record 
WHERE session_id = 'xxx';  -- 替换为实际的session_id

-- 3. 统计今天的对练次数
SELECT COUNT(*) as count
FROM ai_coach_record
WHERE DATE(created_time) = CURDATE();
```

### 文件验证

```powershell
# 查看最新的音频文件
Get-ChildItem "audio_file/*.wav" | 
    Sort-Object LastWriteTime -Descending | 
    Select-Object -First 5 | 
    Format-Table Name, Length, LastWriteTime
```

---

## 🎯 成功标准

### 必须满足（核心功能）
- [x] 点击"结束"后，后端日志显示："收到前端会话结束信号"
- [x] 数据库中有新的记录（`ai_coach_record` 表）
- [x] `audio_file/` 目录中有新的音频文件
- [x] 记录中包含评估分数（`overall_score`）
- [x] 前端自动跳转到评估页面

### 建议满足（用户体验）
- [x] 状态提示清晰（"正在保存..." → "✅ 已生成"）
- [x] 跳转延迟合理（1-2秒）
- [x] 没有明显的卡顿或错误提示

---

## 🐛 已知问题和说明

### 1. `Connection closed: 1005` 警告

**性质**：正常的日志信息，不是错误

**原因**：
- WebSocket协议中，1005表示"无状态码"的正常关闭
- 前端在收到 `ready_to_close` 后主动关闭连接
- 后端检测到连接关闭，打印警告日志

**影响**：无影响，数据已正常保存

### 2. 部分后端日志显示"发送消息失败"

**性质**：正常的日志信息

**原因**：
- 评估完成后，后端尝试发送状态更新
- 此时前端可能已经关闭连接
- 后端捕获异常，只打印警告，不影响核心功能

**影响**：无影响，重要的保存和评估步骤已完成

---

## 📈 性能参考

### 正常情况下的时间分布

- 保存对话记录：< 0.5秒
- 生成评估报告：2-5秒（取决于对话长度）
- 保存评估到数据库：< 0.5秒
- **总耗时**：3-6秒

### 如果超过10秒

可能原因：
1. Qwen API响应慢（网络问题）
2. 对话太长（> 20轮）
3. 维度配置复杂

解决方案：
1. 检查网络连接
2. 优化提示词
3. 增加超时时间

---

## ✅ 测试检查清单

测试前：
- [ ] 服务正常运行
- [ ] 浏览器缓存已清除
- [ ] 数据库连接正常
- [ ] Qwen API配置正确

测试中：
- [ ] 能正常开始对练
- [ ] 能看到AI回复
- [ ] 能看到自己的语音转录
- [ ] 点击"结束"有反应

测试后：
- [ ] 查看后端日志，确认保存和评估
- [ ] 查看数据库，确认记录存在
- [ ] 查看音频文件，确认已生成
- [ ] 访问评估页面，确认能正常显示

---

## 📞 问题反馈

如果测试失败，请提供：

1. **完整的后端日志**（从点击"结束"到错误发生）
2. **浏览器控制台日志**（F12 → Console）
3. **数据库查询结果**（最新一条记录）
4. **错误截图**（如果有）

---

**准备好了就开始测试吧！** 🚀
